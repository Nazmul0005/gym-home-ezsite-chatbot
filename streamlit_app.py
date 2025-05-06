import streamlit as st
import requests
import json
from datetime import datetime

# Configure page settings
st.set_page_config(
    page_title="HealthFit AI Assistant",
    page_icon="💪",
    layout="centered"
)

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")

# FastAPI backend URL
BACKEND_URL = "http://localhost:5000"

def reset_chat():
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/reset",
            json={"sessionId": st.session_state.session_id}
        )
        if response.status_code == 200:
            st.session_state.messages = []
            st.success("Chat history has been reset!")
        else:
            st.error("Failed to reset chat history")
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")

def get_user_info():
    with st.expander("Configure User Profile"):
        user_info = {
            "name": st.text_input("Name", key="user_name"),
            "age": st.number_input("Age", min_value=1, max_value=120, key="user_age"),
            "fitness_level": st.select_slider(
                "Fitness Level",
                options=["Beginner", "Intermediate", "Advanced"],
                key="fitness_level"
            ),
            "goals": st.multiselect(
                "Fitness Goals",
                ["Weight Loss", "Muscle Gain", "Endurance", "Flexibility", "General Health"],
                key="goals"
            ),
            "health_conditions": st.text_area("Health Conditions (if any)", key="health_conditions"),
            "dietary_preferences": st.multiselect(
                "Dietary Preferences",
                ["Vegetarian", "Vegan", "Keto", "Paleo", "No restrictions"],
                key="dietary_prefs"
            )
        }
        return {k: v for k, v in user_info.items() if v}

# Main app layout
st.title("🏋️‍♂️ HealthFit AI Assistant")

# User profile configuration
user_info = get_user_info()

# Chat interface
st.markdown("### Chat with HealthFit AI")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get AI response
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={
                "message": prompt,
                "sessionId": st.session_state.session_id,
                "userInfo": user_info
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            with st.chat_message("assistant"):
                st.markdown(data["response"])
            st.session_state.messages.append({"role": "assistant", "content": data["response"]})
        else:
            st.error("Failed to get response from server")
    
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")

# Reset chat button
st.sidebar.button("Reset Chat", on_click=reset_chat)