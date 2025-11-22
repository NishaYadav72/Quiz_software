import os
import openai

# API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

try:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hi"}]
    )
    print(response.choices[0].message.content)
except openai.OpenAIError as e:
    print("OpenAI API error:", e)

