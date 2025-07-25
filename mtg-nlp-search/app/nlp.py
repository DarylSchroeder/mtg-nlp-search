import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_filters(prompt: str) -> dict:
    system_prompt = "Extract Magic: The Gathering search filters from natural language."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2
    )

    try:
        return eval(response.choices[0].message.content)
    except Exception:
        return {"raw_query": prompt}