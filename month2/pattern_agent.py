import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load .env containing OPENAI_API_KEY
load_dotenv(dotenv_path=os.path.expanduser("~/openai.env"))

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple prompt instructions for pattern detection
INSTRUCTIONS = (
    "You are a trading assistant. Given the recent price action within an upper and lower channel, "
    "decide if it visually resembles a head-and-shoulders pattern. "
    "Only respond with a single word: 'yes' or 'no'."
)


def ask_agent_if_head_and_shoulders(snapshot: dict) -> bool:
    prompt = (
        f"{INSTRUCTIONS}\n\n"
        f"Here is the recent channel snapshot:\n"
        f"{json.dumps(snapshot, indent=2)}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.choices[0].message.content.strip().lower()
        print(result)
        return "yes" in result
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return False
