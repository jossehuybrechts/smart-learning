from google.adk.agents import Agent

from app.instructions import question_eval_agent_instructions


def create_question_eval_agent(llm, tools):
    return Agent(
        model=llm,
        name="question_eval_agent",
        description="Evaluates a user's answer to a question based on retrieved knowledge.",
        instruction=question_eval_agent_instructions,
        tools=tools,
    )
