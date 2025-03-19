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
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.documents import Document
import os
import google
import vertexai
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings
from app.retrievers import get_compressor, get_retriever
from app.templates import format_docs, rag_template

LOCATION = "us-central1"
LLM = "gemini-2.0-flash-001"
EMBEDDING_MODEL = "text-embedding-005"
EMBEDDING_COLUMN = "embedding"
TOP_K = 5

data_store_region = os.getenv("DATA_STORE_REGION", "us")
data_store_id = os.getenv("DATA_STORE_ID", "study-help-datastore")

credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=LOCATION)

embedding = VertexAIEmbeddings(
    project=project_id, location=LOCATION, model_name=EMBEDDING_MODEL
)

retriever = get_retriever(
    project_id=project_id,
    data_store_id=data_store_id,
    data_store_region=data_store_region,
    embedding=embedding,
    embedding_column=EMBEDDING_COLUMN,
    max_documents=10,
)
compressor = get_compressor(
    project_id=project_id,
)

@tool(response_format="content_and_artifact")
def retrieve_docs(query: str) -> tuple[str, list[Document]]:
    """
    Useful for retrieving relevant documents based on a query.
    Use this when you need additional information to answer a question.

    Args:
        query (str): The user's question or search query.

    Returns:
        List[Document]: A list of the top-ranked Document objects, limited to TOP_K (5) results.
    """
    # Use the retriever to fetch relevant documents based on the query
    retrieved_docs = retriever.invoke(query)
    # Re-rank docs with Vertex AI Rank for better relevance
    ranked_docs = compressor.compress_documents(documents=retrieved_docs, query=query)
    # Format ranked documents into a consistent structure for LLM consumption
    formatted_docs = format_docs.format(docs=ranked_docs)

    return formatted_docs, ranked_docs

tools = [retrieve_docs]

llm1 = ChatVertexAI(model=LLM, temperature=0, max_tokens=1024, streaming=True)

llm2 = ChatVertexAI(model=LLM, temperature=0, max_tokens=1024, streaming=True).bind_tools(
    tools, tool_choice="any"
)

# Set up response chain
response_chain = rag_template | llm1

def generate_node(
    state: MessagesState, config: RunnableConfig
) -> dict[str, BaseMessage]:
    """Generates a response using the RAG template and returns it as a message."""
    response = response_chain.invoke(state, config)
    return {"messages": response}

# 3. Define workflow components
def should_continue(state: MessagesState) -> str:
    """Determines whether to use tools or end the conversation."""
    last_message = state["messages"][-1]
    return "tools" if last_message.tool_calls else END

def call_model(state: MessagesState, config: RunnableConfig) -> dict[str, BaseMessage]:
    """Calls the language model and returns the response."""
    system_message = (
        "You are a helpful coaching agent. When the user asks for an exercise, first ask "
        "on which kind on subject and chapter."
    )

    messages_with_system = [{"type": "system", "content": system_message}] + state[
        "messages"
    ]
    # Forward the RunnableConfig object to ensure the agent is capable of streaming the response.
    response = llm2.invoke(messages_with_system, config)
    return {"messages": response}

# 4. Create the workflow graph
workflow = StateGraph(MessagesState)
workflow.add_node("coach_agent", call_model)
workflow.add_node("exercise_generator_agent", generate_node)
workflow.add_node(
    "tools",
    ToolNode(
        tools=tools,
        # With False, tool errors won't be caught by LangGraph
        handle_tool_errors=False,
    ),
)

workflow.set_entry_point("coach_agent")

# 5. Define graph edges
workflow.add_conditional_edges("coach_agent", should_continue)
workflow.add_edge("tools", "exercise_generator_agent")
workflow.add_edge("exercise_generator_agent", "coach_agent")


# 6. Compile the workflow
agent = workflow.compile()
