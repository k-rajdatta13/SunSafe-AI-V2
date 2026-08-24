from agents import explainer_agent
def test_unsupported_request_does_not_call_gemini():
    called = False
    class FailingChain:
        def invoke(self, payload):
            nonlocal called
            called = True
            raise AssertionError("Gemini must not be called for unsupported requests")
    original_chain = explainer_agent.chain
    explainer_agent.chain = FailingChain()
    try:
        state = {
            "intent": "unsupported",
            "user_query": "Will the stock market rise tomorrow because of the weather?",
            "completed_agents": [],
            "trace": [],
        }
        result = explainer_agent.explainer_agent_node(state)
        assert called is False
        assert result["verification_status"] == "NOT_REQUIRED"
        assert "stock-market" in result["explanation"]
        assert "SunSafe AI" in result["explanation"]
    finally:
        explainer_agent.chain = original_chain
