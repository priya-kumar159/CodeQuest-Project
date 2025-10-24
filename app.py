# app.py (Poora code - Solution Box Theek Kar Diya)
import streamlit as st
import json
import os
import random
from datetime import datetime
import gspread  
import pandas as pd 

# --- File aur Data Setup ---
DATA_DIR = "data"
CHALLENGES_FILE = os.path.join(DATA_DIR, "challenges.json")
SHEET_TITLE = "CodeQuest_Progress"

# --- Database Integration (Naye Functions) ---

@st.cache_resource(ttl=3600)
def get_gsheet_client():
    """Google Sheets client ko Streamlit Secrets se authenticate karta hai."""
    try: 
        gc = gspread.service_account_from_dict(st.secrets)
        return gc
    except Exception as e:
        try:
            # Yeh local run ke liye service_account.json file dhoondhega
            gc = gspread.service_account(filename="service_account.json")
            return gc
        except Exception as e2:
            st.error(f"Error connecting to Google Sheets. Is 'service_account.json' file correct and shared with the Sheet?")
            print(f"GSpread Error: {e} / {e2}") 
            return None

def load_progress_data():
    """Google Sheet se saara progress data load karta hai."""
    gc = get_gsheet_client()
    if not gc: return pd.DataFrame(columns=['timestamp', 'mood', 'challenge_id', 'points', 'title'])
    try:
        sheet = gc.open(SHEET_TITLE).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.write(f"Progress load error: {e}")
        return pd.DataFrame(columns=['timestamp', 'mood', 'challenge_id', 'points', 'title'])

def add_progress_gsheet(challenge, mood):
    """Naya entry Google Sheet mein append karta hai."""
    gc = get_gsheet_client()
    if not gc: return 0 

    try:
        sheet = gc.open(SHEET_TITLE).sheet1
        new_entry = [
            datetime.utcnow().isoformat(),
            mood,
            challenge.get("id"),
            challenge.get("points", 0),
            challenge.get("title")
        ]
        sheet.append_row(new_entry)
        df = load_progress_data()
        df['points'] = pd.to_numeric(df['points'], errors='coerce').fillna(0)
        return df['points'].sum()
    except Exception as e:
        st.error(f"Error saving progress: {e}")
        return 0

# --- Default Data, Utility Functions (Puraane) ---

EMOJI_MAP = {"😊": "happy", "🙂": "happy", "😃": "happy", "😢": "sad", "😥": "sad", "😴": "tired", "😫": "tired", "🤩": "excited", "😄": "excited"}
MOTIVATIONS = ["Small steps matter! 🚀", "Keep going — small wins stack up!", "Nice work! Consistency is the secret.", "Every line of code counts."]
DEFAULT_CHALLENGES = {
    "happy": [{"id": "happy_1", "title": "Reverse a String", "description": "Write a function that returns the reverse of a given string.", "points": 10, "solution": "def reverse_string(s):\n  return s[::-1]"}],
    "tired": [{"id": "tired_1", "title": "Warmup loop", "description": "Print numbers 1 to 5 using a loop.", "points": 5, "solution": "for i in range(1, 6):\n  print(i)"}],
    "excited": [{"id": "excited_1", "title": "Mini calculator", "description": "Create add/sub/mul/div functions.", "points": 20, "solution": "def add(a, b):\n  return a + b\n\ndef sub(a, b):\n  return a - b"}],
    "sad": [{"id": "sad_1", "title": "Gratitude list", "description": "Create a list of 3 things you're grateful for and print them.", "points": 5, "solution": "grateful = [\"Family\", \"Health\", \"Friends\"]\nfor item in grateful:\n  print(item)"}]
}

def ensure_challenges_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CHALLENGES_FILE):
        with open(CHALLENGES_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CHALLENGES, f, indent=2)

def load_challenges_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def detect_mood(raw):
    raw = raw.strip().lower()
    if raw in EMOJI_MAP: return EMOJI_MAP[raw]
    if "happy" in raw or "good" in raw: return "happy"
    if "tired" in raw or "sleep" in raw: return "tired"
    if "excited" in raw or "great" in raw: return "excited"
    if "sad" in raw or "down" in raw: return "sad"
    return random.choice(list(DEFAULT_CHALLENGES.keys()))

def pick_challenge(challenges, mood):
    mood_list = challenges.get(mood, [])
    if not mood_list:
        all_ch = [item for sublist in challenges.values() for item in sublist]
        return random.choice(all_ch) if all_ch else None
    return random.choice(mood_list)

# --- Streamlit Web App ka UI (Visual) Code ---

ensure_challenges_data()
challenges = load_challenges_json(CHALLENGES_FILE)
st.set_page_config(page_title="CodeQuest", page_icon="🎮")
st.title("CodeQuest 🎮")
st.write("Welcome to CodeQuest!")

# Session state 
if 'current_challenge' not in st.session_state: st.session_state.current_challenge = None
if 'mood' not in st.session_state: st.session_state.mood = ""
if 'motivation_message' not in st.session_state: st.session_state.motivation_message = ""
if 'points_message' not in st.session_state: st.session_state.points_message = ""

# Mood input form
with st.form(key="mood_form", clear_on_submit=True):
    mood_input = st.text_input("Enter your mood / emoji:")
    submit_button = st.form_submit_button(label="Submit")

    if submit_button and mood_input:
        st.session_state.mood = detect_mood(mood_input)
        st.session_state.current_challenge = pick_challenge(challenges, st.session_state.mood)
        # Purane messages clear karo
        st.session_state.motivation_message = ""
        st.session_state.points_message = ""

# Challenge display
if st.session_state.current_challenge:
    ch = st.session_state.current_challenge
    
    st.subheader("Suggested Challenge:")
    st.markdown(f"**{ch['title']}**")
    st.write(ch['description'])
    st.write(f"Points: {ch['points']}")

    st.text_area("Your Solution:", height=150, placeholder="Write your code here...")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("DONE"):
            total = add_progress_gsheet(ch, st.session_state.mood)
            st.session_state.points_message = f"Nice! +{ch['points']} pts. Total: {total} pts."
            st.session_state.motivation_message = random.choice(MOTIVATIONS)
            st.session_state.current_challenge = None
            # st.rerun()  <-- HATA DIYA

    with col2:
        if st.button("Show Solution"):
            # *** YAHAN CHANGE KIYA HAI (Blur Fix) ***
            # Ab solution clear dikhega
            st.code(ch.get("solution", "No solution available"), language="python")

    with col3:
        if st.button("SKIP"):
            st.session_state.motivation_message = "Skipped. Submit a new mood for a new challenge."
            st.session_state.points_message = ""
            st.session_state.current_challenge = None 
            # st.rerun()  <-- HATA DIYA

    with col4:
        if st.button("PROGRESS"):
            df_progress = load_progress_data()
            if not df_progress.empty:
                df_progress['points'] = pd.to_numeric(df_progress['points'], errors='coerce').fillna(0)
                total_points = df_progress['points'].sum()
                st.write(f"**Total Points: {total_points}**")
                st.write("Recent Activity:")
                st.dataframe(df_progress[['timestamp', 'mood', 'title', 'points']].tail(5).sort_index(ascending=False))
            else:
                 # Yeh message abhi sahi hai, kyunki aapne 'DONE' nahi dabaya hai
                 st.write("No progress entries found.")

# Messages display
if st.session_state.points_message:
    st.success(st.session_state.points_message)
if st.session_state.motivation_message:
    st.info(st.session_state.motivation_message)