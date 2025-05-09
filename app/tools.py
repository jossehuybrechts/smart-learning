import os

import google
import vertexai
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag

from app.question_evaluation_agent import create_question_eval_agent
from app.question_generation_agent import create_question_generation_agent
from app.utils.formatting import format_bq_string

RAG_LOCATION = "europe-west3"
LOCATION = "europe-west1"
LLM = "gemini-2.0-flash-001"

# Initialize Google Cloud and Vertex AI
credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=RAG_LOCATION)

rag_corpus_name = os.getenv("RAG_CORPUS_NAME", "student-helper-rag-corpus")
bq_dataset_id = os.getenv("DATASET_ID", "student_helper")
bq_table_id = os.getenv("TABLE_ID", "question_answer")
for corpus in rag.list_corpora():
    if corpus.display_name == rag_corpus_name:
        rag_corpus = corpus

rag_retrieval_config = rag.RagRetrievalConfig(top_k=5)


rag_resources = [
    rag.RagResource(
        rag_corpus=rag_corpus.name,
    )
]

student_helper_retrieval = VertexAiRagRetrieval(
    name="student_helper_retrieval",
    description="Tools to retrieve data for subject and chapter to generate questions about",
    rag_resources=rag_resources,
    similarity_top_k=5,
    vector_distance_threshold=0.5,  # use bigger threshold so it's easier to return documents for initial testing
)


question_generation_agent_tool = AgentTool(
    agent=create_question_generation_agent(llm=LLM, tools=[student_helper_retrieval]),
)
question_eval_agent_tool = AgentTool(
    agent=create_question_eval_agent(llm=LLM, tools=[question_generation_agent_tool]),
)


def get_bq_data(subject: str, chapter: str, tool_context: ToolContext) -> str:
    """
    Retrieves the student percentage score for a given user and topic from BigQuery.

    This tool queries a BigQuery table to calculate the average student score
    based on the provided topic and user ID. It returns the results as a
    formatted string.

    Args:
        topic (str): The topic for which to retrieve the average score.

    Returns:
        str:  A string containing the student percentage score, or an error message
              if the query fails. The results are formatted with each row
              represented as a dictionary string, separated by newlines.

    Raises:
        Exception: If an error occurs during the BigQuery query execution,
                   an error message is returned as a string.
    """
    from google.cloud import bigquery

    bigquery_client = bigquery.Client(location=LOCATION, project=project_id)

    user_id = tool_context.state["user_id"]
    session_id = tool_context.state["session_id"]

    sql_query = f"""
            SELECT
            SUM(student_score) AS total_student_score,
            SUM(max_score) AS total_max_score,
            (SUM(student_score) * 100.0 / SUM(max_score)) AS total_percentage
            FROM `{project_id}.{bq_dataset_id}.{bq_table_id}`
            WHERE userId = '{user_id}' AND sessionId = '{session_id}' AND subject = '{format_bq_string(subject)}' AND chapter = '{format_bq_string(chapter)}';
        """

    try:
        query_job = bigquery_client.query(sql_query)

        results = query_job.result()

        # Format results as a string
        formatted_results = ""
        for row in results:
            formatted_results += str(dict(row.items())) + "\n"

        return formatted_results

    except Exception as e:
        return f"Error executing BigQuery query: {e}"


def get_subjects_chapters_available(subject: str, tool_context: ToolContext) -> str:
    """
    Retrieves the available subjects from the RAG corpus whenever the user asks for the available subjects.

    Args:
        subject (str): The subject for which to retrieve the available chapters.

    Returns:
        str: A string containing the available subjects, or an error message
             if the retrieval fails.
    """

    vertexai.init(project=project_id, location=RAG_LOCATION)
    # try:
    if subject is None or subject == "":
        subjects = set()
        for document in rag.list_files(corpus_name=rag_corpus.name):
            print(document)
            subjects.add(document.gcs_source.uris[0].split("/")[3])
        return ", ".join(subjects)
    else:
        return [
            context.text
            for context in rag.retrieval_query(
                text=f"Welke hoofdstukken zijn er voor {subject}",
                rag_resources=rag_resources,
                rag_retrieval_config=rag_retrieval_config,
            ).contexts.contexts
        ]
    # except Exception as e:
    #     return f"Error retrieving available subjects: {e}"
