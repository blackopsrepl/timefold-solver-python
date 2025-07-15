from pydantic import BaseModel
from typing import List, Any, Annotated
from timefold.solver.score import HardMediumSoftScore
from .domain import ScoreSerializer

class MatchAnalysisDTO(BaseModel):
    name: str
    score: Annotated[HardMediumSoftScore, ScoreSerializer]
    justification: Any

class ConstraintAnalysisDTO(BaseModel):
    name: str
    weight: Annotated[HardMediumSoftScore, ScoreSerializer]
    score: Annotated[HardMediumSoftScore, ScoreSerializer]
    matches: List[MatchAnalysisDTO]