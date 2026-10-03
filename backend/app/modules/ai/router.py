from fastapi import APIRouter, Depends

from app.ai.schemas.actions import AnalysisResult
from app.modules.auth.dependencies import get_current_user
from app.modules.ai.schemas import AnalyzeRequest
from app.services.ai.analyzer import AIAnalyzer

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest):

    analyzer = AIAnalyzer()

    result = analyzer.analyze(request.message)

    return result
