# Phase 5.2 trace semantics fix

The duplicate `weather_agent` entry was caused by one Weather Agent execution
creating two trace records: weather_agent_node appended a `tools_used` event,
then mark_complete appended a second `completed` event.

This patch makes mark_complete accept event metadata and emits exactly one trace
entry. Weather Agent records its tools in that single event.

This does NOT suppress genuine LangGraph retries: if Weather Agent actually
executes multiple times, there will still be one trace entry per execution.

Run:
`.\\.venv\\Scripts\\python.exe -m pytest tests/test_weather_trace.py -q`

Then:
`.\\.venv\\Scripts\\python.exe evaluation\\live_integration.py`
