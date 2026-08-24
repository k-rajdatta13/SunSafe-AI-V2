"""Phase 5.2/5.3 live integration evaluation."""
from __future__ import annotations
import importlib, json, sys, time
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
from evaluation.agent_eval import evaluate_trace
from utils.cache import geocode_cache, weather_cache, forecast_cache

class FakeResponse:
    def __init__(self,status_code:int,payload:dict[str,Any]): self.status_code=status_code; self._payload=payload
    def json(self): return self._payload
class FakeExplanation:
    def __init__(self,content:str): self.content=content
class FakeChain:
    def invoke(self, values):
        if values.get("evidence_status") == "UNAVAILABLE":
            return FakeExplanation(
                "Authoritative evidence was unavailable for this response. "
                f"Deterministic environmental action: {values.get('overall_action')}. "
                "No authoritative evidence-based claim is being added."
            )
        return FakeExplanation(
            "Verified environmental decision. "
            f"Action: {values.get('overall_action')}. Suggested window: {values.get('best_time')}. "
            f"Evidence: {values.get('evidence_summary','')}. Sources: {values.get('evidence_sources','')}."
        )

def _weather_payload(uv=4.0, temperature=28.0):
    return {
        "current": {
            "temp_c": temperature,
            "humidity": 55,
            "cloud": 20,
            "wind_kph": 10,
            "condition": {
                "code": 1000
            },
            "uv": uv,
        }
    }
def _forecast_payload():
    times = [
        "2026-08-23 08:00",
        "2026-08-23 09:00",
        "2026-08-23 10:00",
        "2026-08-23 11:00",
        "2026-08-23 12:00",
    ]

    hours = []

    temperatures = [24, 25, 27, 29, 31]
    uv_values = [2, 3, 4, 6, 8]
    clouds = [10, 10, 15, 20, 25]

    for time_value, temperature, uv, cloud in zip(
        times,
        temperatures,
        uv_values,
        clouds,
    ):
        hours.append(
            {
                "time": time_value,
                "temp_c": temperature,
                "uv": uv,
                "cloud": cloud,
            }
        )

    return {
        "forecast": {
            "forecastday": [
                {
                    "hour": hours
                }
            ]
        }
    }

def _configure_common_patches():
    import os
    import agents.explainer_agent as explainer_agent

    explainer_agent.chain = FakeChain()

    import tools.weather_api as weather_api

    os.environ["WEATHERAPI_KEY"] = "test-key"

    calls = {"geocode": 0, "current": 0, "forecast": 0}
    failure = {"type": None, "remaining": 0}

    def fake_get(url, params=None, timeout=None):
        params = params or {}

        if "search.json" in url:
            calls["geocode"] += 1
            return FakeResponse(
                200,
                [
                    {
                        "name": "Kanpur",
                        "country": "India",
                        "lat": 26.4499,
                        "lon": 80.3319,
                    }
                ],
            )

        if "current.json" in url:
            calls["current"] += 1

            if failure["type"] == "timeout" and failure["remaining"] > 0:
                failure["remaining"] -= 1
                import requests
                raise requests.Timeout("injected timeout")

            if failure["type"] == "429" and failure["remaining"] > 0:
                failure["remaining"] -= 1
                return FakeResponse(429, {})

            return FakeResponse(200, _weather_payload())

        if "forecast.json" in url:
            calls["forecast"] += 1
            return FakeResponse(200, _forecast_payload())

        raise AssertionError(f"Unexpected URL: {url}")

    weather_api.requests.get = fake_get

    geocode_cache.clear()
    weather_cache.clear()
    forecast_cache.clear()

    return calls, failure
def _reload_graph():
    import agents.weather_agent as wa
    import agents.knowledge_agent as ka
    import agents.verifier_agent as va
    import graph
    return importlib.reload(graph),wa,ka,va
def _client():
    import api.main as main
    return TestClient(main.app)
def _request(client,query):
    start=time.perf_counter()
    r=client.post("/v1/recommend",json={"city":"Kanpur","skin_type":3,"body_area":1,"age":25,"user_query":query})
    return r,r.json(),(time.perf_counter()-start)*1000

