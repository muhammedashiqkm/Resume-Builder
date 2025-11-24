# app/services/llm_service.py
import json
from openai import AsyncOpenAI
import google.generativeai as genai
from app.core.config import settings
from app.models.report import StudentPortfolioInput, AIContentOutput
from app.core.logging_config import app_logger, error_logger

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
deepseek_client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

def get_portfolio_prompt(data: StudentPortfolioInput) -> str:
    # --- 1. Extract ALL Data (Previously some were missing) ---
    
    # Separate Projects, Internships, and Certs
    projects = []
    internships = []
    certs = []
    for item in data.StudentProjectInternshipCertificationDetailsForPortfolio:
        entry = f"{item.Title} ({item.Organization}): {item.Description}"
        if item.Type == 'Project':
            projects.append(entry)
        elif item.Type == 'Internship':
            internships.append(entry)
        elif item.Type == 'Certificate':
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
                # Summarize subjective responses for the AI
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
          "Category Name": ["skill1", "skill2"]
      } (Categorize the 'Abilities' and extract hard tools/skills from 'Projects', 'Internships' and 'Major Papers'. e.g., 'Technical', 'Soft Skills', 'Domain Knowledge'),
      "achievements_activities_formatted": [
          "string"
      ] (Generate impressive bullet points from Achievements, Activities, and Clubs),
      "psychometric_table_rows": [
        {
            "category": "string (The category name from input)",
            "description": "string (What this category measures based on the specific questions/scores provided)",
            "representation": "string (Suggest a visualization)"
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
    2. **Skills:** Extract "Domain Knowledge" (e.g., Journalism, History) from the *Major Papers* list.
    3. **Psychometric Table:** Use the actual scores/answers provided in the context to write a specific description for the table rows.

    **Output strictly JSON:**
    {schema}
    """
    return prompt

async def generate_ai_content(student_data: StudentPortfolioInput) -> AIContentOutput:
    prompt = get_portfolio_prompt(student_data)
    model_name = student_data.model
    
    try:
        response_content = ""
        if model_name == "gemini":
            response = await gemini_model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
            response_content = response.text.strip().removeprefix("```json").removesuffix("```")
        elif model_name == "openai":
             response = await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}], 
                response_format={"type": "json_object"}
            )
             response_content = response.choices[0].message.content
        
        return AIContentOutput(**json.loads(response_content))
    except Exception as e:
        error_logger.error(f"AI Generation failed: {e}")
        return AIContentOutput(
            career_objective="Seeking opportunities to leverage my skills.",
            portfolio_summary="Dedicated student with a strong academic background.",
            course_outcomes_sentence="Demonstrated proficiency in core academic subjects.",
            skills_grouped={"General": ["Communication", "Teamwork"]},
            achievements_activities_formatted=["Participated in various academic events."],
            psychometric_table_rows=[]
        )