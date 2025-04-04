from dotenv import load_dotenv
import os
load_dotenv()
from agent.agent import pet_graph
from agent.utils import _print_event
import uuid
print("DEBUG: ANTHROPIC_API_KEY =", os.getenv("ANTHROPIC_API_KEY"))

def test_interactive_session():
    """
    Starts an interactive testing session with the AI agent using LangGraph's checkpointing.
    State is preserved automatically via thread_id using MemorySaver.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    printed_messages = set()
    print("🧠 Testing session started. Type 'exit' to stop.")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Exiting session.")
            break

        message_payload = {"messages": [("user", user_input)]}
        events = pet_graph.stream(message_payload, config, stream_mode="values")
        for event in events:
            _print_event(event, printed_messages)

if __name__ == "__main__":
    test_interactive_session()

