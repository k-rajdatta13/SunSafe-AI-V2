"""LLM response agent.

The model explains verified environmental decisions; it does not choose the
safety action and cannot manufacture authoritative evidence.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from state import SunState
from agents.common import mark_complete

load_dotenv()


prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the explanation agent for SunSafe AI.
Explain only the verified environmental decision supplied to you.

Hard rules:
- Do not invent exposure durations, diagnoses, treatment, vitamin-D prescriptions,
  safety thresholds, sources, URLs, or evidence.
- Do not override hard_stop or overall_action.
- Deterministic safety policy has authority over the action.
- If verification failed, state that the system could not safely produce a recommendation.
- If evidence status is UNAVAILABLE, explicitly say authoritative evidence was
  unavailable for this response. You may still explain deterministic environmental
  observations supplied in the state, but do not present unsupported public-health
  claims as authoritative or cite nonexistent sources.
- Never claim that an answer is evidence-grounded when evidence is unavailable."""),
    ("human", """
User question: {user_query}
Location: {city}, {country}
Temperature: {temperature}
UV Index: {uv_index}
UV level: {uv_level}
Protection required: {protection_required}
Heat screening: {heat_caution}
Overall action: {overall_action}
Suggested outdoor window: {best_time}
Hard stop: {hard_stop}
Verification: {verification_status}
Intent: {intent}
Verification issues: {verification_issues}
Safety reasons: {safety_reasons}
Protective actions: {protective_actions}
Evidence status: {evidence_status}
Evidence sources: {evidence_sources}
Evidence summaries: {evidence_summary}
Retrieval backend: {retrieval_backend}

CITATION RULE: When mentioning a factual claim from available evidence, cite the
source name and URL supplied above. Never invent a source or URL.
"""),
])


# Deliberately lazy: constructing ChatGoogleGenerativeAI at module import time
# forces Google credential discovery even when the integration harness replaces
# the chain with FakeChain. Keeping the chain as a module-level variable also
# allows the integration harness to inject its deterministic fake chain.
chain = None


def _get_chain():
    global chain

    if chain is None:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        chain = prompt | llm

    return chain


def explainer_agent_node(state: SunState) -> SunState:
    response = _get_chain().invoke({
        "user_query": state.get("user_query", ""),
        "city": state.get("city", "Unknown"),
        "country": state.get("country", "Unknown"),
        "temperature": (
            f"{state.get('temperature')} °C"
            if state.get("temperature") is not None
            else "Not requested"
        ),
        "uv_index": state.get("uv_index", "Not requested"),
        "uv_level": state.get("uv_level", "Not assessed"),
        "protection_required": state.get("protection_required", "Not assessed"),
        "heat_caution": state.get("heat_caution", "Not assessed"),
        "overall_action": state.get("overall_action", "Knowledge-only response"),
        "best_time": state.get("best_time", "Not requested"),
        "hard_stop": state.get("hard_stop", False),
        "verification_status": state.get("verification_status", "NOT_REQUIRED"),
        "intent": state.get("intent", "unknown"),
        "verification_issues": (
            " | ".join(state.get("verification_issues", []))
            or "None"
        ),
        "safety_reasons": " | ".join(state.get("safety_reasons", [])),
        "protective_actions": " | ".join(state.get("protective_actions", [])),
        "evidence_status": state.get("evidence_status", "UNKNOWN"),
        "evidence_sources": " | ".join(
            item.get("source", "") for item in state.get("evidence", [])
        ),
        "evidence_summary": " | ".join(state.get("evidence_summary", [])),
        "retrieval_backend": state.get("retrieval_backend", "unknown"),
    })

    state["explanation"] = str(response.content)
    return mark_complete(state, "explainer_agent")