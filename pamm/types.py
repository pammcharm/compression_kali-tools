from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AnalysisResult:
    file_type: str
    entropy: float
    zero_block_density: float
    repetition_score: str
    already_compressed: bool
    executable_hint: bool
