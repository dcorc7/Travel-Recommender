# Off-the-Beaten-Path Travel Recommender

**Authors:**
- David Corcoran
- Morgan Dreiss
- Nadav Gerner
- Walter Hall
- Adam Stein

## Overview

This project implements a context-aware travel recommendation system designed to surface "off-the-beaten-path" destinations. Unlike traditional recommendation engines that favor popular tourist spots, our system identifies hidden gems by analyzing travel blogs, structured attributes, and popularity signals to recommend lesser-known destinations that match user interests.

The application combines:
- **BM25 Baseline Search**: Traditional information retrieval over a corpus of travel blogs
- **ModernBERT Search Model**: Semantic retrieval and re-ranking using transformer-based text embeddings from blog content, enabling contextual understanding beyond keyword matching

All components are containerized using Docker and orchestrated with Docker Compose for easy deployment and reproducibility.

## Project Structure
```
dsan6700_app_dev_project/
│
├── backend/
│   ├── Dockerfile.api              # API container definition
│   ├── configs/
│   │   └── app_config.yaml         # Application configuration
│   ├── off_the_path/               # Core package
│   ├── src/
│   │   ├── api/
│   │   │   ├── main.py             # FastAPI endpoints
│   │   │   ├── bm25_utils.py       # BM25 search utilities
│   │   │   └── __init__.py
│   │   └── features/
│   │       └── engineer.py         # Feature engineering
│   └── pyproject.toml              # Python dependencies
│
├── frontend/
│   ├── Dockerfile.streamlit        # Frontend container definition
│   └── streamlit_app/
│       └── app.py                  # Streamlit UI
│
├── .dockerignore                   # Files to ignore in Docker builds
├── .gitignore                      # Files to ignore in Git
├── .env                            # Environment variables (DATABASE_URL)
├── docker-compose.yml              # Orchestrates all services
└── README.md                       # This file
```

## Project Components

### BM25 Baseline Search
BM25 (Best Match 25) is a ranking function used by search engines to estimate the relevance of documents to a given search query. Our implementation:

**How It Works:**
- Loads ~XX,XXX travel blog posts from PostgreSQL database
- Tokenizes and indexes content using `rank-bm25`
- Returns top-k most relevant destinations based on query terms
- Provides blog metadata (title, author, URL) for each result

**Features:**
- Full-text search over blog titles, descriptions, and content
- Fast in-memory indexing (loaded once at startup)
- Returns destination names, coordinates, and content previews

### ModernBERT Semantic Search Model

A transformer-based semantic retrieval and re-ranking model that captures the meaning of user queries and travel narratives, enabling discovery of destinations that align with “off-the-beaten-path” intent beyond surface-level keyword overlap.

**How it Works**

- Encodes blog content and user queries using ModernBERT transformer embeddings
- Projects both into a shared semantic vector space
- Computes similarity scores to retrieve and re-rank destinations based on contextual relevance
- Combines semantic similarity with lightweight metadata filters (e.g., geography, experience type)

**Model Capabilities:**

- Understands experiential intent (e.g., quiet, local, remote, authentic) from natural language
- Captures contextual cues implicitly through embeddings rather than hand-crafted rules
- Handles synonymy and paraphrasing (e.g., “hidden village” ≈ “undiscovered town”)
- Robust to sparse or ambiguous queries

**Outputs:**

- Ranked list of destinations with semantic relevance scores
- Associated blog metadata (title, author, URL, excerpts)
- Destination coordinates for downstream visualization

### Architecture

The application consists of two Docker containers:

**Frontend (Streamlit)**
- Port: 8501
- Framework: Streamlit
- Purpose: Interactive web UI for search and visualization

**API Layer (FastAPI)**
- Port: 8000 (mapped to 8081 on host)
- Framework: FastAPI
- Purpose: Serves BM25 and ModernBERT models via REST API

**Database**
- PostgreSQL database containing travel blog corpus
- Connected via `DATABASE_URL` environment variable
- Stores: blog posts, locations, coordinates, metadata

## Prerequisites

Before running this project, ensure you have:

**Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- Version 20.10 or higher
- Download: https://www.docker.com/products/docker-desktop

**Docker Compose**
- Version 2.0 or higher
- Included with Docker Desktop
- For Linux: https://docs.docker.com/compose/install/

**Verify Installation:**
```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Verify Docker is running
docker ps
```

## Docker Deployment Instructions

### Building and Starting Containers

**1. Clone the Repository:**
```bash
# Clone the project repository
git clone https://github.com/your-org/dsan6700_app_dev_project.git

# Navigate to project directory
cd dsan6700_app_dev_project
```

**2. Set Up Environment Variables:**

Create a `.env` file in the project root with your database connection:
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

**3. Build and Start All Services:**
```bash
# Build images and start containers
docker-compose up --build

# OR run in detached mode (background)
docker-compose up --build -d
```

**What This Does:**
- Builds the API container from `backend/Dockerfile.api`
- Builds the Streamlit container from `frontend/Dockerfile.streamlit`
- Creates a Docker network for inter-container communication
- Starts both services with proper dependency ordering
- Mounts source directories for hot-reloading during development

