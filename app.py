import streamlit as st
import google.generativeai as genai
import os
import time
import json
import folium
from streamlit_folium import st_folium

# --- Page Config ---
st.set_page_config(page_title="Vagabond AI", page_icon="🌍", layout="wide", initial_sidebar_state="collapsed")

# --- App Memory (Session State) ---
# This prevents the app from forgetting your data when you click different tabs
if "itinerary_data" not in st.session_state:
    st.session_state.itinerary_data = None
if "current_destination" not in st.session_state:
    st.session_state.current_destination = None

# --- Advanced CSS Injection ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #090b10; color: #e2e8f0; }
    .hero-text {
        font-size: 4rem; font-weight: 800;
        background: -webkit-linear-gradient(45deg, #ff4b4b, #ff8f00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0px; padding-bottom: 0px;
    }
    .subtitle {
        text-align: center; color: #94a3b8; font-size: 1.2rem;
        font-weight: 400; margin-top: -10px; margin-bottom: 40px;
    }
    div[data-testid="stForm"], div[data-testid="stContainer"] {
        background-color: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 30px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- Hero Section ---
st.markdown("<h1 class='hero-text'>VAGABOND AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Generative travel blueprints tailored to your pace.</p>", unsafe_allow_html=True)

# --- API Key Setup ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("🔑 Enter Gemini API Key (Local Use):", type="password")

# --- Interactive Form Widget ---
with st.form("trip_form", border=True):
    col1, col2, col3 = st.columns([2, 1.5, 1])
    with col1: destination = st.text_input("📍 Destination", placeholder="e.g., Tokyo, Japan")
    with col2: vibe = st.selectbox("🎭 Travel Vibe", ["Adventure", "Relaxing / Luxury", "Foodie", "Art & History", "Nightlife"])
    with col3: days = st.number_input("📅 Days", min_value=1, max_value=14, value=3)
    
    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col: submitted = st.form_submit_button("Generate Blueprint", use_container_width=True)

# --- Logic & Output Engine ---
if submitted:
    if api_key and destination:
        st.toast(f"Locking in destination: {destination}...", icon="🌍")
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
            
            prompt = f"""
            Act as an elite bespoke travel planner. Create a highly detailed {days}-day {vibe.lower()} itinerary for {destination}.
            You MUST return a valid JSON object matching this exact schema:
            {{
                "overview": "A compelling 2-sentence hook about this specific trip.",
                "coordinates": {{ "lat": <accurate latitude float>, "lng": <accurate longitude float> }},
                "days": [
                    {{
                        "day": 1,
                        "theme": "Theme of the day",
                        "morning": "Detailed morning plan",
                        "afternoon": "Detailed afternoon plan",
                        "evening": "Detailed evening plan"
                    }}
                ],
                "local_intel": ["Tip 1", "Tip 2", "Tip 3"]
            }}
            """
            
            with st.spinner("Plotting coordinates and scouting locations..."):
                response = model.generate_content(prompt)
                
                # Save the data into app memory
                st.session_state.itinerary_data = json.loads(response.text)
                st.session_state.current_destination = destination.title()
            
            st.toast("Blueprint Compiled Successfully!", icon="✨")
                
        except Exception as e:
            st.error(f"Execution Error: {e}")
    else:
        st.warning("Please specify a destination before generating.")

# --- Render the UI if Data Exists in Memory ---
if st.session_state.itinerary_data:
    data = st.session_state.itinerary_data
    
    st.markdown("<br>", unsafe_allow_html=True)
    met1, met2, met3 = st.columns(3)
    met1.metric(label="Destination", value=st.session_state.current_destination)
    met2.metric(label="Latitude", value=data['coordinates']['lat'])
    met3.metric(label="Longitude", value=data['coordinates']['lng'])
    
    st.markdown(f"> *{data['overview']}*")
    st.divider()
    
    # --- Three-Tab Layout ---
    tab1, tab2, tab3 = st.tabs(["🗺️ DAILY TIMELINE", "📍 SPATIAL MAP", "💡 LOCAL INTELLIGENCE"])
    
    with tab1:
        st.markdown("### The Itinerary")
        for day in data["days"]:
            with st.expander(f"Day {day['day']} — {day['theme']}", expanded=(day['day'] == 1)):
                m_col, a_col, e_col = st.columns(3)
                with m_col: st.info(f"**🌅 Morning**\n\n{day['morning']}")
                with a_col: st.warning(f"**☀️ Afternoon**\n\n{day['afternoon']}")
                with e_col: st.error(f"**🌙 Evening**\n\n{day['evening']}")
    
    with tab2:
        st.markdown("### Destination Overview")
        # Initialize an interactive map centered on the AI-generated coordinates
        m = folium.Map(location=[data['coordinates']['lat'], data['coordinates']['lng']], zoom_start=11, tiles="CartoDB dark_matter")
        # Add a marker for the destination
        folium.Marker(
            [data['coordinates']['lat'], data['coordinates']['lng']], 
            popup=st.session_state.current_destination, 
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        # Render the map in Streamlit
        st_folium(m, width=1000, height=500, returned_objects=[])

    with tab3:
        st.markdown("### Insider Knowledge")
        for tip in data["local_intel"]:
            st.success(f"**🕵️‍♂️ Tip:** {tip}")
        
        # A sleek download button for the raw JSON data
        json_string = json.dumps(data, indent=4)
        st.download_button(
            label="Download Itinerary Data",
            data=json_string,
            file_name=f"{st.session_state.current_destination.lower()}_itinerary.json",
            mime="application/json",
            type="primary"
        )