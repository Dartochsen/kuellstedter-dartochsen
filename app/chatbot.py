import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_chatbot_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Du bist ein hilfreicher Assistent für den Dartverein Küllstedter Dartochsen."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message['content']
