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

# ruff: noqa: RUF015
import json
import os
import uuid
from typing import Any

from utils.chat_utils import save_chat

EMPTY_CHAT_NAME = "Empty chat"
NUM_CHAT_IN_RECENT = 3
DEFAULT_BASE_URL = "http://localhost:8000/"

DEFAULT_REMOTE_AGENT_ENGINE_ID = "N/A"
if os.path.exists("deployment_metadata.json"):
    with open("deployment_metadata.json") as f:
        DEFAULT_REMOTE_AGENT_ENGINE_ID = json.load(f)["remote_agent_engine_id"]
DEFAULT_AGENT_CALLABLE_PATH = "app.agent_engine_app.AgentEngineApp"


class SideBar:
    """Manages the sidebar components of the Streamlit application."""

    def __init__(self, st: Any) -> None:
        """
        Initialize the SideBar.

        Args:
            st (Any): The Streamlit object for rendering UI components.
        """
        self.st = st

    def init_side_bar(self) -> None:
        """Initialize and render the sidebar components."""
        with self.st.sidebar:
            default_agent_type = (
                "Remote URL" if os.path.exists("Dockerfile") else "Local Agent"
            )
            self.user = self.st.text_input(
                label="User Name", placeholder="Firstname Lastname", value=""
            )
            use_agent_path = self.st.selectbox(
                "Select Agent Type",
                ["Local Agent", "Remote Agent Engine ID", "Remote URL"],
                index=["Local Agent", "Remote Agent Engine ID", "Remote URL"].index(
                    default_agent_type
                ),
                help="'Local Agent' uses a local implementation, 'Remote Agent Engine ID' connects to a deployed Vertex AI agent, and 'Remote URL' connects to a custom endpoint.",
            )

            if use_agent_path == "Local Agent":
                self.agent_callable_path = self.st.text_input(
                    label="Agent Callable Path",
                    value=os.environ.get(
                        "AGENT_CALLABLE_PATH", DEFAULT_AGENT_CALLABLE_PATH
                    ),
                )
                self.remote_agent_engine_id = None
            elif use_agent_path == "Remote Agent Engine ID":
                self.remote_agent_engine_id = self.st.text_input(
                    label="Remote Agent Engine ID",
                    value=os.environ.get(
                        "REMOTE_AGENT_ENGINE_ID", DEFAULT_REMOTE_AGENT_ENGINE_ID
                    ),
                )
                self.agent_callable_path = None
            self.st.session_state["app_id"] = self.remote_agent_engine_id
            col1, col2, col3 = self.st.columns(3)
            with col1:
                if self.st.button("+ New chat"):
                    if (
                        len(
                            self.st.session_state.user_chats[
                                self.st.session_state["session_id"]
                            ]["messages"]
                        )
                        > 0
                    ):
                        self.st.session_state.run_id = None

                        self.st.session_state["session_id"] = str(uuid.uuid4())
                        self.st.session_state.session_db.get_session(
                            session_id=self.st.session_state["session_id"],
                        )
                        self.st.session_state.user_chats[
                            self.st.session_state["session_id"]
                        ] = {
                            "title": EMPTY_CHAT_NAME,
                            "messages": [],
                        }

            with col2:
                if self.st.button("Delete chat"):
                    self.st.session_state.run_id = None
                    self.st.session_state.session_db.clear()
                    self.st.session_state.user_chats.pop(
                        self.st.session_state["session_id"]
                    )
                    if len(self.st.session_state.user_chats) > 0:
                        chat_id = list(self.st.session_state.user_chats.keys())[0]
                        self.st.session_state["session_id"] = chat_id
                        self.st.session_state.session_db.get_session(
                            session_id=self.st.session_state["session_id"],
                        )
                    else:
                        self.st.session_state["session_id"] = str(uuid.uuid4())
                        self.st.session_state.user_chats[
                            self.st.session_state["session_id"]
                        ] = {
                            "title": EMPTY_CHAT_NAME,
                            "messages": [],
                        }
            with col3:
                if self.st.button("Save chat"):
                    save_chat(self.st)

            self.st.subheader("Recent")  # Style the heading

            all_chats = list(reversed(self.st.session_state.user_chats.items()))
            for chat_id, chat in all_chats[:NUM_CHAT_IN_RECENT]:
                if self.st.button(chat["title"], key=chat_id):
                    self.st.session_state.run_id = None
                    self.st.session_state["session_id"] = chat_id
                    self.st.session_state.session_db.get_session(
                        session_id=self.st.session_state["session_id"],
                    )

            with self.st.expander("Other chats"):
                for chat_id, chat in all_chats[NUM_CHAT_IN_RECENT:]:
                    if self.st.button(chat["title"], key=chat_id):
                        self.st.session_state.run_id = None
                        self.st.session_state["session_id"] = chat_id
                        self.st.session_state.session_db.get_session(
                            session_id=self.st.session_state["session_id"],
                        )
