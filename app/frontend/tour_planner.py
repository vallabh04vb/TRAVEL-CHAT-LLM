import streamlit as st
import requests

# Function to authenticate user
def authenticate(username, password):
    # Test users with their usernames and passwords
    test_users = {
        "user1": "password1",
        "user2": "password2"
    }
    return test_users.get(username) == password

# Login function
def login():
    st.session_state["logged_in"] = False
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state["user_id"] = username
            st.session_state["logged_in"] = True
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# CSS styling
st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; color: #ffffff; font-family: Arial, sans-serif; }
    .title { font-size: 36px; font-weight: bold; color: #f7931e; text-align: center; margin-top: 20px; }
    .chat-container { border: 2px solid #f7931e; border-radius: 15px; padding: 20px; max-width: 800px; 
                      margin: auto; background-color: #2b2b2b; overflow-y: auto; height: 500px; 
                      display: flex; flex-direction: column-reverse; }
    .assistant-message { background-color: #d4f4dd; padding: 10px; border-radius: 8px; color: #1d1d1d; 
                         margin: 5px 0; font-weight: bold; display: inline-block; max-width: 75%; word-wrap: break-word; }
    .user-message { background-color: #cde7ff; padding: 10px; border-radius: 8px; color: #1d1d1d; margin: 5px 0;
                    font-weight: bold; display: inline-block; max-width: 75%; word-wrap: break-word; align-self: flex-end; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "history" not in st.session_state:
    st.session_state.history = []
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Main app logic
if not st.session_state["logged_in"]:
    st.markdown('<div class="title">Login to Access Travel Companion Chatbot</div>', unsafe_allow_html=True)
    login()
else:
    st.markdown('<div class="title">Travel Companion Chatbot</div>', unsafe_allow_html=True)
    user_id = st.session_state["user_id"]

    if len(st.session_state.history) == 0:
        st.session_state.history.append("Assistant: Welcome to your Travel Companion! Chat with me to plan your trip.")

    chat_history_html = '<div class="chat-container">'
    for message in reversed(st.session_state.history):
        if message.startswith("Assistant:"):
            chat_history_html += f'<div class="assistant-message">{message}</div>'
        else:
            chat_history_html += f'<div class="user-message">{message}</div>'
    chat_history_html += '</div>'
    st.markdown(chat_history_html, unsafe_allow_html=True)

    user_input = st.text_input("Enter your message:", value="", key="user_input_key")
    if st.button("Send") and user_input.strip():
        st.session_state.history.append(f"User: {user_input}")

        with st.spinner("Generating response..."):
            try:
                response = requests.post(
                    "http://localhost:8000/generate_response/",
                    json={"user_id": user_id, "message": user_input}
                )
                response.raise_for_status()
                assistant_response = response.json().get("response", "Error with the response")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred: {e}")
                assistant_response = "An unexpected error occurred."

        st.session_state.history.append(f"Assistant: {assistant_response}")
        st.experimental_rerun()
