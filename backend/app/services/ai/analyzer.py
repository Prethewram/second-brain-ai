import json

from app.ai.client import AIClient
from app.ai.prompts.analyzer import ANALYZER_PROMPT
from app.ai.schemas.actions import AnalysisResult
from app.services.ai.constants import SUPPORTED_ACTIONS


class AIAnalyzer:

    def __init__(self):

        self.ai = AIClient()

    def analyze(
        self,
        message: str,
    ) -> AnalysisResult:

        prompt = [
            {
                "role": "system",
                "content": ANALYZER_PROMPT,
            },
            {
                "role": "user",
                "content": message,
            },
        ]

        response = self.ai.chat(prompt)

        try:

            data = json.loads(response)

            analysis = AnalysisResult.model_validate(data)

            # Keep only supported actions
            analysis.actions = [
                action
                for action in analysis.actions
                if action.type in SUPPORTED_ACTIONS
            ]

            return analysis

        except Exception:

            return AnalysisResult(
                actions=[],
                reply={
                    "text": response,
                },
            )
