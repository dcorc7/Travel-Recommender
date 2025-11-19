# streamlit_app/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for better caching
COPY streamlit_app/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip wheel && \
    pip install -r /tmp/requirements.txt

# Then bring in the app
COPY ./streamlit_app /app/streamlit_app

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
