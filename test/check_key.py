import os
import openai

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    print("❌ OPENAI_API_KEY is not set in environment variables.")
else:
    print(f"✅ OPENAI_API_KEY is set (starts with {api_key[:8]}...)")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        client.models.list()
        print("✅ API Key is valid (successfully listed models).")
    except Exception as e:
        print(f"❌ API Key validation failed: {e}")
