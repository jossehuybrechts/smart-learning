# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="unreachable"
import importlib
import uuid
from collections.abc import Generator
from typing import Any

import streamlit as st
import vertexai
from utils.multimodal_utils import format_content
from vertexai import agent_engines

st.cache_resource.clear()


@st.cache_resource
def get_remote_agent(remote_agent_engine_id: str) -> Any:
    """Get cached remote agent instance."""
    # Extract location and engine ID from the full resource ID.
    parts = remote_agent_engine_id.split("/")
    project_id = parts[1]
    location = parts[3]
    vertexai.init(project=project_id, location=location)
    return agent_engines.AgentEngine(remote_agent_engine_id)


@st.cache_resource()
def get_local_agent(agent_callable_path: str) -> Any:
    """Get cached local agent instance."""
    module_path, class_name = agent_callable_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    agent = getattr(module, class_name)(agent=module.root_agent)
    agent.set_up()
    return agent


class Client:
    """A client for streaming events from a server."""

    def __init__(
        self,
        agent_callable_path: str | None = None,
        remote_agent_engine_id: str | None = None,
    ) -> None:
        """Initialize the Client with appropriate configuration.

        Args:
            agent_callable_path: Path to local agent class
            remote_agent_engine_id: ID of remote Agent engine
        """
        if remote_agent_engine_id:
            self.agent = get_remote_agent(remote_agent_engine_id)
        else:
            if agent_callable_path is None:
                raise ValueError("agent_callable_path cannot be None")
            self.agent = get_local_agent(agent_callable_path)

    def log_feedback(self, feedback_dict: dict[str, Any], run_id: str) -> None:
        """Log user feedback for a specific run."""
        score = feedback_dict["score"]
        if score == "😞":
            score = 0.0
        elif score == "🙁":
            score = 0.25
        elif score == "😐":
            score = 0.5
        elif score == "🙂":
            score = 0.75
        elif score == "😀":
            score = 1.0
        feedback_dict["score"] = score
        feedback_dict["run_id"] = run_id
        feedback_dict["log_type"] = "feedback"
        feedback_dict.pop("type")
        if self.agent is not None:
            self.agent.register_feedback(feedback=feedback_dict)
        else:
            raise ValueError("No agent configured for feedback logging")

    def stream_messages(
        self, data: dict[str, Any]
    ) -> Generator[dict[str, Any], None, None]:
        """Stream events from the server, yielding parsed event data."""
        if type(self.agent.list_sessions(user_id=data["user_id"])) is not dict:
            sessions = self.agent.list_sessions(user_id=data["user_id"]).model_dump()[
                "sessions"
            ]
        else:
            sessions = self.agent.list_sessions(user_id=data["user_id"])["sessions"]
        if data["session_id"] not in [session["id"] for session in sessions]:
            self.agent.create_session(
                # app_name=data["app_id"],
                session_id=data["session_id"],
                user_id=data["user_id"],
                state={
                    "session_id": data["session_id"],
                    "user_id": data["user_id"],
                },
            )

        if type(self.agent.list_sessions(user_id=data["user_id"])) is not dict:
            sessions = self.agent.list_sessions(user_id=data["user_id"]).model_dump()[
                "sessions"
            ]
        else:
            sessions = self.agent.list_sessions(user_id=data["user_id"])["sessions"]
        yield from self.agent.stream_query(
            session_id=data["session_id"],
            user_id=data["user_id"],
            message=data["message"],
        )


class StreamHandler:
    """Handles streaming updates to a Streamlit interface."""

    def __init__(self, st: Any, initial_text: str = "") -> None:
        """Initialize the StreamHandler with Streamlit context and initial text."""
        self.st = st
        self.tool_expander = st.expander("Tool Calls:", expanded=False)
        self.container = st.empty()
        self.text = initial_text
        self.tools_logs = initial_text

    def new_token(self, token: str) -> None:
        """Add a new token to the main text display."""
        self.text += token
        self.container.markdown(format_content(self.text), unsafe_allow_html=True)

    def new_status(self, status_update: str) -> None:
        """Add a new status update to the tool calls expander."""
        self.tools_logs += status_update
        self.tool_expander.markdown(status_update)


