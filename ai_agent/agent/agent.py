from dotenv import load_dotenv
load_dotenv()

import json
import re
import csv
import shutil
import numpy as np
import openai
import requests
import uuid
import faiss
from pathlib import Path
from datetime import datetime

from langchain_core.tools import tool
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict
from typing import Annotated
from sentence_transformers import SentenceTransformer
from langchain_anthropic import ChatAnthropic
#tools and packages

from user_tools.fetch_user_info import fetch_user_info
from user_tools.airlines_freight_quote import airlines_freight_quote
from user_tools.ground_transfer import ground_transfer_agent_origin, ground_transfer_agent_destination,send_driver_notification
from user_tools.policy_lookup import pet_relocation_answer
from langchain_community.tools.tavily_search import TavilySearchResults
from agent.system_prompt import load_system_prompt
from agent.utils import handle_tool_error, tools_condition,_print_event


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_email: str
    user_info: dict
    ground_transfer_requested: bool
    origin_driver_options: list[str]
    origin_driver_emails: list[str]
    destination_driver_options: list[str]
    destination_driver_emails: list[str]
    current_stage: str

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        """
        Handles assistant execution and state transitions.
        Ensures AI reacts correctly to errors and missing information.
        """
        # Extract relevant data from state
        configuration = config.get("configurable", {})
        state = {**state, "user_info": configuration.get("user_info", "")}

        # Check if there’s an error in state
        error_msg = state.get("error", None)
        current_stage = state.get("current_stage", "")

        # If there’s an error, format a user-friendly response
        if error_msg:
            if current_stage == "awaiting_email":
                response = "I couldn't find your email. Can you provide your registered email?"
            else:
                response = "Something went wrong. Let me know if you'd like to try again."
            
            # Clear error after handling it
            state["error"] = None

            return {"messages": [{"role": "assistant", "content": response}]}

        # Otherwise, continue normal execution
        while True:
            result = self.runnable.invoke(state)

            # If the LLM returns an empty response, re-prompt
            if not result.tool_calls and (
                not result.content or
                (isinstance(result.content, list) and not result.content[0].get("text"))
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break

        return {"messages": result}

# Define Prompt
pet_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", load_system_prompt()),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

# Define tools
pet_tools = [
    TavilySearchResults(max_results=1),
    fetch_user_info,
    pet_relocation_answer,
    ground_transfer_agent_origin,
    ground_transfer_agent_destination,
    send_driver_notification,
    airlines_freight_quote,
]

llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=1)
pet_assistant_runnable = pet_assistant_prompt | llm.bind_tools(pet_tools)

# Build graph
builder = StateGraph(State)
builder.add_node("assistant", Assistant(pet_assistant_runnable))
builder.add_node("tools", ToolNode(pet_tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error"))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")
memory = MemorySaver()
pet_graph = builder.compile(checkpointer=memory)
print("Graph successfully built.")