# app/models/report.py

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# --- Nested models for the detailed self_assessment structure ---

class SubjectiveResponse(BaseModel):
    question: str
    selected_option: str

class Section(BaseModel):
    section: str
    result_type: str
    total_mark: Optional[int] = None
    student_score: Optional[int] = None
    responses: Optional[List[SubjectiveResponse]] = None

class SelfAssessmentCategory(BaseModel):
    category: str
    sections: List[Section]

# --- Main Input Models ---

class Subject(BaseModel):
    name: str
    marks: int

class Semester(BaseModel):
    semester: int # This is "semester", not "semester_id"
    subjects: List[Subject]

class StudentReportInput(BaseModel):
    """
    Pydantic model for the INCOMING student data, matching your exact request.
    """
    model: Literal["openai", "gemini", "deepseek"] = Field( # This is "model", not "model_provider"
        ...,
        description="The AI model provider to use for generating the report."
    )
    name: str
    semester_marks: List[Semester]
    skillset: List[str]
    self_assessment: List[SelfAssessmentCategory] # This correctly expects a List

# --- AI Output Models (These are for the AI's response) ---

class Skillset(BaseModel):
    summary: str
    tags: List[str]

class AssessmentBreakdown(BaseModel):
    category: str
    interpretation: str

class AssessmentOverview(BaseModel):
    summary: str
    breakdown: List[AssessmentBreakdown]

class AIReportOutput(BaseModel):
    name: str
    profile_summary: str
    academic_snapshot: str
    skillset: Skillset
    assessment_overview: AssessmentOverview
    career_recommendation: str