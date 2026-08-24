"""
Validates user profile information.

The UI (CLI or Streamlit) collects inputs.
This node only validates and normalizes them.
"""

from state import SunState


def profile_node(state: SunState) -> SunState:

    print("\nProfile Node Running...")

    if not state.get("city"):
        raise ValueError("City is required.")

    if state["skin_type"] not in [1,2,3,4,5,6]:
        raise ValueError("Skin type must be between 1 and 6.")

    if state["body_area"] not in [10,25,50,80]:
        raise ValueError(
            "Body area must be 10, 25, 50 or 80."
        )

    if state["age"] <= 0:
        raise ValueError(
            "Age must be positive."
        )

    return state