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

# mypy: disable-error-code="assignment"

import vertexai
from vertexai.generative_models import GenerativeModel


def get_title(project: str, location: str, llm: str, messages) -> str:
    vertexai.init(project=project, location=location)
    model = GenerativeModel(model_name=llm)

    response = model.generate_content(f"""Given a list of messages between a human and AI, come up with a short and relevant title for the conversation. Use up to 10 words. The title needs to be concise.
Examples:
**Input:**
```
Human: hi, what is the best italian dish?
AI: That's a tough one! Italy has so many amazing dishes, it's hard to pick just one "best." To help me give you a great suggestion, tell me a little more about what you're looking for.
```
**Output:** Best italian dish

**Input:**

```
Human: How to fix a broken laptop screen?
AI: Fixing a broken laptop screen can be tricky and often requires professional help. However, there are a few things you can try at home before resorting to a repair shop.
```

**Output:** Fixing a broken laptop screen

**Input:**

```
Human: Can you write me a poem about the beach?
AI: As the sun dips down below the horizon
And the waves gently kiss the shore,
I sit here and watch the ocean
And feel its power evermore.
```

**Output:** Poem about the beach

**Input:**

```
Human: What's the best way to learn to code?
AI: There are many ways to learn to code, and the best method for you will depend on your learning style and goals.
```

**Output:** How to learn to code

If there's not enough context in the conversation to create a meaningful title, create a generic title like "New Conversation", or "A simple greeting".


** Chat History: **
{messages}
""")
    return response
