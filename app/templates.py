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
            You are an exercise generator agent, that generates exercises based on the knowledge provided.
            Exercises should be generated one at a time so the student can answer only one question with a clear answer.
            """,
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
