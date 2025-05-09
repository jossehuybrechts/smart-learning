from google.adk.agents import Agent

from app.instructions import question_generation_agent_instructions


def create_question_generation_agent(llm, tools):
    return Agent(
        model=llm,
        name="question_generation_agent",
        description="Agent to generate questions based on subject and chapter.",
        instruction=question_generation_agent_instructions,
        tools=tools,
    )
