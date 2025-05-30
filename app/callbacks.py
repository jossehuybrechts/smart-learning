import json
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


def store_results(
    user_id: str,
    session_id: str,
    subject: str,
    chapter: str,
    question: str,
    answer: str,
    student_score: int,
    max_score: int,
    difficulty: int,
) -> None:
    """
    After a user answers a question the result of the evaluation is stored in bigquery with this tool.
    """
    import datetime
    import os

    import google
    from google.cloud import bigquery

    from app.utils.formatting import format_bq_string

    LOCATION = "europe-west1"

    # Initialize Google Cloud and Vertex AI
    _, project_id = google.auth.default()

    bq_dataset_id = os.getenv("DATASET_ID", "student_helper")
    bq_table_id = os.getenv("TABLE_ID", "question_answer")

    bigquery_client = bigquery.Client(location=LOCATION, project=project_id)
    table_id = f"{project_id}.{bq_dataset_id}.{bq_table_id}"
    table = bigquery_client.get_table(table_id)
    rows_to_insert = [
        (
            user_id,
            session_id,
            format_bq_string(subject),
            format_bq_string(chapter),
            question,
            answer,
            student_score,
            max_score,
            difficulty,
            datetime.datetime.now(),
        )
    ]
    bigquery_client.insert_rows(table, rows_to_insert)


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmRequest | None:
    function_response = llm_request.contents[-1].parts[-1].function_response
    if function_response:
        if (
            "result" in function_response.response
        ):
            if "json" in function_response.response["result"]:
                result = json.loads(
                    function_response.response["result"]
                    .replace("\n", "")
                    .replace("None", "null")
                    .strip("`json ")
                )
            elif function_response.response["result"].startswith("{"):
                result = json.loads(
                    function_response.response["result"]
                    .replace("\n", "")
                    .replace("None", "null")
                    .replace("'", '"')
                )
            if result:
                if function_response.name == "question_generation_agent":
                    return LlmResponse(
                        content=types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text=f"{result['question']}\n\nMoeilijkheid: {result['difficulty']}/5\n\nScore: /{result['max_score']}"
                                )
                            ],
                        )
                    )
                elif function_response.name == "question_eval_agent":
                    store_results(
                        user_id=callback_context.state["user_id"],
                        session_id=callback_context.state["session_id"],
                        subject=result["subject"],
                        chapter=result["chapter"],
                        question=result["question"],
                        answer=result["answer"],
                        student_score=result["score"],
                        max_score=result["max_score"],
                        difficulty=result["difficulty"],
                    )
                    return LlmResponse(
                        content=types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text=f"{result['feedback']}\n\nMoeilijkheid: {result['difficulty']}/5\n\nScore: {result['score']}/{result['max_score']}\n\n---\n\n***Volgende vraag:***\n\n{result['next_question']['question']}\n\nMoeilijkheid: {result['next_question']['difficulty']}/5\n\nScore: /{result['next_question']['max_score']}"
                                )
                            ],
                        )
                    )
                elif function_response.name == "get_bq_data":
                    if result["total_student_score"] is not None:
                        return LlmResponse(
                            content=types.Content(
                                role="model",
                                parts=[
                                    types.Part(
                                        text=f"Je hebt een score van {result['total_student_score']}/{result['total_max_score']} ({int(result['total_percentage'])}%). Wil je nog een vraag?"
                                    )
                                ],
                            )
                        )
                    else:
                        return LlmResponse(
                            content=types.Content(
                                role="model",
                                parts=[
                                    types.Part(
                                        text="U hebt in deze sessie nog geen vragen beantwoord. Wil je een vraag beantwoorden?"
                                    )
                                ],
                            )
                        )
    return None


def before_tool_callback(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> dict | None:
    # Was added for testing an issue, but didn't happen anymore
    # if "agent" in tool.name:
    #     print(tool.name)
    #     print(args)
    return None
