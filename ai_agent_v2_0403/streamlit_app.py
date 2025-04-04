# streamlit_app.py

import streamlit as st
import uuid
from agent.agent import pet_graph

st.set_page_config(page_title="🐾 Smart Pet Travel Assistant")
st.title("🐾 Smart Pet Travel Assistant")

# --- Initialize state
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = {"messages": []}

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "config" not in st.session_state:
    st.session_state.config = {"configurable": {"user_info": "", "thread_id": st.session_state.thread_id}}

# --- Display chat history
for msg in st.session_state.conversation_state["messages"]:
    role, content = msg
    with st.chat_message(role):
        st.markdown(content)

# --- Chat input
if user_input := st.chat_input("Say something about your pet travel..."):
    # Show user message
    st.session_state.conversation_state["messages"].append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Run graph with updated state
    result = pet_graph.invoke(st.session_state.conversation_state, st.session_state.config)

    # Extract final assistant message
    messages = result.get("messages", [])
    final_text = "[No response from assistant]"
    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, "content"):
            final_text = last_msg.content
        elif isinstance(last_msg, tuple):
            _, final_text = last_msg
        elif isinstance(last_msg, dict) and "content" in last_msg:
            final_text = last_msg["content"]

    # Show assistant message
    with st.chat_message("assistant"):
        st.markdown(final_text)

    st.session_state.conversation_state["messages"].append(("assistant", final_text))