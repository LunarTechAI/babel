import os
import openai
from tenacity import retry, stop_after_attempt, wait_fixed

# Mocking the Translator class behavior for the prompt
class MockTranslator:
    def __init__(self, lang_out="Dutch"):
        self.lang_out = lang_out

    def prompt(self, text):
        return [
            {
                "role": "system",
                "content": "You are a professional,authentic machine translation engine.",
            },
            {
                "role": "user",
                "content": f";; Treat next line as plain text input and translate it into {self.lang_out}, output translation ONLY. If translation is unnecessary (e.g. proper nouns, codes, {{1}}, etc. ), return the original text. NO explanations. NO notes. Input:\n\n{text}",
            },
        ]

api_key = os.environ.get("OPENAI_API_KEY")
# Fallback if env var is not set in this context (it should be if we use uv run)
if not api_key:
    print("Error: OPENAI_API_KEY not found.")
    exit(1)

client = openai.OpenAI(api_key=api_key)
translator = MockTranslator(lang_out="Dutch")
text_to_translate = "We have introduced a novel class of adversarial failures resulting from the physical process of failures in the camera. In this paper, we provide an approach to generate a realistic broken glass pattern from a physical simulation and subsequently embed that to existing image datasets using physically based rendering."

print(f"Translating: '{text_to_translate}' to Dutch using gpt-5-mini-2025-08-07")

try:
    # Using the fixed parameter logic we added
    response = client.chat.completions.create(
        model="gpt-5-nano-2025-08-07",
        messages=translator.prompt(text_to_translate),
        max_completion_tokens=16384
    )
    result = response.choices[0].message.content.strip()
    print(f"\nResult length: {len(result)}")
    print(f"Token usage: {response.usage}")
    print(f"\nResult:\n{result}")
    
    if result == text_to_translate:
        print("\nFAILURE: Model returned original text!")
    else:
        print("\nSUCCESS: Model translated the text.")

except Exception as e:
    print(f"\nError: {e}")
