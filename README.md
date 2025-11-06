# dsan6700_app_dev_project
Off the Beaten Path application deployment

# Off-the-Beaten-Path Travel Recommender

## Project Overview
This project is a travel recommendation system designed to help users discover “off-the-beaten-path” destinations. Unlike traditional recommendation engines that favor popular tourist spots, our system identifies hidden gems by analyzing context, attributes, and trends from travel blogs and other content. Users can input free-form queries such as:

"small coastal towns in Spain with artisan markets"

and the system returns a ranked list of lesser-known destinations that match their interests.

### Key Features
- **Context-Aware Scoring:** NLP pipeline detects phrases indicating hidden or popular destinations and adjusts scores accordingly.  
- **Attribute-Based Matching:** Recommends destinations even if they are not explicitly mentioned, based on attributes like geography, culture, and experience type.  
- **Popularity Bias Mitigation:** Uses Bloom filters, frequency tiers, and temporal trend analysis to reduce dominance of mainstream locations.  
- **Evaluation and Visualization:** Combines TF-IDF, BM25, and cosine similarity for ranking, and displays results on an interactive map with confidence and trend indicators.  

## Project Structure

```
dsan6700_app_dev_project/
│ pyproject.toml
│ docker-compose.yml
│ Dockerfile.api
│ README.md
│
├── configs/ # Model and app configuration files
├── data/
│ ├── raw/ # Original raw data
│ └── processed/ # Preprocessed datasets
├── deployment/
│ ├── kubernetes/ # K8s deployment instructions
│ └── mlflow/ # MLflow docker setup
├── models/ # Saved trained models
├── src/
│ ├── api/ # API backend (inference & schemas)
│ ├── data/ # Data processing scripts
│ └── features/ # Feature engineering scripts
└── streamlit_app/ # Streamlit frontend and Dockerfile
```


## Getting Started

### Prerequisites
- Python >= 3.10  
- [Poetry](https://python-poetry.org/) for dependency management  
- [Docker](https://www.docker.com/) for containerized deployment  

### Local Setup with Poetry
1. Navigate to the project directory:  

```bash
cd /path/to/dsan6700_app_dev_project
```

2. Install dependencies and create a virtual environment:

```bash
poetry install
```

3. Activate the environment:

```bash
poetry shell
```

4. Run the Streamlit app locally:

```bash
cd streamlit_app
streamlit run app.py
```

### Docker Deployment

1. Build the Docker image for the API backend:
```bash
docker build -f Dockerfile.api -t travel-api .
```

2. Start the app via Docker Compose:
```bash
docker-compose up
```

### Hugging Face Spaces Deployment

To deploy on Hugging Face Spaces:

FILL IN LATER