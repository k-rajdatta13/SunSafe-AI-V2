from agents.weather_agent import weather_agent_node

def test_weather_agent_records_one_trace_entry(monkeypatch):
    monkeypatch.setattr(
        "agents.weather_agent.WEATHER_TOOLS",
        {
            "geocode_city": lambda city: {"latitude": 26.45, "longitude": 80.33, "country": "India"},
            "get_current_weather": lambda lat, lon: {
                "temperature": 30.0, "uv_index": 5.0, "cloud_cover": 20.0,
                "relative_humidity": 50.0, "wind_speed": 10.0, "weather_code": 1,
            },
            "get_hourly_forecast": lambda lat, lon: [],
        },
    )
    state = {"city": "Kanpur", "completed_agents": [], "trace": [{"agent": "orchestrator", "event": "plan_created"}]}
    result = weather_agent_node(state)
    entries = [e for e in result["trace"] if e.get("agent") == "weather_agent"]
    assert len(entries) == 1
    assert entries[0]["event"] == "tools_used"
    assert entries[0]["tools"] == ["geocode_city", "get_current_weather", "get_hourly_forecast"]
    assert result["completed_agents"] == ["weather_agent"]
