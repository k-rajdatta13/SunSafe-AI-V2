from agents.decision_agent import decision_agent_node
def test_afternoon_query_selects_afternoon_window():
    state = {
        "user_query": "I'm going hiking outdoors this afternoon. What precautions should I take?",
        "hard_stop": False,
        "hourly_forecast": [
            {"time": "2026-08-25T09:00", "temperature": 25, "uv_index": 2, "cloud_cover": 10},
            {"time": "2026-08-25T12:00", "temperature": 29, "uv_index": 5, "cloud_cover": 10},
            {"time": "2026-08-25T15:00", "temperature": 28, "uv_index": 3, "cloud_cover": 10},
            {"time": "2026-08-25T17:00", "temperature": 27, "uv_index": 2, "cloud_cover": 10},
            {"time": "2026-08-25T23:00", "temperature": 24, "uv_index": 0, "cloud_cover": 5},
        ],
        "completed_agents": [],
        "trace": [],
    }
    result = decision_agent_node(state)
    assert result["best_time"] in {"12:00 PM", "3:00 PM", "5:00 PM"}
    assert result["best_time"] != "11:00 PM"
def test_hard_stop_does_not_select_outdoor_window():
    state = {
        "user_query": "I'm going hiking this afternoon.",
        "hard_stop": True,
        "hourly_forecast": [
            {"time": "2026-08-25T15:00", "temperature": 28, "uv_index": 3, "cloud_cover": 10},
        ],
        "completed_agents": [],
        "trace": [],
    }
    result = decision_agent_node(state)
    assert result["best_time"] == "No recommended direct-sun window under current safety conditions"
