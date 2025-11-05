# Dockerfile

# 1. Base Image: Use a slim, stable version of Python.
FROM python:3.11-slim-bullseye

# 2. Set Environment Variables: Prevents Python from buffering output, which is better for logging.
ENV PYTHONUNBUFFERED=1

# 3. Install System Dependencies: Update package lists and install wkhtmltopdf, which is required by pdfkit.
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 4. Set Working Directory: Create a directory inside the container to hold the application code.
WORKDIR /app

# 5. Copy and Install Python Dependencies: Copy the requirements file first to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Code: Copy the rest of your application source code into the working directory.
COPY ./app ./app
COPY main.py .

# 7. Expose Port: Inform Docker that the container listens on port 8000.
EXPOSE 8000

# 8. Run Command: The command to start the application when the container launches.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]