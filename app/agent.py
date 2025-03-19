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

# mypy: disable-error-code="union-attr"
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from .crew.crew import StudyHelperCrew

LOCATION = "us-central1"
LLM = "gemini-2.0-flash-001"


@tool
def study_helper_tool(topic: str, age: int) -> str:
    """Use this tool to generate sample test questions and evaluate the students their answers. Give them constructive feedback."""
    inputs = {"topic": topic, "age": age}
    return StudyHelperCrew().crew().kickoff(inputs=inputs)


tools = [study_helper_tool]

# 2. Set up the language model
llm = ChatVertexAI(
    model=LLM, location=LOCATION, temperature=0, max_tokens=4096, streaming=True
).bind_tools(tools)


# 3. Define workflow components
def should_continue(state: MessagesState) -> str:
    """Determines whether to use the crew or end the conversation."""
    last_message = state["messages"][-1]
    return "study_helper_crew" if last_message.tool_calls else END


def call_model(state: MessagesState, config: RunnableConfig) -> dict[str, BaseMessage]:
    """Calls the language model and returns the response."""
    # system_message = (
    #     "You are an expert Teacher.\n"
    #     "Your role is to help the students prepare for tests and learn by practicing the materials "
    #     "by giving them sample questions.\n"
    #     "You will evaluate the answer of the students and give them feedback.\n"
    #     "Questions are asked one by one so the student can focus on one question at a time.\n"
    #     "If the answer of the student is incorrect, you will correct them in a constructive and positive way.\n"
    #     "If their answer is incomplete you give them the complete answer.\n"
    #     "If the answer is very close to the correct one but has some spelling mistakes, the answer is correct but you can correct their spelling mistakes.\n"
    #     "Keep on giving them questions until they say they have had enough, you don't need to ask for confirmation to give them the following question.\n"
    #     "Remember, you are an expert teacher trying to encourage the students to keep on learning.\n "
    #     "Be positive and encouriging at all times."
    # )
    system_message = (
        "You are an expert Teacher.\n"
        "Your role is to help the students prepare for tests and learn by practicing the materials "
        "by giving them sample questions.\n"
        "You ask the student what topic they want to practice and what age they have.\n"
        "You can then use the tool to generate the questions and evaluate them."
    )

    messages_with_system = [{"type": "system", "content": system_message}] + state[
        "messages"
    ]
    # Forward the RunnableConfig object to ensure the agent is capable of streaming the response.
    response = llm.invoke(messages_with_system, config)
    return {"messages": response}


def welcome(state: MessagesState) -> dict[str, BaseMessage]:
    """Gives a welcome message to the student."""
    if state["messages"]:
        # We've already greeted the user
        return {"messages": []}
    # Return a greeting ,since no message has been sent
    return {
        "messages": [
            AIMessage(
                content="Hi welcome to the study helper crew.\nHow old are you and what topic would you like to practice?"
            )
        ]
    }


# 4. Create the workflow graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", lambda state: welcome(state))
workflow.add_node("study_helper_crew", ToolNode(tools))
workflow.set_entry_point("agent")

# 5. Define graph edges
# workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("agent", "study_helper_crew")
workflow.add_conditional_edges("study_helper_crew", should_continue)

# 6. Compile the workflow
agent = workflow.compile()

agent.invoke({"messages": []})
