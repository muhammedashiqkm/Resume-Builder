import json
from collections import defaultdict
from openai import AsyncOpenAI
import google.generativeai as genai
from fastapi import HTTPException

from app.core.config import settings
from app.models.report import StudentPortfolioInput, AIContentOutput
from app.core.logging_config import app_logger, error_logger
from app.core.utils import format_date_str

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
deepseek_client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

def get_portfolio_prompt(data: StudentPortfolioInput) -> str:
    
    projects_str = []
    internships_str = []
    certs_str = []
    
    for item in data.projects:
        start = format_date_str(item.from_date)
        end = format_date_str(item.to_date)
        subtype = f" ({item.sub_type})" if item.sub_type and item.sub_type.lower() != "none" else ""
        title = f"{item.title}{subtype}"
        entry = f"{title}: {item.description}"
        projects_str.append(entry)

    for item in data.internships:
        start = format_date_str(item.from_date)
        end = format_date_str(item.to_date)
        date_str = f"{start} - {end}" if start and end else ""
        entry = f"{item.title} at {item.organization} ({date_str}): {item.description}"
        internships_str.append(entry)

    for item in data.certifications:
        entry = f"{item.title} by {item.organization}"
        certs_str.append(entry)

    major_papers = [subject.paper_name for subject in data.major_papers]
    outcomes = [po.course_outcome for po in data.po_details]
    
    clubs = [c.club for c in data.club_details]
    abilities = [f"{a.ability} (Self-Rating: {a.value}%)" for a in data.ability_details]
    
    achievements = [f"Achievement: {a.achievement_item} Date:{format_date_str(a.achievement_date)} Achievement:{a.achievement_level} Remark:({a.remarks})" for a in data.achievement_details]
    activities = [f"Activity: {act.activity} Date:{format_date_str(act.activity_date)}" for act in data.activity_details]

    psychometric_context = []
    grouped_psycho = defaultdict(list)
    
    if data.psychometric_details:
        for item in data.psychometric_details:
            try:
                if not item.json_result:
                    continue
                    
                result_data = json.loads(item.json_result)
                
                description = result_data.get("description", "")
                representation = result_data.get("representation", "")
                
                if description or representation:
                    details = f"Description: {description} | Representation: {representation}"
                    grouped_psycho[item.category].append(details)
            except Exception as e:
                error_logger.warning(f"Failed to parse psychometric json_result for category {item.category}: {e}")

    for category, items in grouped_psycho.items():
        psychometric_context.append(f"Category '{category}': {'; '.join(items)}")

    drive_context = "General Portfolio (No specific job targeted)"
    if data.drive_data:
        drive_entries = []
        for d in data.drive_data:
            entry = f"Company: {d.company_name}, Role: {d.designation} ({d.job_name})"
            drive_entries.append(entry)
        drive_context = "; ".join(drive_entries)

    schema = """
    {
      "career_objective": "string (3-4 lines, crisp and personalized. If a Target Job is listed, tailor this specifically to that role/company.)",
      "portfolio_summary": "string (5-7 lines, holistic. Summarize academics, projects, internships, abilities, and activities.)",
      "course_outcomes_sentence": "string (A single sentence starting with 'Demonstrated proficiency in...', listing the outcomes. Ensure the last item is preceded by 'and'.)",
      "skills_grouped": {
          "<CategoryName>": ["skill1", "skill2", "..."]
      },
      "achievements_activities_formatted": [
          "string"
      ] (Generate impressive bullet points from Achievements and Activities),

      "rating": "integer (1-5 only). A suitability score based on how well the student's overall profile matches the 'Target Job/Drive'."

    }
    """

    prompt = f"""
    You are an expert HR Recruiter and Resume Writer. Analyze the student profile and the Target Job/Drive.

    **Target Job/Drive:**
    {drive_context}

    **Student Profile:**
    - Name: {data.student_name} ({data.course_name})
    - Major Papers Studied: {', '.join(major_papers)}
    - Internships: {'; '.join(internships_str)}
    - Projects: {'; '.join(projects_str)}
    - Certifications: {'; '.join(certs_str)}
    - Active Clubs: {', '.join(clubs)}
    - Achievements/Activities: {'; '.join(achievements + activities)}
    - Key Course Outcomes: {'; '.join(outcomes)}
    - Self-Reported Abilities: {', '.join(abilities)}
    - Psychometric/Aptitude Analysis: {' || '.join(psychometric_context)}

    **Instructions:**
    1. **RATING (Crucial):** Evaluate how well the student fits the "Target Job/Drive" using the entire Student Profile.
   - Use this scale:
     - **5** - Very strong overall match.
     - **4** - Good match with minor gaps.
     - **3** - Moderate match.
     - **2** - Low match.
     - **1** - Very low match.
   - Return only an **integer**: `1`, `2`, `3`, `4`, or `5`.

    2. **CAREER OBJECTIVE:**
       • 3-4 lines, crisp and personalized.
       • **Tailor this specifically to the Target Job/Drive if provided.**

    3. **PORTFOLIO SUMMARY:**
       • 5-7 lines, holistic and clear.
       • Summarize academics, projects, internships, abilities, certificates, and activities.

    4. **SKILLS:**
       Analyze the student's data and group detected skills into meaningful categories (e.g., "Technical", "Tools", "Soft Skills").

    **Output strictly JSON:**
    {schema}
    """
    return prompt

async def generate_ai_content(student_data: StudentPortfolioInput) -> AIContentOutput:
    prompt = get_portfolio_prompt(student_data)
    model_name = student_data.model
    
    app_logger.info(f"Generating AI content for {student_data.student_name} using {model_name}")

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
        
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "LLM_PROCESSING_ERROR",
                "message": f"Failed to generate analysis using {model_name}.",
                "technical_details": str(e),
            },
        )