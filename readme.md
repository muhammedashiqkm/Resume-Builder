### **README.md**

````markdown
# Student Portfolio & CV Generator API

This FastAPI application generates professional PDF portfolios for students. It utilizes Large Language Models (Gemini, OpenAI, or DeepSeek) to process raw student data—including academic records, projects, internships, and psychometric test results—into a cohesive narrative, which is then rendered into a styled PDF.

## 🌟 Features

* **Secure Authentication:** JWT-based login system.
* **Multi-LLM Support:** Choose between Google Gemini, OpenAI GPT-4o, or DeepSeek for content generation.
* **PDF Generation:** Converts HTML templates to PDF using `pdfkit` and `wkhtmltopdf`.
* **Asynchronous Processing:** Non-blocking PDF generation and LLM calls.
* **Robust Logging:** Dedicated logs for application events, errors, access, and security.

## 🛠️ Prerequisites

1.  **Python 3.9+**
2.  **wkhtmltopdf:** This system requires `wkhtmltopdf` to be installed on the host machine to generate PDFs.
    * *Ubuntu/Debian:* `sudo apt-get install wkhtmltopdf`
    * *Windows:* Download the installer from the [wkhtmltopdf site](https://wkhtmltopdf.org/downloads.html) and add the `bin` folder to your system PATH.

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration:**
    Create a `.env` file in the root directory:
    ```ini
    # API Keys (At least one is required)
    OPENAI_API_KEY=sk-proj-...
    GEMINI_API_KEY=AIzaSy...
    DEEPSEEK_API_KEY=sk-...

    # Model Configuration (Optional overrides)
    OPENAI_MODEL_NAME=gpt-4o
    GEMINI_MODEL_NAME=gemini-2.5-flash
    DEEPSEEK_MODEL_NAME=deepseek-chat

    # Security
    SECRET_KEY=your_super_secret_random_string
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_HOURS=1
    
    # Admin Credentials for Login
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=change_this_password

    # App Config
    BASE_URL=http://localhost:5011
    BACKEND_CORS_ORIGINS=["http://localhost:3000"]
    ```

5.  **Run the Server:**
    ```bash
    uvicorn app.main:app --reload
    ```

---

## 📡 API Documentation

### 1. Authentication
**Endpoint:** `POST /auth/login`

Used to obtain a Bearer token required for generating reports.

**Request Body:**
```json
{
  "username": "admin",
  "password": "change_this_password"
}
````

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5c...",
  "token_type": "bearer"
}
```

-----

### 2\. Generate Portfolio

**Endpoint:** `POST /report/generate`  
**Auth:** Requires Header `Authorization: Bearer <access_token>`

Generates a PDF portfolio based on the provided student data. The system sends this data to the selected LLM to write the Career Objective, Summary, and Skill Grouping before creating the PDF.

**Request Structure (JSON):**
*Note: The API expects specific Aliases (CamelCase) as defined in the Pydantic models.*

```json
{
  "model": "gemini",
  "ProfileURL": "http://127.0.0.1:5000/student.json",
  "DriveData": [
     {
      "CompanyName": "Infosys",
      "JobName": "Power Programmer",
      "Designation": "Python",
      "StudentPlacementID": "453"
    }
  ]
}
```

**Response (200 OK):**
Returns the download URL for the generated PDF.

```json
{
  "filename": "John_Doe_Portfolio.pdf",
  "report_url": "http://localhost:5011/media/reports/John_Doe_Tech_Institute_of_Engineering_john_doe_at_example_com.pdf",
  "rating": "4.3/5"
}
```

**Error Responses:**

  * `400 Bad Request`: If the input list is empty.
  * `401 Unauthorized`: If the Bearer token is missing or invalid.
  * `422 Validation Error`: If JSON keys (Aliases) do not match the expected format exactly.

## 📂 Project Structure

```
├── app
│   ├── core
│   │   ├── config.py          # Settings & Env vars
│   │   ├── logging_config.py  # Logger setup
│   │   ├── security.py        # JWT utilities
│   │   └── utils.py           # Date formatting helpers
│   ├── models
│   │   ├── report.py          # Pydantic models (Input/Output schemas)
│   │   ├── token.py           # Token schema
│   │   └── user.py            # User Login schema
│   ├── services
│   │   ├── llm_service.py     # Logic for OpenAI/Gemini/DeepSeek
│   │   └── pdf_service.py     # Logic for Jinja2 + PDFKit
│   ├── templates
│   │   └── report_template.html # Jinja2 HTML Template
│   ├── routers
│   │   ├── auth.py            # Login routes
│   │   └── report.py          # Generation routes
│   └── main.py
├── media
│   └── reports                # Generated PDF storage
├── logs                       # App logs
├── .env
└── requirements.txt
```