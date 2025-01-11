import os
import json
import datetime
import streamlit as st
from groq import Groq

# Set up Streamlit page configuration
st.set_page_config(
    page_title="EnlightAI",
    page_icon="🤖",
    layout="wide"
)

# File for storing chat history persistently
HISTORY_FILE = "chat_history.json"

# Load API key from configuration file
working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))
GROQ_API_KEY = config_data["GROQ_API_KEY"]
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Load saved chat history
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    return {}

# Save chat history
def save_history(chats):
    with open(HISTORY_FILE, "w") as f:
        json.dump(chats, f)

# Initialize Groq client
client = Groq()

# Initialize session state
if "chats" not in st.session_state or not isinstance(st.session_state.chats, dict):
    st.session_state.chats = load_history()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# Function to categorize chats by time
def categorize_chats(chats):
    today, yesterday, last_7_days = [], [], []
    now = datetime.datetime.now()

    for chat, messages in chats.items():
        if not isinstance(chat, str) or not chat.strip():
            continue
        try:
            first_message_time = datetime.datetime.strptime(messages[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
            delta = (now - first_message_time).days

            if delta == 0:
                today.append(chat)
            elif delta == 1:
                yesterday.append(chat)
            elif delta <= 7:
                last_7_days.append(chat)
        except (ValueError, KeyError):
            continue

    return today, yesterday, last_7_days

# Sidebar for navigating chats and managing parameters
with st.sidebar:
    st.header("**Chat History**")
    st.button("**Start New Chat**", key="start_new_chat", on_click=lambda: st.session_state.update({"current_chat": None}))

    today, yesterday, last_7_days = categorize_chats(st.session_state.chats)

    def display_chats(title, chat_list):
        st.write(f"{title}")
        for chat_name in chat_list:
            if st.button(chat_name[:40] + "...", key=chat_name):
                st.session_state.current_chat = chat_name

    display_chats("**Today**", today)
    display_chats("**Yesterday**", yesterday)
    display_chats("**Last 7 Days**", last_7_days)

    # Response Parameters Section
    st.header("**Response Parameters**")

    # Temperature slider
    st.session_state.temperature = st.slider(
        "**Temperature**",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Controls the randomness of responses. Higher values make the output more creative, while lower values make it more focused and deterministic."
    )

    # Max tokens slider
    st.session_state.max_tokens = st.slider(
        "**Max Tokens**",
        min_value=50,
        max_value=2000,
        value=500,
        step=50,
        help="Limits the maximum length of the response in tokens."
    )

    # Response type selection
    st.session_state.response_type = st.radio(
        "**Response Type**",
        options=["Brief", "Elaborate"],
        index=0,
        help="Choose whether you want concise or detailed answers."
    )

# CSS for styling
st.markdown("""<style>
    .message { padding: 8px; border-radius: 8px; max-width: 100%; margin: 5px 0; word-wrap: break-word; text-align: justify; }
    .user-message { background-color: #f7f7f7; border-radius: 8px; }
    .assistant-message { background-color: white; box-shadow: none; border-radius: 8px; }
</style>""", unsafe_allow_html=True)

# Display the page title
st.markdown(""" 
<div style="text-align: center;">
    <h1>Welcome to EnlightAI 🤖</h1>
    <h5><i>🌐 Smarter Conversations, ⚡ Faster Solutions</i></h5>
</div>
""", unsafe_allow_html=True)

with st.expander("**About this app**"):
    st.write(""" 
        **EnlightAI** is an AI-powered chatbot, powered by the **Llama 3.1-8b-instant model**, designed to:

        - Provide accurate, context-aware answers to user queries.
        - Store chat history persistently, allowing easy access to past conversations.
        - Categorize chats by time (Today, Yesterday, Last 7 Days) for better navigation.
        - Use response parameters to deliver personalized answers tailored to user needs.
    """)

# Display chat history
if st.session_state.current_chat:
    for message in st.session_state.chats[st.session_state.current_chat]:
        with st.chat_message(message["role"]):
            st.markdown(f"{message['role'].capitalize()}: {message['content']}")

# Handle user input
user_prompt = st.chat_input("Ask EnlightAI...")
if user_prompt:
    # If it's a new chat, initialize a new chat session with the user prompt as the name
    if not st.session_state.current_chat:
        st.session_state.current_chat = user_prompt[:40]
        st.session_state.chats[st.session_state.current_chat] = []

    # Add user message
    st.session_state.chats[st.session_state.current_chat].append({
        "role": "user",
        "content": user_prompt,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    with st.chat_message("user"):
        st.markdown(f"User: {user_prompt}")

    # Generate assistant response
    messages = [{"role": "system", "content": "You are a helpful assistant"}]
    messages += [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chats[st.session_state.current_chat]]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=st.session_state.temperature,
        max_tokens=st.session_state.max_tokens
    )
    assistant_response = response.choices[0].message.content

    # Adjust response type based on user selection
    if st.session_state.response_type == "Brief":
        assistant_response = assistant_response[:300]  # Truncate to 300 characters for brevity

    # Add assistant response to chat history
    st.session_state.chats[st.session_state.current_chat].append({
        "role": "assistant",
        "content": assistant_response,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_history(st.session_state.chats)

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(f"Assistant: {assistant_response}")