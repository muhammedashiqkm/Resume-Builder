# app/services/llm_service.py
import json
from openai import AsyncOpenAI
import google.generativeai as genai

from app.core.config import settings
from app.models.report import StudentReportInput, AIReportOutput
from app.core.logging_config import app_logger, error_logger

# --- Client Initializations ---
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
deepseek_client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

def get_report_prompt(student_data: StudentReportInput) -> str:
    """Creates a sophisticated prompt to guide the AI in generating a detailed student analysis report."""
    data_dict = student_data.model_dump()

    # --- UPDATED: Smarter formatting for the new self_assessment structure ---
    assessment_lines = []
    for category in data_dict.get("self_assessment", []):
        assessment_lines.append(f"\n### Category: {category['category']}")
        for section in category.get("sections", []):
            if section['result_type'] == 'marks':
                score = section.get('student_score', 'N/A')
                total = section.get('total_mark', 'N/A')
                assessment_lines.append(f"- {section['section']}: Scored {score} out of {total}")
            elif section['result_type'] == 'subjective':
                assessment_lines.append(f"- {section['section']}:")
                for response in section.get("responses", []):
                    question = response.get('question', 'N/A')
                    answer = response.get('selected_option', 'N/A')
                    assessment_lines.append(f"  - Q: {question}")
                    assessment_lines.append(f"    A: {answer}")
    
    self_assessment_text = "\n".join(assessment_lines)
    # --- END OF UPDATE ---

    all_marks = [subject['marks'] for semester in data_dict['semester_marks'] for subject in semester['subjects']]
    cgpa = round((sum(all_marks) / len(all_marks) / 10), 2) if all_marks else 0

    schema = """
    {
      "name": "string",
      "profile_summary": "string (A 3-4 sentence holistic summary of the student)",
      "academic_snapshot": "string (A single sentence summarizing degree, CGPA, and performance)",
      "skillset": { "summary": "string (A 1-2 sentence summary of skills)", "tags": ["string", "..."] },
      "assessment_overview": { "summary": "string (A 1-2 sentence summary of assessment findings)", "breakdown": [{ "category": "string", "interpretation": "string (AI's analysis)" }] },
      "career_recommendation": "string (Recommend 2-3 specific career paths)"
    }
    """
    prompt = f"""
    You are an expert student career analyst. Generate a comprehensive, analytical report for a student based on the data provided. You MUST generate a single, valid JSON object that strictly follows the schema. Do not add extra text or explanations.

    **JSON Schema to Follow:**
    {schema}

    **Analysis Instructions:**
    1.  **profile_summary**: Write a compelling, holistic summary combining academics, skills, and assessment insights.
    2.  **academic_snapshot**: Create a single string that includes the degree (assume 'Bachelor of Technology'), the calculated CGPA, and a brief comment on performance.
    3.  **skillset**: From the 'skillset' list, generate a short summary and also reproduce the list in the 'tags' field.
    4.  **assessment_overview**: Analyze the 'Self Assessment Data'. For each category, write a concise 'interpretation' for the 'breakdown'. Then, write an overall 'summary' of the findings.
    5.  **career_recommendation**: Based on all available data, suggest 2-3 specific and suitable career roles for the student.

    **Student Data:**
    - Name: {data_dict['name']}
    - Calculated Overall CGPA: {cgpa}
    - Skillset: {', '.join(data_dict['skillset'])}
    - Self Assessment Data:
    {self_assessment_text}
    """
    return prompt

async def _call_openai_compatible(client: AsyncOpenAI, model: str, prompt: str):
    response = await client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
    return response.choices[0].message.content

async def _call_gemini(prompt: str):
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")
    response = await gemini_model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
    return response.text.strip().removeprefix("```json").removesuffix("```")

async def generate_report_from_llm(student_data: StudentReportInput, model_name: str) -> AIReportOutput:
    """Generates an analytical report using the dynamically provided model_name."""
    prompt = get_report_prompt(student_data)
    
    app_logger.info(f"Generating AI report for {student_data.name} using model: {model_name}")
    response_content = ""
    
    try:
        if model_name == "openai":
            model_to_use = settings.OPENAI_MODEL_NAME
            response_content = await _call_openai_compatible(openai_client, model_to_use , prompt)
        elif model_name == "deepseek":
            model_to_use = settings.DEEPSEEK_MODEL_NAME
            response_content = await _call_openai_compatible(deepseek_client, model_to_use , prompt)
        elif model_name == "gemini":
            response_content = await _call_gemini(prompt)
        else:
            raise ValueError(f"Unsupported model: {model_name}")

        validated_report = AIReportOutput(**json.loads(response_content))
        app_logger.info(f"Successfully generated AI report for {student_data.name}")
        return validated_report
    except Exception as e:
        error_logger.error(f"Error with model {model_name}: {e}. Raw response: {response_content[:200]}")
        raise