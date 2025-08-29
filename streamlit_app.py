import json
import os
import requests
import streamlit as st

BACKEND_URL = os.environ.get("F1_API_URL", "http://localhost:8000")

st.set_page_config(page_title="F1 Race Predictor", page_icon="🏁", layout="wide")
st.title("F1 Race Predictor 🏁")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Inputs")
    # Load options from data files for convenience
    base_path = os.path.join(os.path.dirname(__file__), "backend", "data")
    with open(os.path.join(base_path, "tracks.json")) as f:
        tracks = json.load(f)
    with open(os.path.join(base_path, "drivers.json")) as f:
        drivers = json.load(f)

    track_names = [f"{t['name']} ({t['code']})" for t in tracks]
    track_choice = st.selectbox("Track", track_names, index=track_names.index("Italy (Monza) (ITA)"))
    track_code = track_choice.split("(")[-1].strip(")")

    weather = st.selectbox("Weather", ["dry", "wet"], index=0)
    safety_car = st.slider("Safety car chance", 0.0, 1.0, 0.2, 0.05)

    st.markdown("### Optional: Qualifying positions")
    qual_expander = st.expander("Add qualifying data (lower is better)")
    qualifying = {}
    with qual_expander:
        for d in drivers:
            q = st.number_input(f"{d['name']}", min_value=0, max_value=20, value=0, step=1, key=f"q_{d['name']}")
            if q and q > 0:
                qualifying[d['name']] = int(q)

    st.markdown("### Optional: Recent results")
    recent_expander = st.expander("Add recent results (e.g., P3, P7, DNF)")
    recent_results = {}
    with recent_expander:
        for d in drivers:
            text = st.text_input(f"{d['name']} results (comma-separated)", value="", key=f"r_{d['name']}")
            if text.strip():
                recent_results[d['name']] = [t.strip() for t in text.split(',') if t.strip()]

    if st.button("Predict"):
        payload = {
            "track": track_code,
            "weather": weather,
            "safety_car_chance": safety_car,
            "qualifying": qualifying,
            "recent_results": recent_results,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=30)
            resp.raise_for_status()
            predictions = resp.json().get("predictions", [])
            st.session_state["predictions"] = predictions
        except Exception as e:
            st.error(f"Failed to fetch predictions: {e}")

with col2:
    st.subheader("Results")
    predictions = st.session_state.get("predictions")
    if predictions:
        points_table = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
        for i, p in enumerate(predictions[:10]):
            pts = points_table[i] if i < len(points_table) else 0
            st.markdown(f"**{i+1}. {p['driver']}** — {p['team']} • Score: {p['score']} • Points: {pts}")
    else:
        st.info("Click Predict to see results.")


