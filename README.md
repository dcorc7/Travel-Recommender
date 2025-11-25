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
- **Attribute+Context Model**: Custom ranking that considers geographic type, cultural focus, experience tags, and contextual cues from blog content
- **Popularity Bias Correction**: Bloom filters and Zipf-penalty dampening to reduce over-representation of mainstream destinations

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

### Attribute+Context Model
A custom ranking algorithm that goes beyond keyword matching to understand what makes a destination "off the beaten path."

**Scoring Components:**
1. **Attribute Matching** (`w_attr = 0.5`): Matches user-selected filters
   - Geographic type: coastal, mountain, island, urban, etc.
   - Cultural focus: food, art, history, markets, etc.
   - Experience tags: quiet, adventure, hiking, photography, etc.

2. **Context Signal** (`w_ctx = 0.35`): Analyzes blog language
   - Positive cues: "hidden gem", "locals only", "underrated", "rarely visited"
   - Negative cues: "bucket list", "must-see", "tourist hotspot", "crowded"

3. **Query Term Overlap** (`w_qry = 0.15`): Traditional text matching

**Popularity Dampening:**
- **Bloom Filter**: Excludes destinations above popularity threshold
- **Zipf Penalty**: Applies graduated penalty based on destination frequency
- **Tier Bucketing**: Groups popularity into discrete tiers for consistent dampening

### Architecture

The application consists of two Docker containers:

**Frontend (Streamlit)**
- Port: 8501
- Framework: Streamlit
- Purpose: Interactive web UI for search and visualization

**API Layer (FastAPI)**
- Port: 8000 (mapped to 8081 on host)
- Framework: FastAPI
- Purpose: Serves BM25 and Attribute+Context models via REST API

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
- **Attribute+Context (Recommended)**: Custom ranking with popularity dampening
- **TF-IDF**: Alternative keyword-based approach

### Step 3: Configure Search Parameters

**Query:**
- Enter free-form text: "small coastal towns with artisan markets"
- Describe the type of destination you're looking for

**Filters:**
- **Geographic Type**: coastal, mountain, island, urban, desert, etc.
- **Cultural Focus**: food, art, history, music, markets, festivals
- **Experience Tags**: quiet, adventure, local, hiking, scenic

**Model Controls:**
- **Bloom Filter**: Exclude high-frequency (popular) destinations
- **Zipf Penalty**: Adjust popularity dampening strength (0-1)
- **Tier Bucketing**: Group similar popularity levels together

**Advanced:**
- **Google Trends**: Incorporate temporal popularity signals (experimental)
- **Time Horizon**: 1 year, 90 days, 30 days, or all time
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
    "filters": {
      "geotype": [],
      "culture": [],
      "experience": [],
      "min_confidence": 0.0
    },
    "retrieval": {
      "model": "bm25",
      "use_bloom": false,
      "zipf_penalty": 0.0,
      "tier_bucketing": false,
      "use_trends": false,
      "date_range": "1y",
      "k": 10
    }
  }'
```

**Attribute+Context Search:**
```bash
curl -X POST "http://localhost:8081/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quiet coastal villages with local markets",
    "filters": {
      "geotype": ["coastal"],
      "culture": ["markets", "food"],
      "experience": ["quiet", "local"],
      "min_confidence": 0.3
    },
    "retrieval": {
      "model": "attribute+context",
      "use_bloom": true,
      "zipf_penalty": 0.35,
      "tier_bucketing": true,
      "use_trends": false,
      "date_range": "1y",
      "k": 12
    }
  }'
```

### Response Format
```json
{
  "query": "quiet coastal villages",
  "params": {
    "filters": { ... },
    "retrieval": { ... },
    "model_used": "bm25"
  },
  "results": [
    {
      "destination": "Ninh Binh, Vietnam",
      "country": "Vietnam",
      "lat": 20.25,
      "lon": 105.9,
      "score": 8.3421,
      "confidence": 0.83,
      "tags": ["coastal", "kayak", "quiet"],
      "snippets": [
        "Pre-sunrise kayak under limestone arches—no tour buses.",
        "Herons wake along quiet canals; underrated and serene."
      ],
      "why": {
        "model": "BM25",
        "page_title": "Hidden Gems of Northern Vietnam",
        "page_url": "https://example.com/blog/post",
        "author": "Travel Blogger"
      }
    }
  ]
}
```

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