class EventProcessor:
    """Processes events from the stream and updates the UI accordingly."""

    def __init__(
        self, st: Any, user_id: str, client: Client, stream_handler: StreamHandler
    ) -> None:
        """Initialize the EventProcessor with Streamlit context, client, and stream handler."""
        self.st = st
        self.user_id = user_id
        self.client = client
        self.stream_handler = stream_handler
        self.final_content = ""
        self.tool_calls: list[dict[str, Any]] = []
        self.current_run_id: str | None = None
        self.additional_kwargs: dict[str, Any] = {}

    def process_events(self) -> None:
        """Process events from the stream, handling each event type appropriately."""
        if (
            len(
                self.st.session_state.user_chats[self.st.session_state["session_id"]][
                    "messages"
                ]
            )
            == 0
        ):
            message = " "
        else:
            message = self.st.session_state.user_chats[
                self.st.session_state["session_id"]
            ]["messages"][-1]["content"][0]["text"]
        self.current_run_id = str(uuid.uuid4())
        # Set run_id in session state at start of processing
        self.st.session_state["run_id"] = self.current_run_id
        stream = self.client.stream_messages(
            data={
                "app_id": self.st.session_state["app_id"],
                "session_id": self.st.session_state["session_id"],
                "user_id": self.user_id,
                "message": message,
            }
        )
        # Each event is a tuple message, metadata. https://langchain-ai.github.io/langgraph/how-tos/streaming/#messages
        for message in stream:
            if isinstance(message, dict):
                for part in message["content"].get("parts"):
                    # if message.get("type") == "constructor":
                    #     message = message["kwargs"]

                    # Handle tool calls
                    if part.get("function_call"):
                        function_call = part["function_call"]
                        ai_message = {"type": "ai", "tool_calls": [function_call]}
                        self.tool_calls.append(ai_message)
                        msg = f"\n\nCalling tool: `{function_call['name']}` with args: `{function_call['args']}`"
                        self.stream_handler.new_status(msg)

                    # Handle tool responses
                    elif part.get("function_response"):
                        content = part["function_response"]
                        tool_message = {"type": "tool", "content": content}
                        self.tool_calls.append(tool_message)
                        msg = f"\n\nTool response: `{content}`"
                        self.stream_handler.new_status(msg)

                    # Handle AI responses
                    elif content := part["text"]:
                        self.final_content += content
                        self.stream_handler.new_token(content)

        # Handle end of stream
        if self.final_content:
            final_message = {
                "content": self.final_content,
                "type": "ai",
                "id": self.current_run_id,
            }
            #     AIMessage(
            #     content=self.final_content,
            #     id=self.current_run_id,
            #     additional_kwargs=self.additional_kwargs,
            # ).model_dump()
            session = self.st.session_state["session_id"]
            self.st.session_state.user_chats[session]["messages"] = (
                self.st.session_state.user_chats[session]["messages"] + self.tool_calls
            )
            self.st.session_state.user_chats[session]["messages"].append(final_message)
            self.st.session_state.run_id = self.current_run_id


def get_chain_response(
    st: Any, user_id: str, client: Client, stream_handler: StreamHandler
) -> None:
    """Process the chain response update the Streamlit UI.

    This function initiates the event processing for a chain of operations,
    involving an AI model's response generation and potential tool calls.
    It creates an EventProcessor instance and starts the event processing loop.

    Args:
        st (Any): The Streamlit app instance, used for accessing session state
                 and updating the UI.
        user_id (str): User Id of the user that uses the agent
        client (Client): An instance of the Client class used to stream events
                        from the server.
        stream_handler (StreamHandler): An instance of the StreamHandler class
                                      used to update the Streamlit UI with
                                      streaming content.

    Returns:
        None

    Side effects:
        - Updates the Streamlit UI with streaming tokens and tool call information.
        - Modifies the session state to include the final AI message and run ID.
        - Handles various events like chain starts/ends, tool calls, and model outputs.
    """
    processor = EventProcessor(st, user_id, client, stream_handler)
    processor.process_events()