def run_normal():
    calls,_=_configure_common_patches(); _reload_graph()
    r,b,lat=_request(_client(),"Can I plan an outdoor activity safely today?")
    trace=[x.get("agent") for x in b.get("trace",[])]
    expected=["orchestrator","weather_agent","safety_agent","knowledge_agent","decision_agent","verifier_agent","explainer_agent"]
    c=evaluate_trace(b.get("trace",[]),b)
    return {"case":"normal_full_graph","passed":r.status_code==200 and b.get("status")=="success" and trace==expected and b.get("evidence_status")=="AVAILABLE" and len(b.get("evidence",[]))>0 and b.get("verification_status")=="PASS" and c["required_agents_present"] and c["required_agent_order"],"status_code":r.status_code,"status":b.get("status"),"trace_agents":trace,"evidence_count":len(b.get("evidence",[])),"evidence_status":b.get("evidence_status"),"verification_status":b.get("verification_status"),"latency_ms":round(lat,2),"weather_http_calls":calls}

def run_retry_case(mode):
    calls,f=_configure_common_patches(); f["type"]=mode; f["remaining"]=2; _reload_graph()
    r,b,lat=_request(_client(),"Can I plan an outdoor activity safely today?")
    return {"case":f"weather_{mode}_retry","passed":r.status_code==200 and b.get("status")=="success" and b.get("verification_status")=="PASS" and calls["current"]==3,"status_code":r.status_code,"status":b.get("status"),"weather_calls":calls,"verification_status":b.get("verification_status"),"latency_ms":round(lat,2)}

def run_missing_evidence_case():
    _configure_common_patches(); _,_,ka,_=_reload_graph()
    ka.retriever.retrieve_for_state=lambda state:[]
    import graph; importlib.reload(graph)
    r,b,lat=_request(_client(),"Can I plan an outdoor activity safely today?")
    explanation=(b.get("explanation") or "").lower()
    degraded=(r.status_code==200 and b.get("status")=="degraded" and b.get("evidence_status")=="UNAVAILABLE" and len(b.get("evidence",[]))==0 and "authoritative evidence" in explanation)
    return {"case":"missing_evidence_degraded_mode","passed":degraded,"status_code":r.status_code,"status":b.get("status"),"evidence_count":len(b.get("evidence",[])),"evidence_status":b.get("evidence_status"),"explanation_contains_authority_notice":"authoritative evidence" in explanation,"latency_ms":round(lat,2)}

def run_verifier_failure_case():
    _configure_common_patches()
    import agents.verifier_agent as va
    original=va.verifier_agent_node
    def forced(state):
        from agents.common import mark_complete
        state["verification_issues"]=["Injected verifier failure"]; state["verification_status"]="FAIL"; state["verification_attempts"]=state.get("verification_attempts",0)+1; state["hard_stop"]=False; state["best_time"]="No conservative outdoor window found"
        return mark_complete(state,"verifier_agent","injected_verification_failure")
    va.verifier_agent_node=forced
    try:
        import graph; importlib.reload(graph)
        r,b,lat=_request(_client(),"Can I plan an outdoor activity safely today?")
    finally:
        va.verifier_agent_node=original
        import graph; importlib.reload(graph)
    trace=[x.get("agent") for x in b.get("trace",[])]
    return {"case":"verifier_failure_revision_loop","passed":r.status_code==200 and trace.count("verifier_agent")==2 and b.get("verification_status")=="FAIL" and b.get("best_time")=="No conservative outdoor window found","status_code":r.status_code,"verifier_executions":trace.count("verifier_agent"),"verification_status":b.get("verification_status"),"best_time":b.get("best_time"),"trace_agents":trace,"latency_ms":round(lat,2)}

def run_all():
    cases=[run_normal(),run_retry_case("timeout"),run_retry_case("429"),run_missing_evidence_case(),run_verifier_failure_case()]
    return {"phase":"5.3","mode":"LIVE_GRAPH_INTEGRATION_WITH_EVIDENCE_DEGRADED_MODE","cases":cases,"passed_cases":sum(bool(c["passed"]) for c in cases),"total_cases":len(cases),"all_harness_cases_passed":all(c["passed"] for c in cases)}
if __name__=="__main__":
    result=run_all(); out=ROOT/"evaluation"/"results"/"phase5_3_live_results.json"; out.write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
