from pydantic import BaseModel
from typing import Literal

class Finding(BaseModel):
  file: str
  line: int
  severity: Literal["blocker", "suggestion", "nit"]
  category: Literal["bug", "security", "style", "performance"]
  message: str

class ReviewResult(BaseModel):
  findings: list[Finding]
  summary: str