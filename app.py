"""
SunSafe AI v2.0
Professional Streamlit Dashboard
"""

import streamlit as st
from graph import run_agent

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="SunSafe AI",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# CUSTOM CSS
# ==========================================================

st.markdown("""
<style>

.main{
    padding-top:1rem;
}

.block-container{
    padding-top:1rem;
}

div[data-testid="metric-container"]{
    background:#f8f9fa;
    border:1px solid #e6e6e6;
    border-radius:12px;
    padding:15px;
}

h1{
    color:#ff9800;
}

.footer{
    text-align:center;
    color:gray;
    font-size:14px;
    margin-top:40px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.title("☀ SunSafe AI")

    st.markdown("---")

    st.subheader("About")

    st.write(
        """
Evidence-grounded outdoor UV & heat safety decision support
built using a bounded, policy-constrained agent workflow:

- LangGraph
- Gemini
- Open-Meteo
- Rule Engine
- Local RAG / Vector Retrieval
- Streamlit
"""
    )

    st.markdown("---")

    st.subheader("Workflow")

    st.markdown("""
👤 User Profile

⬇

🌦 Weather API

⬇

⚠ Safety Assessment

⬇

📚 RAG Evidence

⬇

🎯 Decision + Verification

⬇

🤖 Gemini Explanation
""")

    st.markdown("---")

    st.subheader("Technology")

    st.write("Python")
    st.write("LangGraph")
    st.write("Gemini")
    st.write("Streamlit")
    st.write("RAG / Vector Retrieval")

    st.markdown("---")

    st.caption("Version 2.0 — final audit build")

# ==========================================================
# HEADER
# ==========================================================

st.title("☀ SunSafe AI")

st.caption(
    "Evidence-grounded UV & Outdoor Safety Decision Support"
)

st.divider()

# ==========================================================
# USER PROFILE
# ==========================================================

st.header("👤 User Profile")

user_query = st.text_input(
    "💬 What do you want to know?",
    value="Can I plan outdoor activity safely today?",
    help="The bounded orchestrator uses this request to select the safest workflow path. The safety policy remains deterministic.",
)

skin_options = {
    "Type I - Very Fair": 1,
    "Type II - Fair": 2,
    "Type III - Medium": 3,
    "Type IV - Olive": 4,
    "Type V - Brown": 5,
    "Type VI - Dark Brown / Black": 6
}

body_options = {
    "Face Only (~10%)": 10,
    "Face + Arms (~25%)": 25,
    "Face + Arms + Legs (~50%)": 50,
    "Almost Full Body (~80%)": 80
}

left, right = st.columns(2)

with left:

    city = st.text_input(
        "📍 City",
        placeholder="Example: Kanpur"
    )

    selected_skin = st.selectbox(
        "🧑 Skin Type",
        list(skin_options.keys())
    )

with right:

    age = st.number_input(
        "🎂 Age",
        min_value=1,
        max_value=120,
        value=25
    )

    selected_body = st.selectbox(
        "🩳 Body Area Exposed",
        list(body_options.keys())
    )

skin = skin_options[selected_skin]
body = body_options[selected_body]

st.caption("Skin type and exposed body area are retained as non-dosing profile context; V2 does not convert them into exposure-minute prescriptions.")

st.divider()

generate = st.button(
    "☀ Generate Recommendation",
    use_container_width=True,
    type="primary"
)




# ==========================================================
# RUN AI AGENT
# ==========================================================

if generate:

    if city.strip() == "":

        st.error("⚠ Please enter your city.")

        st.stop()

    with st.spinner(
        "🤖 Fetching live conditions, applying the safety policy and generating an explanation..."
    ):

        result = run_agent(
            city,
            skin,
            body,
            age,
            user_query=user_query
        )

    st.success("✅ Recommendation Generated Successfully!")

    with st.expander("🤖 Agent execution trace", expanded=False):
        st.write("Plan:", result.get("plan", []))
        st.write("Verification:", result.get("verification_status", "UNKNOWN"))
        st.json(result.get("trace", []))

    st.divider()

    # ==========================================================
    # WEATHER SUMMARY
    # ==========================================================

    st.header("🌦 Today's Weather")

    weather1, weather2, weather3 = st.columns(3)

    with weather1:

        st.metric(
            "📍 Location",
            f"{result['city']}, {result['country']}"
        )

        st.metric(
            "🌡 Temperature",
            f"{result['temperature']} °C"
        )

    with weather2:

        st.metric(
            "☀ UV Index",
            result["uv_index"]
        )

        st.metric(
            "🛡 Protection",
            result["uv_level"]
        )

    with weather3:

        if result["uv_index"] < 2:
            uv_status = "Very Low"

        elif result["uv_index"] < 5:
            uv_status = "Moderate"

        elif result["uv_index"] < 8:
            uv_status = "High"

        else:
            uv_status = "Very High"

        st.metric(
            "📈 UV Status",
            uv_status
        )

        st.metric(
            "🛡 Protection",
            "Required" if result["protection_required"] else "Standard precautions"
        )


    st.divider()

    # ==========================================================
    # SAFETY ASSESSMENT
    # ==========================================================

    st.header("🛡 Safety Assessment")

    risk1, risk2 = st.columns(2)

    with risk1:
        heat = result["heat_caution"]
        if heat == "LOW":
            st.success("🟢 Heat condition screening: LOW")
        elif heat == "CAUTION":
            st.warning("🟡 Heat condition screening: CAUTION")
        else:
            st.error("🔴 Heat condition screening: HIGH")

    with risk2:
        uv = result["uv_level"]
        if uv == "LOW":
            st.success("🟢 UV level: LOW")
        elif uv in {"MODERATE", "HIGH"}:
            st.warning(f"🟡 UV level: {uv}")
        else:
            st.error("🔴 UV level: VERY HIGH")

    st.info(result["overall_action"].replace("_", " ").title())

    st.divider()

    st.header("📚 Evidence & RAG Retrieval")
    st.caption(
        f"Retrieved {result.get('retrieval_count', 0)} authoritative evidence chunks "
        f"using {result.get('retrieval_backend', 'unknown')} vector retrieval."
    )

    for i, item in enumerate(result.get("evidence", []), start=1):
        with st.expander(
            f"{i}. {item.get('source', 'Source')} · score {item.get('score', 0):.3f}",
            expanded=(i == 1),
        ):
            st.write(item.get("claim", ""))
            st.caption(f"Topic: {item.get('topic', 'unknown')} · Chunk: {item.get('chunk_id', 'unknown')}")
            st.markdown(f"[Open authoritative source]({item.get('url', '')})")

    st.divider()
    st.header("🤖 Explanation")
    st.write(result.get("explanation", ""))

    st.divider()

    st.header("🌤 Conservative Outdoor Window")
    st.metric("Suggested start time", result["best_time"])
    st.caption("V2 does not prescribe a personalized UV-exposure duration. The selected window is an outdoor-activity planning aid, not a vitamin-D dose.")

    st.divider()

    st.header("Why this recommendation?")
    for reason in result.get("safety_reasons", []):
        st.write(f"• {reason}")

    st.header("Protective actions")
    for action in result.get("protective_actions", []):
        st.write(f"• {action}")

    st.divider()

    # ==========================================================
    # GEMINI AI EXPLANATION
    # ==========================================================

    st.header("🤖 AI Explanation")

    with st.expander(
        "Click to view Gemini explanation",
        expanded=True
    ):
        st.write(result["explanation"])

    st.divider()

    # ==========================================================
    # SAFETY TIPS
    # ==========================================================

    st.header("🩺 General Safety Guidance")

    st.info("""
• Seek shade and avoid prolonged direct sun when UV is elevated.

• Wear protective clothing, a broad-brimmed hat and UV-protective eyewear.

• Stay hydrated and avoid strenuous activity during the hottest part of the day.

• If you feel dizzy, confused, nauseated or unusually weak, stop activity and seek appropriate medical help.

• People with medical conditions or photosensitive disorders should consult a healthcare professional.
""")

    st.divider()

    # ==========================================================
    # DISCLAIMER
    # ==========================================================

    st.warning(
        """
This application provides general outdoor UV and heat-safety decision support.

It is **NOT** medical advice.

Recommendations are generated using:
- Open-Meteo Weather API
- Evidence-aligned deterministic safety policy
- Google Gemini AI for explanation only

Always consult a healthcare professional for personalized medical advice.
"""
    )

# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.markdown(
    """
<div class="footer">

☀ <b>SunSafe AI v2.0</b><br>

Built using LangGraph • Gemini • Open-Meteo • Streamlit

AI Engineering Portfolio Project — deterministic safety policy + bounded agents + RAG

</div>
""",
unsafe_allow_html=True
)