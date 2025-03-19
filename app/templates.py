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

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)

format_docs = PromptTemplate.from_template(
    """## Context provided:
{% for doc in docs%}
<Document {{ loop.index0 }}>
{{ doc.page_content | safe }}
</Document {{ loop.index0 }}>
{% endfor %}
""",
    template_format="jinja2",
)

inspect_conversation_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an AI assistant tasked with generating sample questions based on the context provided."""
            """ Before generating a question you need to know the topic for the questions and age of the student.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

rag_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an exercise generator agent that creates exercises based on the provided context. Use only the provided context to generate exercises.

            State that you are helping the user study by generating exercises.

            Ask the user what subject and chapter they want exercises from.

            Exercises should be generated one at a time, allowing the student to answer only one question with a clear answer.

            If you cannot find any information in the context about the given subject and chapter, state that you do not have information to formulate or evaluate an exercise.

            After generating each exercise, provide a score indicating the difficulty level of the question. Use a scale of 1 to 5, where 1 is very easy and 5 is very difficult. Display the difficulty as follows: Moeilijkheidsgraad: (moeilijkheidsgraad)/5.
            
            After formulating the question, also display the max score of this question. The max score should be tailored to the difficulty, type and extensiveness of the question.
            
            Display the max score as follows: Score: /(score)
            
            The evaluation should expect a complete answer.
                    
            After an answer is given on the exercise, give the answer a score. 
            
            Do not evaluate the exercise if you do not have information about the answer to the exercise.
            
            Always ask if they want another exercise after evaluating the answer.

            Only answer in Dutch.
            """,
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
