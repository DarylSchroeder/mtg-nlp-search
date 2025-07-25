from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_filters(prompt: str) -> dict:
    system_prompt = """Extract Magic: The Gathering search filters from natural language.
    Return a JSON object with relevant filters like:
    - "cmc": converted mana cost (number)
    - "type": card type (e.g., "instant", "creature", "artifact")
    - "effects": list of effects to search for in oracle text
    
    Example: {"cmc": 2, "type": "instant", "effects": ["counter", "token"]}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2
        )
        
        # Try to parse as JSON instead of using eval
        content = response.choices[0].message.content
        return json.loads(content)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing OpenAI response: {e}")
        return {"raw_query": prompt}