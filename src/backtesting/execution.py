"""
Execution model (RESEARCH_SPEC.md section 18: "Do not assume signal at
close -> perfect fill at close unless explicitly the tested execution
assumption. Document whichever model is used.").

Two models:
  - NEXT_OPEN (default): a decision available using day t's data (target
    allocation computed from features/regime known by t's close) fills
    at day t+1's OPEN price. This is the realistic default -- you cannot
    trade on information before it exists, and you cannot fill at a
    price that already reflects the day's full range.
  - SAME_CLOSE: fills at day t's own close, immediately. Kept only as an
    explicitly-labeled UNREALISTIC comparison point (section 18's own
    example of what NOT to assume by default) -- never the default.
"""

from __future__ import annotations

from enum import Enum


class ExecutionModel(str, Enum):
    NEXT_OPEN = "next_open"
    SAME_CLOSE = "same_close"  # unrealistic; comparison-only, see module docstring


DEFAULT_EXECUTION_MODEL = ExecutionModel.NEXT_OPEN
