import json
from datetime import datetime
from openai import AsyncOpenAI
import google.generativeai as genai

from app.core.config import settings
from app.models.report import StudentPortfolioInput, AIContentOutput
from app.core.logging_config import app_logger, error_logger

# --- Client Initializations ---
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
deepseek_client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

def format_date_for_prompt(date_str: str) -> str:
    """Helper to make dates readable for the AI (e.g., '2023-06' -> 'Jun 2023')"""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %Y")
    except ValueError:
        return date_str

def get_portfolio_prompt(data: StudentPortfolioInput) -> str:
    # --- 1. Extract & Format Data ---
    
    projects = []
    internships = []
    certs = []
    
    for item in data.StudentProjectInternshipCertificationDetailsForPortfolio:
        # Format Dates
        start = format_date_for_prompt(item.FromDate)
        end = format_date_for_prompt(item.ToDate)
        date_str = f"{start} - {end}" if start and end else ""
        
        # Build specific strings for AI context
        if item.Type == 'Project':
            # Add (Major/Minor) to title if present
            subtype = f" ({item.SubType})" if item.SubType and item.SubType.lower() != "none" else ""
            title = f"{item.Title}{subtype}"
            # Entry format: "Smart Attendance (Major): Description"
            entry = f"{title}: {item.Description}"
            projects.append(entry)
            
        elif item.Type == 'Internship':
            # Entry format: "Intern at Google (Jun 2023 - Aug 2023): Description"
            entry = f"{item.Title} at {item.Organization} ({date_str}): {item.Description}"
            internships.append(entry)
            
        elif item.Type == 'Certificate':
            entry = f"{item.Title} by {item.Organization}"
            certs.append(entry)

    # Academic Details
    major_papers = [subject.PaperName for subject in data.StudentMajorCourseDetailsForPortfolioData]
    outcomes = [po.CourseOutCome for po in data.StudentPODetailsForPortfolioData]
    
    # Activities & Engagement
    clubs = [club.Club for club in data.StudentClubDetailsForPortfolioData]
    abilities = [f"{a.Ability} (Self-Rating: {a.Value}%)" for a in data.StudentAbilityDetailsForPortfolioData]
    
    # Achievements & Activities
    achievements = [f"Achievement: {a.AchievementItem} ({a.Remarks})" for a in data.StudentAchievementDetailsForPortfolioData]
    activities = [f"Activity: {act.Activity}" for act in data.StudentActivityDetailsForPortfolioData]
    
    # Psychometric Context
    psychometric_context = []
    for cat in data.StudentPsychometricDetailsForPortfolioData:
        details = []
        for sec in cat.sections:
            if cat.result_type == 'marks':
                details.append(f"{sec.section}: {sec.student_score}/{sec.total_mark}")
            elif sec.responses:
                q_a = [f"Q:{r['question']}->A:{r['selected_option']}" for r in sec.responses]
                details.append(f"{sec.section} Answers: {'; '.join(q_a)}")
        psychometric_context.append(f"Category {cat.category}: {', '.join(details)}")

    # --- 2. Construct the Schema ---
    schema = """
    {
      "career_objective": "string (First-person, ~40 words. Tailor specifically to the Major Subjects and Internships listed.)",
      "portfolio_summary": "string (Third-person, ~60 words. A professional bio highlighting their specific skills, clubs, and academic focus.)",
      "course_outcomes_sentence": "string (A single sentence starting with 'Demonstrated proficiency in...', listing the outcomes. Ensure the last item is preceded by 'and'.)",
      "skills_grouped": {
          "<CategoryName>": ["skill1", "skill2", "..."]
      },
      "achievements_activities_formatted": [
          "string"
      ] (Generate impressive bullet points from Achievements, Activities, and Clubs),
      "psychometric_table_rows": [
        {
            "category": "string (The main category name, e.g., 'General Aptitude Test')",
            "section": "string (The specific sub-section, e.g., 'Quantitative Analysis' or 'Behavioral Assessment')",
            "description": "string (What this specific section measures based on the context)",
            "representation": "string (1–2 sentences, concise, student-specific, referencing the scores/responses)"
        }
      ]
    }
    """

    # --- 3. Construct the Prompt ---
    prompt = f"""
    You are a professional Resume Writer. Analyze the COMPLETE student profile below to generate a high-impact portfolio.

    **Student Profile:**
    - Name: {data.StudentName} ({data.CourseName})
    - Major Papers Studied: {', '.join(major_papers)}
    - Internships: {'; '.join(internships)}
    - Projects: {'; '.join(projects)}
    - Certifications: {'; '.join(certs)}
    - Active Clubs: {', '.join(clubs)}
    - Achievements/Activities: {'; '.join(achievements + activities)}
    - Key Course Outcomes: {'; '.join(outcomes)}
    - Self-Reported Abilities: {', '.join(abilities)}
    - Psychometric/Aptitude Results: {' | '.join(psychometric_context)}

    **Instructions:**
    1. **Career Objective:** Must reflect the mix of their *Major Papers* (e.g., History/Media) AND their *Internship* experience.
    2. **Skills:**
    Analyze the student's data (Major Papers, Projects, Internships, Abilities, Certificates)
    and group detected skills into meaningful categories chosen by you (the LLM).
    • Decide which category each skill belongs to (do not use a fixed list).
    • Keep category names short (e.g., "Technical", "Domain Knowledge", "Tools", "Soft Skills").
    • Put each skill under the most appropriate category. Avoid duplicates.
    3. **Psychometric Table:**
    For each psychometric section found in the data, generate one row.
    • **Category:** Use the high-level group name provided (e.g., "General Aptitude Test").
    • **Section:** Use the specific section/sub-test name (e.g., "Quantitative Analysis", "Logical Reasoning").
    • **Description:** Briefly explain what this specific section measures.
    • **Representation:** 1–2 concise sentences quoting the specific score or summarizing the response pattern.
    • Keep the wording simple, clear, and easy to read.

    **Output strictly JSON:**
    {schema}
    """
    return prompt

async def generate_ai_content(student_data: StudentPortfolioInput) -> AIContentOutput:
    prompt = get_portfolio_prompt(student_data)
    model_name = student_data.model
    
    app_logger.info(f"Generating AI content for {student_data.StudentName} using {model_name}")

    try:
        response_content = ""
        if model_name == "gemini":
            if not settings.GEMINI_API_KEY:
                 raise ValueError("GEMINI_API_KEY not found")
            response = await gemini_model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
            response_content = response.text.strip().removeprefix("```json").removesuffix("```")
        elif model_name == "openai":
             response = await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}], 
                response_format={"type": "json_object"}
            )
             response_content = response.choices[0].message.content
        elif model_name == "deepseek":
             response = await deepseek_client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}], 
                response_format={"type": "json_object"}
            )
             response_content = response.choices[0].message.content
        
        return AIContentOutput(**json.loads(response_content))
    except Exception as e:
        error_logger.error(f"AI Generation failed: {e}")
        # Fallback to prevent PDF crash
        return AIContentOutput(
            career_objective="Seeking opportunities to leverage my skills.",
            portfolio_summary="Dedicated student with a strong academic background.",
            course_outcomes_sentence="Demonstrated proficiency in core academic subjects.",
            skills_grouped={"General": ["Communication", "Teamwork"]},
            achievements_activities_formatted=["Participated in various academic events."],
            psychometric_table_rows=[]
        )