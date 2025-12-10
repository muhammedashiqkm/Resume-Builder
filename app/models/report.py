from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict

class BasePortfolioModel(BaseModel):
    """Base config to handle CamelCase JSON <-> snake_case Python"""
    model_config = ConfigDict(
        alias_generator=None, 
        populate_by_name=True
    )

class DriveData(BasePortfolioModel):
    company_name: str = Field(..., alias="CompanyName")
    job_name: str = Field(..., alias="JobName")
    designation: str = Field(..., alias="Designation")

class PsychometricCategoryWrapper(BaseModel):
    category: str = Field(..., alias="PsychometricTestCategory")
    json_result: str = Field(..., alias="JsonResult")
    
class ProjectDetail(BasePortfolioModel):
    type: Literal["Project"] = Field(default="Project", alias="Type")
    sub_type: Optional[str] = Field(None, alias="SubType")
    title: str = Field(..., alias="Title")
    description: str = Field(..., alias="Description")
    organization: Optional[str] = Field(None, alias="Organization")
    from_date: str = Field(..., alias="FromDate")
    to_date: str = Field(..., alias="ToDate")
    submitted_on: Optional[str] = Field(None, alias="SubmittedOn")
    year: Optional[int] = Field(None, alias="Year")

class InternshipDetail(BasePortfolioModel):
    type: Literal["Internship"] = Field(default="Internship", alias="Type")
    sub_type: Optional[str] = Field(None, alias="SubType")
    title: str = Field(..., alias="Title")
    description: str = Field(..., alias="Description")
    organization: Optional[str] = Field(None, alias="Organization")
    from_date: str = Field(..., alias="FromDate")
    to_date: str = Field(..., alias="ToDate")
    submitted_on: Optional[str] = Field(None, alias="SubmittedOn")
    year: Optional[int] = Field(None, alias="Year")

class CertificationDetail(BasePortfolioModel):
    type: Literal["Certification"] = Field(default="Certification", alias="Type")
    sub_type: Optional[str] = Field(None, alias="SubType")
    title: str = Field(..., alias="Title")
    description: str = Field(..., alias="Description")
    organization: Optional[str] = Field(None, alias="Organization")
    from_date: str = Field(..., alias="FromDate")
    to_date: str = Field(..., alias="ToDate")
    submitted_on: Optional[str] = Field(None, alias="SubmittedOn")
    year: Optional[int] = Field(None, alias="Year")

class MajorPaper(BasePortfolioModel):
    paper_name: str = Field(..., alias="PaperName")
    paper_code: Optional[str] = Field(None, alias="PaperCode")

class CourseOutcome(BasePortfolioModel):
    course_outcome: str = Field(..., alias="CourseOutCome")
    co_number: Optional[str] = Field(None, alias="CONumber")

class ClubDetail(BasePortfolioModel):
    club: str = Field(..., alias="Club")

class AbilityDetail(BasePortfolioModel):
    ability: str = Field(..., alias="Ability")
    value: int = Field(..., alias="Value")

class AchievementDetail(BasePortfolioModel):
    achievement_item: str = Field(..., alias="AchievementItem")
    achievement_level: str = Field(..., alias="AchievementLevel")
    achievement_date: str = Field(..., alias="AchievementDate")
    remarks: str = Field(..., alias="Remarks")
    academic_year: Optional[str] = Field(None, alias="AcademicYear")

class ActivityDetail(BasePortfolioModel):
    activity: str = Field(..., alias="Activity")
    activity_date: str = Field(..., alias="ActivityDate")
    academic_year: Optional[str] = Field(None, alias="AcademicYear")

class StudentPortfolioInput(BasePortfolioModel):
    model: Literal["openai", "gemini", "deepseek"] = "gemini"

    student_name: str     = Field(..., alias="StudentName")
    course_name: Optional[str]      = Field(..., alias="CourseName")
    institution_name: Optional[str] = Field(..., alias="InstitutionName")
    email: Optional[str]           = Field(..., alias="Email")
    batch: Optional[str]            = Field(..., alias="Batch")
    cgpa: Optional[str]   = Field(None, alias="CGPA")
    course_id: Optional[int] = Field(None, alias="CourseID") 
    year_back_count: Optional[int] = Field(None, alias="YearBackCount")

    projects: List[ProjectDetail] = Field(default=[], alias="StudentProjectDetailsForPortfolioData")
    internships: List[InternshipDetail] = Field(default=[], alias="StudentInternshipDetailsForPortfolioData")
    certifications: List[CertificationDetail] = Field(default=[], alias="StudentCertificationDetailsForPortfolioData")

    major_papers: List[MajorPaper]                  = Field(default=[], alias="StudentMajorCourseDetailsForPortfolioData")
    po_details: List[CourseOutcome]                 = Field(default=[], alias="StudentPODetailsForPortfolioData")
    club_details: List[ClubDetail]                  = Field(default=[], alias="StudentClubDetailsForPortfolioData")
    ability_details: List[AbilityDetail]            = Field(default=[], alias="StudentAbilityDetailsForPortfolioData")
    achievement_details: List[AchievementDetail]    = Field(default=[], alias="StudentAchievementDetailsForPortfolioData")
    activity_details: List[ActivityDetail]          = Field(default=[], alias="StudentActivityDetailsForPortfolioData")
    
    psychometric_details: Optional[List[PsychometricCategoryWrapper]] = Field(default=[], alias="StudentPsychometricCategoryDetailsForPortfolioData")
    
    drive_data: Optional[List[DriveData]] = Field(default=[], alias="DriveData")

class AIContentOutput(BaseModel):
    career_objective: str
    portfolio_summary: str
    course_outcomes_sentence: str
    skills_grouped: Dict[str, List[str]]
    achievements_activities_formatted: List[str]
    rating: int

class ReportURLResponse(BaseModel):
    filename: str
    report_url: str
    rating: Optional[int] = None

class PortfolioUrlRequest(BaseModel):
    model: Literal["openai", "gemini", "deepseek"] = "gemini"
    url: str = Field(..., alias="ProfileURL")
    drivedata: List[DriveData] = Field(default=[], alias="DriveData")