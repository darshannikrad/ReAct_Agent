import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not set.")

client = Groq(api_key=api_key)

MODEL_NAME = "llama-3.3-70b-versatile"

def generate(prompt: str):
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    text = completion.choices[0].message.content
    tokens = 0
    if hasattr(completion, "usage") and completion.usage:
        tokens = completion.usage.total_tokens
    return text, tokens