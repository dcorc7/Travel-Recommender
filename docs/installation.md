# Installation & Setup Guide

This guide walks through setting up the Off-The-Path Travel Recommendation system locally, installing dependencies, running the backend API, and launching the Streamlit frontend interface. You should only need to follow this once during development.

---

## Requirements

Ensure you have the following installed:

- Python **3.10+**
- Docker & Docker Compose
- Git
- uv or pip for dependency management
- PostgreSQL instance (local or cloud)
- AWS S3 bucket (for embedding storage)

Optional but recommended:
- Virtual environment tool (`uv venv`, `python -m venv`, `conda`, etc.)

---

## 1. Clone the Repository

```bash
git clone https://github.com/med2106/dsan6700_app_dev_project.git
cd dsan6700_app_dev_project
```

## 2. Create & Activate Virtual Environment (Recommended)

```bash
uv venv
.\.venv\Scripts\activate         # Windows
source .venv/bin/activate        # Mac/Linux
```

## 3. Install Dependencies

Install the base package

```bash
uv sync
```

or alternatively using pip:

```bash
pip install .
```

## 4. Configure Environment Variables

Create a .env file in the project root:

```bash
POSTGRES_URL=your_postgres_url
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket
SERP_API_KEY=your_serp_key
```

Make sure not to commit .env to GitHub.

## 5. Run With Docker (Recommended)

From project root:

```bash
docker compose up --build
```

| Service                   | URL                                                      |
| ------------------------- | -------------------------------------------------------- |
| **Backend API (FastAPI)** | [http://localhost:8000](http://localhost:8000)           |
| **Streamlit UI**          | [http://localhost:8501](http://localhost:8501)           |
| **API Docs**              | [http://localhost:8000/docs](http://localhost:8000/docs) |


## 6. Run Locally Without Docker

Start Backend

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Start Frontend

```bash
uv run streamlit run frontend/streamlit_app/app.py
```

## 7. Verify Installation

Open browser and test:

```bash
http://localhost:8501          # Streamlit App
http://localhost:8000/docs     # Swagger API Docs
```