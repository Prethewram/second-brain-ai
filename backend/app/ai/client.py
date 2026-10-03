from google import genai

from app.core.config import settings


class AIClient:

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def chat(self, messages):

        prompt = ""

        for message in messages:
            prompt += f"{message['role']}: {message['content']}\n"

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        return response.text
