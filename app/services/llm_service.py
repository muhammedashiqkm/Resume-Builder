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
    # Context Preparation
    projects = [f"{p.Title}: {p.Description}" for p in data.StudentProjectInternshipCertificationDetailsForPortfolio if p.Type == 'Project']
    abilities = [f"{a.Ability} (Value: {a.Value})" for a in data.StudentAbilityDetailsForPortfolioData]
    outcomes = [po.CourseOutCome for po in data.StudentPODetailsForPortfolioData]
    
    # Combine Achievements & Activities for the list generation
    achievements = [f"Achievement: {a.AchievementItem}, Level: {a.AchievementLevel}, Remarks: {a.Remarks}" for a in data.StudentAchievementDetailsForPortfolioData]
    activities = [f"Activity: {act.Activity}" for act in data.StudentActivityDetailsForPortfolioData]
    combined_activities = achievements + activities

    psychometric_cats = [cat.category for cat in data.StudentPsychometricDetailsForPortfolioData]

    schema = """
    {
      "career_objective": "string (First-person, ~40 words)",
      "portfolio_summary": "string (Third-person, ~60 words)",
      "course_outcomes_sentence": "string (A single sentence starting with 'Demonstrated proficiency in...', listing the outcomes. Ensure the last item is preceded by 'and'.)",
      "skills_grouped": {
          "Category Name": ["skill1", "skill2"]
      } (Categorize the 'StudentAbilityDetails' and extracted skills from 'Projects'. e.g., 'Technical Skills', 'Soft Skills', 'Tools'),
      "achievements_activities_formatted": [
          "string (e.g. 'Winner, National ERP Hackathon 2024 built an AI module...')", 
          "string (e.g. 'Attended Workshop on AI in Education Systems - IIT Delhi')"
      ] (Generate impressive one-line bullet points from the achievements/activities list),
      "psychometric_table_rows": [
        {
            "category": "string (The category name from input)",
            "description": "string (What this category measures)",
            "representation": "string (How to represent it, e.g. 'Radar chart showing Openness, ...')"
        }
      ]
    }
    """

    prompt = f"""
    You are a professional Resume Writer. Transform the student's data into an ATS-friendly portfolio structure.

    **Student Data:**
    - Name: {data.StudentName}
    - Course Outcomes: {'; '.join(outcomes)}
    - Abilities & Projects: {'; '.join(abilities + projects)}
    - Achievements/Activities: {'; '.join(combined_activities)}
    - Psychometric Categories Available: {', '.join(psychometric_cats)}

    **Specific Instructions:**
    1. **Course Outcomes:** Combine the list into one fluent sentence using an Oxford comma (e.g., "A, B, and C").
    2. **Skills:** Use the 'StudentAbilityDetails' as the primary source, but also extract hard skills from Project descriptions. Group them logically.
    3. **Psychometric Table:** For each category listed in the input, explain what it is (Description) and suggest a visualization (Representation).

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
        # Fallback
        return AIContentOutput(
            career_objective="Seeking opportunities.",
            portfolio_summary="Dedicated student.",
            course_outcomes_sentence="Demonstrated proficiency in core academic subjects.",
            skills_grouped={"General": ["Communication", "Teamwork"]},
            achievements_activities_formatted=["Participated in academic events."],
            psychometric_table_rows=[]
        )