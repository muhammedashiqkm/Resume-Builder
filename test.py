import requests
from requests_toolbelt.multipart import decoder

# --- Setup your request ---
api_url = "http://127.0.0.1:8000/api/v1/generate-portfolio-multipart"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1OTIxNTU4NH0.tkNL7Rd5cNlSxD0VjLkY-pqv-EWY0tQrVI6OtdPmYI4"
headers = {"Authorization": f"Bearer {token}"}
json_payload = {
  "name": "Your Name",
  "email": "your.email@example.com",
  "number": "+1-555-123-4567",
  "semester_marks": [{"semester": 1, "marks": 88.5}],
  "skillset": ["Python", "FastAPI"],
  "self_assessment": "A dedicated student.",
  "projects": [{"title": "Test Project", "description": "A cool project."}]
}

# --- Send the request ---
response = requests.post(api_url, headers=headers, json=json_payload)

# --- Parse the response ---
if response.status_code == 200:
    multipart_data = decoder.MultipartDecoder.from_response(response)
    for part in multipart_data.parts:
        # Get the filename from the headers of each part
        content_disposition = part.headers.get(b'Content-Disposition', b'').decode()

        if 'filename="portfolio.json"' in content_disposition:
            print("--- Portfolio JSON ---")
            print(part.text)

        elif 'filename="cv.pdf"' in content_disposition:
            with open("downloaded_cv.pdf", "wb") as f:
                f.write(part.content)
            print("\n--- PDF ---")
            print("✅ CV saved as 'downloaded_cv.pdf'")
else:
    print(f"Error: {response.status_code}")
    print(response.text)