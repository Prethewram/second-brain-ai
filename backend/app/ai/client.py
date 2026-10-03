from google import genai
from google.genai import errors
from httpx import TransportError

from app.core.config import settings
from app.common.exceptions import AIProviderException


class AIClient:

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def chat(self, messages):

        prompt = ""

        for message in messages:
            prompt += f"{message['role']}: {message['content']}\n"

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
        except errors.APIError as exc:
            if exc.code == 429:
                message = "The AI usage limit has been reached. Try again later or check your Gemini quota."
            elif exc.code == 503:
                message = "The AI model is busy right now. Please try again shortly."
            elif exc.code in (400, 401, 403, 404):
                message = "The AI provider rejected this request. Check the server's Gemini key and model configuration."
            else:
                message = "The AI provider is temporarily unavailable. Please try again later."
            raise AIProviderException(
                message, 503 if exc.code == 429 or exc.code >= 500 else 502
            ) from None
        except TransportError:
            raise AIProviderException(
                "Cannot reach the AI provider. Please try again later."
            ) from None

        if not response.text or not response.text.strip():
            raise AIProviderException(
                "The AI provider returned an empty reply. Please try again later.", 502
            )

        return response.text
