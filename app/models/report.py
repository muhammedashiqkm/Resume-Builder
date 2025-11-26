from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict

#snake_case to camel_case
def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))

class BasePortfolioModel(BaseModel):
    """Base config to handle CamelCase JSON <-> snake_case Python"""
    model_config = ConfigDict(
        alias_generator=None, 
        populate_by_name=True
    )

class AssessmentResponse(BasePortfolioModel):
    question: str
    selected_option: str = Field(..., alias="selected_option")

class PsychometricSection(BasePortfolioModel):
    section: str
    student_score: Optional[float] = None
    total_mark: Optional[float] = None
    responses: Optional[List[AssessmentResponse]] = None

class PsychometricCategory(BasePortfolioModel):
    category: str
    result_type: str
    sections: List[PsychometricSection]

class ProjectInternshipCertDetail(BasePortfolioModel):
    type: Literal["Project", "Internship", "Certificate"] = Field(..., alias="Type")
    sub_type: Optional[str] = Field(None, alias="SubType")
    title: str = Field(..., alias="Title")
    description: str = Field(..., alias="Description")
    organization: Optional[str] = Field(None, alias="Organization")
    from_date: str = Field(..., alias="FromDate")
    to_date: str = Field(..., alias="ToDate")

class MajorPaper(BasePortfolioModel):
    paper_name: str = Field(..., alias="PaperName")

class CourseOutcome(BasePortfolioModel):
    course_outcome: str = Field(..., alias="CourseOutCome")

class ClubDetail(BasePortfolioModel):
    club: str = Field(..., alias="Club")

class AbilityDetail(BasePortfolioModel):
    ability: str = Field(..., alias="Ability")
    value: int = Field(..., alias="Value")

class AchievementDetail(BasePortfolioModel):
    achievement_item: str = Field(..., alias="AchievementItem")
    remarks: str = Field(..., alias="Remarks")

class ActivityDetail(BasePortfolioModel):
    activity: str = Field(..., alias="Activity")

class StudentPortfolioInput(BasePortfolioModel):
    model: Literal["openai", "gemini", "deepseek"] = "gemini"
    
    # Python Variables (snake_case)      # JSON Keys (CamelCase)
    student_name: str                  = Field(..., alias="StudentName")
    course_name: str                   = Field(..., alias="CourseName")
    institution_name: str              = Field(..., alias="InstitutionName")
    email: str                         = Field(..., alias="Email")
    batch: str                         = Field(..., alias="Batch")
    cgpa: Optional[str]                = Field(None, alias="CGPA")
    
    # Nested Lists
    details_list: List[ProjectInternshipCertDetail] = Field(..., alias="StudentProjectInternshipCertificationDetailsForPortfolio")
    major_papers: List[MajorPaper]                  = Field(..., alias="StudentMajorCourseDetailsForPortfolioData")
    po_details: List[CourseOutcome]                 = Field(..., alias="StudentPODetailsForPortfolioData")
    club_details: List[ClubDetail]                  = Field(..., alias="StudentClubDetailsForPortfolioData")
    ability_details: List[AbilityDetail]            = Field(..., alias="StudentAbilityDetailsForPortfolioData")
    achievement_details: List[AchievementDetail]    = Field(..., alias="StudentAchievementDetailsForPortfolioData")
    activity_details: List[ActivityDetail]          = Field(..., alias="StudentActivityDetailsForPortfolioData")
    psychometric_details: List[PsychometricCategory]= Field(..., alias="StudentPsychometricDetailsForPortfolioData")

class AIContentOutput(BaseModel):
    career_objective: str
    portfolio_summary: str
    course_outcomes_sentence: str
    skills_grouped: Dict[str, List[str]]
    achievements_activities_formatted: List[str]
    psychometric_table_rows: List[Dict[str, str]]

class ReportURLResponse(BaseModel):
    filename: str
    report_url: str