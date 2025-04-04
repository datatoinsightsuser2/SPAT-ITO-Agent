
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

def handle_tool_error(state: dict) -> dict:
    error_msg = state.get("error", "An unknown error occurred.")
    tool_calls = state["messages"][-1].tool_calls if "messages" in state else []
    if "Email not provided" in error_msg:
        user_response = "I couldn't find your email. Could you please provide your registered email?"
        next_stage = "awaiting_email"
    elif "No user found" in error_msg:
        user_response = "I couldn't find an account with that email. Could you try again?"
        next_stage = "awaiting_email"
    elif "Error reading CSV" in error_msg:
        user_response = "There was an issue fetching your information. Please try again later."
        next_stage = "error"
    else:
        user_response = "Something went wrong. Let me know if you'd like to try again."
        next_stage = "error"
    state["current_stage"] = next_stage
    return {
        "messages": [
            ToolMessage(
                content=user_response,
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ],
        "error": None
    }

def create_tool_node_with_fallback(tools: list) -> ToolNode:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)

def format_stream_event(event: dict, _printed: set, max_length=1500) -> str:
    """Formats a streamed LangGraph event for Streamlit without printing."""
    current_state = event.get("dialog_state")
    message = event.get("messages")

    output = ""

    if current_state:
        output += f"_Current Stage: {current_state[-1]}_\n\n"

    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            _printed.add(message.id)
            output += msg_repr

    return output