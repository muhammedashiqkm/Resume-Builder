import json
from openai import AsyncOpenAI
import google.generativeai as genai

from app.core.config import settings
from app.models.report import StudentPortfolioInput, AIContentOutput
from app.core.logging_config import app_logger, error_logger
from app.core.utils import format_date_str

# --- Client Initializations ---
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
deepseek_client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

def get_portfolio_prompt(data: StudentPortfolioInput) -> str:
    # --- 1. Extract & Format Data ---
    # We use snake_case accessors here (data.details_list) because the Pydantic model 
    # parses the CamelCase JSON into snake_case Python variables.
    
    projects = []
    internships = []
    certs = []
    
    for item in data.details_list:
        start = format_date_str(item.from_date)
        end = format_date_str(item.to_date)
        date_str = f"{start} - {end}" if start and end else ""
        
        if item.type == 'Project':
            subtype = f" ({item.sub_type})" if item.sub_type and item.sub_type.lower() != "none" else ""
            title = f"{item.title}{subtype}"
            entry = f"{title}: {item.description}"
            projects.append(entry)
            
        elif item.type == 'Internship':
            entry = f"{item.title} at {item.organization} ({date_str}): {item.description}"
            internships.append(entry)
            
        elif item.type == 'Certificate':
            entry = f"{item.title} by {item.organization}"
            certs.append(entry)

    # Academic Details
    major_papers = [subject.paper_name for subject in data.major_papers]
    outcomes = [po.course_outcome for po in data.po_details]
    
    # Activities & Engagement
    clubs = [c.club for c in data.club_details]
    abilities = [f"{a.ability} (Self-Rating: {a.value}%)" for a in data.ability_details]
    
    # Achievements
    achievements = [f"Achievement: {a.achievement_item} ({a.remarks})" for a in data.achievement_details]
    activities = [f"Activity: {act.activity}" for act in data.activity_details]
    
    # Psychometric Context
    psychometric_context = []
    for cat in data.psychometric_details:
        details = []
        for sec in cat.sections:
            if cat.result_type == 'marks':
                details.append(f"{sec.section}: {sec.student_score}/{sec.total_mark}")
            elif sec.responses:
                q_a = [f"Q:{r.question}->A:{r.selected_option}" for r in sec.responses]
                details.append(f"{sec.section} Answers: {'; '.join(q_a)}")
        psychometric_context.append(f"Category {cat.category}: {', '.join(details)}")

    # --- 2. Construct the Schema ---
    schema = """
    {
      "career_objective": "string (3–4 lines, crisp and personalized. Reflect Major Papers + Projects + Internships + Certifications.)",
      "portfolio_summary": "string (5–7 lines, holistic. Summarize academics, projects, internships, abilities, and activities.)",
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
    - Name: {data.student_name} ({data.course_name})
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
    1. **CAREER OBJECTIVE:**
       • 3–4 lines, crisp and personalized.
       • Must reflect Major Papers + Projects + Internships + Certifications.
       • Tone: professional, confident, future-oriented.
       • Avoid generic phrases (“seeking opportunity”, “to work in a company”).
       • Clearly state the student's direction + strengths + value they bring.

    2. **PORTFOLIO SUMMARY:**
       • 5–7 lines, holistic and clear.
       • Summarize academics, projects, internships, abilities, certificates, and activities.
       • Highlight both technical and soft skills with brief examples.
       • Avoid repeating the Career Objective wording.
       • End with a short line showing readiness for industry roles.

    3. **SKILLS:**
       Analyze the student's data (Major Papers, Projects, Internships, Abilities, Certificates)
       and group detected skills into meaningful categories chosen by you (the LLM).
       • Decide which category each skill belongs to (do not use a fixed list).
       • Keep category names short (e.g., "Technical", "Domain Knowledge", "Tools", "Soft Skills").
       • Put each skill under the most appropriate category. Avoid duplicates.

    4. **PSYCHOMETRIC TABLE:**
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
        return AIContentOutput(
            career_objective="Seeking opportunities to leverage my skills.",
            portfolio_summary="Dedicated student with a strong academic background.",
            course_outcomes_sentence="Demonstrated proficiency in core academic subjects.",
            skills_grouped={"General": ["Communication", "Teamwork"]},
            achievements_activities_formatted=["Participated in various academic events."],
            psychometric_table_rows=[]
        )