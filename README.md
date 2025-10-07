# AI-Powered Candidate Evaluation Service

This backend service automates the initial candidate screening process using an AI-driven architecture. The service accepts a candidate's CV and project report, evaluates them against reference documents (like a job description and scoring rubrics) using a **Retrieval-Augmented Generation (RAG)** and **LLM Chaining** workflow, and produces a structured evaluation report in JSON format.

## Key Features

* **Asynchronous Architecture**: Intensive evaluation processes run in the background using Celery and Redis, ensuring the API remains responsive.
* **Cloud Storage Ready**: Integrated with **Amazon S3** for scalable and persistent file storage using `django-storages`.
* **RESTful API**: Provides clean endpoints for uploading documents, managing references, triggering evaluations, and retrieving results.
* **Intelligent Evaluation Pipeline**: Utilizes **RAG** to retrieve relevant context from a vector database (ChromaDB) before constructing prompts for the LLM.
* **LLM Chaining**: Breaks down the evaluation into three distinct stages (CV Evaluation, Project Evaluation, and Final Synthesis) for more accurate and structured results.
* **Idempotency**: Prevents duplicate job creation on the evaluation endpoint through the use of an `Idempotency-Key` header.

## Architecture & Tech Stack

* **Backend Framework**: Django & Django REST Framework
* **Asynchronous Processing**: Celery & Redis
* **File Storage**: Amazon S3 (via `django-storages` and `boto3`)
* **Vector Database**: ChromaDB
* **PDF Processing**: pypdf (file-like extractor)
* **LLM Interaction**: OpenRouter/OpenAI

## Installation & Setup Guide

Follow these steps to get the project running locally.

### 1. Prerequisites

* Python 3.10+
* Redis
* An AWS S3 bucket with IAM credentials.
* Docker (Recommended for Redis)

### 2. Project Setup

1.  **Clone this repository:**
    ```bash
    git clone [https://github.com/abbysgud/ai-candidate-evaluation.git](https://github.com/abbysgud/ai-candidate-evaluation.git)
    cd ai-candidate-evaluation
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use: .\venv\Scripts\activate
    ```

3.  **Install all dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the project's root directory. This is where you'll store all your secrets.

    ```env
    # Django Settings
    SECRET_KEY='your-django-secret-key'
    DEBUG=True

    # Database URL (default: sqlite)
    DATABASE_URL='sqlite:///db.sqlite3'

    # Redis URL for Celery
    CELERY_BROKER_URL='redis://localhost:6379/0'
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'

    # LLM Provider API Key
    OPENROUTER_API_KEY='your-openrouter-or-openai-api-key'

    # AWS S3 Configuration for File Storage
    AWS_ACCESS_KEY_ID='your-aws-access-key-id'
    AWS_SECRET_ACCESS_KEY='your-aws-secret-access-key'
    AWS_STORAGE_BUCKET_NAME='your-s3-bucket-name'
    AWS_S3_REGION_NAME='your-s3-bucket-region' # e.g., ap-southeast-1
    ```

5.  **Run Database Migrations:**
    ```bash
    python manage.py migrate
    ```

### 3. Running the Service

You will need to run three separate processes in different terminals.

1.  **Start the Redis Server:**
    If you are using Docker, run:
    ```bash
    docker run -d -p 6379:6379 redis
    ```

2.  **Start the Celery Worker:**
    In a second terminal (with the virtual environment activated), run:
    ```bash
    celery -A backend worker -l info
    ```

3.  **Start the Django Development Server:**
    In a third terminal (with the virtual environment activated), run:
    ```bash
    python manage.py runserver
    ```

The API server will now be running at `http://127.0.0.1:8000`.

## Basic API Workflow

Here is the basic workflow to evaluate a candidate:

1.  **Create a Reference Set**: Send a `POST` request to `/api/reference-set` to create a container for your reference documents.
    ```json
    {
        "name": "Backend Engineer 2025"
    }
    ```
    Save the `id` from the response.

2.  **Upload Reference Documents**: Send multiple `POST` requests to `/api/upload-reference/` to upload the job description, case brief, and rubrics. Use the `reference_set_id` from the previous step.

3.  **Upload Candidate Documents**: Send a `POST` request to `/api/upload/` with the candidate's `cv` and `report`. Save the `cv_document_id` and `report_document_id` from the response.

4.  **Start the Evaluation**: Send a `POST` request to `/api/evaluate` with all the IDs you have collected.
    ```json
    {
      "reference_set_id": "0ce4b974-6897-4ff7-8eed-4f08f678cda4",
      "job_title": "Backend Engineer",
      "cv_document_id": "uuid-from-step-3",
      "report_document_id": "uuid-from-step-3"
    }
    ```
    Save the job `id` from the response.

5.  **Check the Result**: Poll the `GET /api/result/<job_id>` endpoint. Repeat until the status changes to `completed` or `failed`.

## API Endpoint Summary

### Core Endpoints

* `POST /api/upload/`: Upload candidate CV and report.
* `POST /api/evaluate`: Trigger the evaluation process.
* `GET /api/result/<uuid:job_id>`: Retrieve the evaluation status and result.

### Reference Management

* `GET, POST /api/reference-set`: List or create a new reference set.
* `POST /api/upload-reference/`: Upload a single reference document.

### Debug & Utility

* `GET /api/jobs/<uuid:job_id>`: Get detailed information about a job.
* `GET /api/debug/index-stats`: Get stats from the vector database.
* `POST /api/debug/reindex-all`: Force re-index all documents.
* `GET /api/retrieve`: Test the RAG search functionality directly.