**4. Wait for Services to Initialize:**

The first BM25 search will load ~XX,XXX blog posts from the database and build the index. This takes approximately 30-60 seconds.

### Accessing the Applications

Once containers are running:

**Travel Recommender Web Interface:**
- URL: http://localhost:8501
- Opens Streamlit application in your browser
- Search for destinations and view recommendations

**API Documentation:**
- URL: http://localhost:8081/docs
- Interactive FastAPI Swagger documentation
- Test API endpoints directly from browser

**Health Check:**
- URL: http://localhost:8081/health
- Returns system status and BM25 availability

### Viewing Container Status

**Check Running Containers:**
```bash
# View all running containers
docker-compose ps

# Expected output:
# NAME        IMAGE                             STATUS    PORTS
# api         dsan6700_app_dev_project-api      Up        0.0.0.0:8081->8000/tcp
# streamlit   dsan6700_app_dev_project-streamlit Up       0.0.0.0:8501->8501/tcp
```

**View Container Logs:**
```bash
# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs api
docker-compose logs streamlit

# Follow logs in real-time (Ctrl+C to exit)
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail=50
```

**Monitor Resource Usage:**
```bash
# View CPU, memory, and network usage
docker stats
```

**Inspect Container Details:**
```bash
# List all Docker containers (including stopped)
docker ps -a

# Execute commands inside container
docker exec -it api bash
```

### Stopping and Removing Containers

**Stop Containers (Preserves Data):**
```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop api
```

**Complete Cleanup (Remove Everything):**
```bash
# Stop containers and remove volumes
docker-compose down -v

# Remove all unused Docker resources
docker system prune -a --volumes
```

**Restart Services:**
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
```

## Using the Travel Recommender

### Step 1: Access the Web Interface
Open your browser and navigate to http://localhost:8501

### Step 2: Select Search Model
Choose between:
- **BM25**: Traditional keyword-based search over blog corpus
- **ModernBERT (Recommended)**: Custom ranking with popularity dampening

### Step 3: Configure Search Parameters

**Query:**
- Enter free-form text: "small coastal towns with artisan markets"
- Describe the type of destination you're looking for

**Filters:**
- **Activity Types**: skiing, hiking, museums, camping, diving, etc.
- **Geographic Type**: coastal, mountain, island, urban, desert, etc.
- **Results (k)**: Number of destinations to return (3-50)

### Step 4: View Results

The application returns:

**Results Tab:**
- Ranked list of destinations with scores and confidence
- Destination name and country
- Tags (geographic, cultural, experience)
- Snippets from relevant blog posts
- Context cues (positive/negative indicators)
- Scoring breakdown

**Maps Tab:**
- Interactive global map with destination markers
- Color-coded by relevance score
- Click markers for details

**Diagnostics Tab:**
- Model parameters used
- Weight distributions
- Filter settings

## API Usage

You can also interact directly with the API:

### Search Endpoint

**BM25 Search:**
```bash
curl -X POST "http://localhost:8081/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "temples in Kyoto Japan",
    "retrieval": {
      "model": "bm25",
      "k": 10
    }
  }'
```

**ModernBERT Semantic Search (FAISS):**
```bash
curl -X POST "http://localhost:8081/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quiet coastal villages with local markets",
    "retrieval": {
      "model": "faiss",
      "k": 12
    }
  }'
```

### Response Format
```json
{
  "query": "quiet coastal villages with local markets",
  "params": {
    "retrieval": {
      "model": "faiss",
      "k": 12
    },
    "model_used": "faiss"
  },
  "results": [
    {
      "destination": "Ninh Binh",
      "country": "Vietnam",
      "lat": 20.25,
      "lon": 105.9,
      "distance": 0.1342,
      "snippets": [
        "A quiet region of limestone karsts and river villages.",
        "Local markets operate daily with minimal tourism."
      ],
      "full_content": "Full blog text...",
      "why": {
        "model": "FAISS",
        "page_title": "Hidden Northern Vietnam",
        "page_url": "https://example.com/blog/post",
        "blog_url": "https://example.com",
        "author": "Travel Blogger"
      }
    }
  ],
  "explanations": [
    "This destination aligns with your query due to its emphasis on quiet local villages and authentic market culture..."
  ]
}
```

## Viewing the MkDocs Documentation

This project includes a documentation site built with MkDocs.

### Serve the Docs Locally

From the project root directory, run:

```bash
mkdocs serve
```

Open your browser and navigate to:

```
http://127.0.0.1:8000/
```

### Build the Static Site

To generate a static version of the documentation:

```bash
mkdocs build
```

This creates a site/ directory containing the compiled HTML files. You can open site/index.html directly in a browser or deploy the folder to any static hosting service.

## Development

### Local Development Without Docker

**1. Set up Python environment:**
```bash
# Using Poetry
poetry install
poetry shell

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

**2. Run API locally:**
```bash
cd backend/src/api
uvicorn main:app --reload --port 8000
```

**3. Run Streamlit locally:**
```bash
cd frontend/streamlit_app
streamlit run app.py
```