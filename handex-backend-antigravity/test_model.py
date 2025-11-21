import openai
import os

api_key = "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"

client = openai.OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": "Hello"}],
        max_completion_tokens=10
    )
    print("Success! Model exists.")
except Exception as e:
    print(f"Error: {e}")
