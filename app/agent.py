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

import os

import google
import vertexai
from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig

from app.callbacks import (
    before_model_callback,
    before_tool_callback,
)
from app.instructions import root_agent_instructions
from app.tools import (
    get_bq_data,
    get_subjects_chapters_available,
    question_eval_agent_tool,
    question_generation_agent_tool,
)

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

LLM = "gemini-2.0-flash-001"
TOP_K = 5
TEMPERATURE = 0.0

vertexai.init(
    project=project_id,
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)

root_agent = Agent(
    model=LLM,
    name="student_helper_agent",
    instruction=root_agent_instructions,
    tools=[
        get_bq_data,
        question_generation_agent_tool,
        question_eval_agent_tool,
        get_subjects_chapters_available,
    ],
    before_model_callback=before_model_callback,
    before_tool_callback=before_tool_callback,
    generate_content_config=GenerateContentConfig(temperature=TEMPERATURE),
)
