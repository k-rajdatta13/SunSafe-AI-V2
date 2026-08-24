from agents.orchestrator import orchestrator_node, next_agent
from agents.verifier_agent import verifier_agent_node


def test_orchestrator_routes_decision_support_request():
    state = {"city":"Kanpur","skin_type":3,"body_area":25,"age":25,
             "user_query":"Can I go outside safely today?"}
    result = orchestrator_node(state)
    assert result["intent"] == "decision_support"
    assert result["plan"] == ["weather_agent","safety_agent","knowledge_agent","decision_agent","verifier_agent","explainer_agent"]
    assert next_agent(result) == "weather_agent"


def test_orchestrator_routes_knowledge_request_without_weather():
    state = {"city":"Kanpur","skin_type":3,"body_area":25,"age":25,
             "user_query":"What does UV index 8 mean?"}
    result = orchestrator_node(state)
    assert result["intent"] == "knowledge"
    assert result["plan"] == ["knowledge_agent", "explainer_agent"]
    assert next_agent(result) == "knowledge_agent"


def test_verifier_catches_inconsistent_high_uv_state():
    state = {"uv_index":9,"temperature":25,"protection_required":True,"hard_stop":False,
             "best_time":"10:00 AM","verification_attempts":0,"completed_agents":[],"trace":[]}
    result = verifier_agent_node(state)
    assert result["verification_status"] == "FAIL"
    assert result["verification_issues"]
