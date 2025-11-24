# app/models/report.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

# --- Helper Models (Unchanged) ---
class PODetail(BaseModel):
    CONumber: str
    CourseOutCome: str

class MajorCourseDetail(BaseModel):
    PaperName: str
    PaperCode: str

class AchievementDetail(BaseModel):
    AchievementItem: str
    AchievementLevel: str
    AchievementDate: str
    Remarks: str
    AcademicYear: str

class AbilityDetail(BaseModel):
    Ability: str
    Value: int

class ClubDetail(BaseModel):
    Club: str

class ActivityDetail(BaseModel):
    Activity: str
    ActivityDate: str
    AcademicYear: str

class ProjectInternshipCertDetail(BaseModel):
    Type: Literal["Project", "Internship", "Certificate"]
    SubType: Optional[str] = None
    Title: str
    Description: str
    SubmittedOn: Optional[str] = None
    Organization: str
    Year: int
    FromDate: str
    ToDate: str

# --- Psychometric Input Models ---
class PsychometricSection(BaseModel):
    section: str
    total_mark: Optional[int] = None
    student_score: Optional[int] = None
    responses: Optional[List[dict]] = None 

class PsychometricCategory(BaseModel):
    category: str
    result_type: Literal["marks", "subjective"]
    sections: List[PsychometricSection]

# --- Main Request Model ---
class StudentPortfolioInput(BaseModel):
    model: Literal["openai", "gemini", "deepseek"] = "gemini"
    StudentName: str
    CourseName: str
    InstitutionName: str
    Email: str
    Batch: str
    CGPA: str
    CourseID: int
    
    StudentPODetailsForPortfolioData: List[PODetail]
    StudentMajorCourseDetailsForPortfolioData: List[MajorCourseDetail]
    StudentAchievementDetailsForPortfolioData: List[AchievementDetail]
    StudentAbilityDetailsForPortfolioData: List[AbilityDetail]
    StudentClubDetailsForPortfolioData: List[ClubDetail]
    StudentActivityDetailsForPortfolioData: List[ActivityDetail]
    StudentProjectInternshipCertificationDetailsForPortfolio: List[ProjectInternshipCertDetail]
    StudentPsychometricDetailsForPortfolioData: List[PsychometricCategory]

# --- UPDATED AI Output Models ---

class PsychometricRowAI(BaseModel):
    category: str
    description: str
    representation: str

class AIContentOutput(BaseModel):
    career_objective: str
    portfolio_summary: str
    
    # Formatted sentence: "Demonstrated proficiency in X, Y, and Z."
    course_outcomes_sentence: str 
    
    # Dynamic Dictionary: {"Technical Skills": ["C#", "Python"], "Soft Skills": ["Leadership"]}
    skills_grouped: Dict[str, List[str]] 
    
    # Formatted bullet points for achievements
    achievements_activities_formatted: List[str] 
    
    # Data for the 3-column table
    psychometric_table_rows: List[PsychometricRowAI]

class ReportURLResponse(BaseModel):
    filename: str
    report_url: str