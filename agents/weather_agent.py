"""Tool-using weather intelligence agent."""
from state import SunState
from agents.common import mark_complete
from tools.weather_api import get_coordinates, get_weather, get_hourly_forecast

WEATHER_TOOLS = {
    "geocode_city": get_coordinates,
    "get_current_weather": get_weather,
    "get_hourly_forecast": get_hourly_forecast,
}

def weather_agent_node(state: SunState) -> SunState:
    city = state["city"]
    location = WEATHER_TOOLS["geocode_city"](city)
    current = WEATHER_TOOLS["get_current_weather"](location["latitude"], location["longitude"])
    forecast = WEATHER_TOOLS["get_hourly_forecast"](location["latitude"], location["longitude"])
    state.update({
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "country": location["country"],
        "temperature": current["temperature"],
        "uv_index": current["uv_index"],
        "cloud_cover": current["cloud_cover"],
        "relative_humidity": current["relative_humidity"],
        "wind_speed": current["wind_speed"],
        "weather_code": current["weather_code"],
        "hourly_forecast": forecast,
    })
    return mark_complete(
        state,
        "weather_agent",
        event="tools_used",
        tools=["geocode_city", "get_current_weather", "get_hourly_forecast"],
    )
