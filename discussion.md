# Discussion

This project set out to build a context aware travel recommender that can surface “off-the-beaten-path” destinations rather than repeating the same mainstream tourist hotspots. Over the course of implementation, we combined traditional information retrieval(IR) techniques, structured attributes, large-language-model explanations, and a fully containerized architecture with cloud storage on AWS. The final system not only returns relevant destinations, but also offers interpretable explanations and a modern, usable interface.

## Retrieval Models and Popularity Bias
Our first baseline was a BM25 search engine over a corpus of travel blogs. The backend structure reflects this separation: the backend/bm25 module contains scripts for constructing and evaluating BM25, while the API entry point in backend/src/api/main.py exposes a /search endpoint that can route requests to either BM25 or a custom ranking model. BM25 provided a strong traditional baseline, especially for specific keyword queries, but it also made the project’s central problem clear that it tends to over rank destinations that appear frequently in the corpus, reinforcing popularity bias.

To address this, we implemented an Attribute+Context model that integrates three main signals attribute matching, contextual cues, and query term overlap. The attribute component uses structured filters (geographic type, cultural focus, and experience tags) to ensure that results align with the user’s stated preferences. The context component scans snippets for phrases like “hidden gem,” “locals only,” or “underrated” versus “bucket list” or “tourist hotspot,” and shifts scores accordingly. This allowed the system to distinguish between generic mentions of a destination and blog posts that explicitly frame a location as quiet, local, or off the beaten path.

## LLM-Based Explanations
A notable extension beyond classic IR is the integration of a large language model explanation layer. In addition to returning structured fields (destination, country, tags, snippets, and scores), the API can call out to a Hugging Face model (configured in backend/src/api/llm_utils.py) to generate short, human-readable explanations for why each result was retrieved.

This LLM uses the original query and a summary of blog snippets as input and returns a concise paragraph describing why the location is a good fit. Conceptually, this moves the system closer to an explanatory recommender instead of just saying “Ninh Binh Backwaters – score 8.3,” the system can produce a justification like “This destination matches your request for quiet river scenery and local experiences, with early-morning kayak routes away from tour buses.” Even when the underlying ranking logic remains relatively simple, the explanation layer improves user trust and makes the system easier to evaluate qualitatively.

## Frontend Design and User Experience
The frontend, implemented in frontend/streamlit_app/app.py, evolved into a polished, product like interface. We separated concerns by moving all custom CSS into frontend/streamlit_app/style.css, then loading it via a small helper function. This made it much easier for the team to collaborate on styling changes no longer risked breaking Python logic, and interface tweaks could be done independently of the backend.

A key UX improvement was splitting the main text query into multiple prompts in the sidebar for example, asking separately about desired destination characteristics, activities, and geographic preferences. These fields are then concatenated into a single query string for the backend, but the guided prompts help users provide richer, more structured descriptions. Combined with multiselect filters for geographic type, cultural focus, and experience tags, this design encourages users to express both explicit constraints and softer “vibe” preferences.

On the results side, we used card-style layouts, metric chips, and a pydeck map to make model outputs more interpretable. The “Results” tab summarizes aggregate metrics (e.g., number of destinations, average score and confidence), while the “Maps” tab visualizes destinations geographically with color coding by score. A “Diagnostics” tab exposes the resolved parameters and model settings that were used for a given query, supporting transparency and debugging.

## Data Pipeline and AWS Storage
Under the hood, the directory structure reflects a clear pipeline:
- backend/data_collection contains scripts for scraping and reading travel blogs (get_travel_blogs.py, read_blogs_db.py).

- backend/bm25 holds the code and CSV outputs used to construct and evaluate BM25 rankings.

- data/raw and data/processed (at the project root) provide a local mirror of the data pipeline stages.

To support collaboration and scalability, we integrated AWS S3 as our primary storage for travel blog data and processed datasets. Raw and processed files such as travel_blogs.csv and BM25 top-location outputs are uploaded to S3 and mirrored in the local data directory. Access is controlled via IAM credentials loaded from environment variables (e.g., through .env and dotenv), which allows Dockerized services to read the same datasets regardless of where they run. This cloud-based storage pattern reduces friction when working across machines and directly supports the project’s Docker-first development model.

## Containerization and Deployment
The entire system is containerized: backend/Dockerfile.api defines the FastAPI image, and frontend/Dockerfile.streamlit defines the Streamlit image. Both are orchestrated by docker-compose.yml at the project root and a separate frontend/docker-compose.yml for frontend-only workflows. Building and running with docker compose up --build reliably reproduces the API and UI across environments, with ports exposed on 8081 (API) and 8501 (Streamlit).

In practice, containerization did introduce some challenges, especially around Python packaging and build tooling (e.g., pyproject.toml configuration and including backend modules in builds). Resolving these issues forced our team to clarify the package structure (e.g., backend/src/api, backend/off_the_path/src) and make the build process more explicit. While these details are largely invisible to end users, they are essential for reliable deployment and are a meaningful part of the project’s engineering learning outcomes.

## Limitations and Future Directions
Despite its strengths, the system has several limitations:

- Corpus dependency: Recommendations are constrained by the blogs in our dataset; regions with sparse coverage will remain underrepresented.

- LLM cost and latency: The explanation layer depends on external LLM inference, which introduces latency and requires careful API key management.

- Popularity estimation: Popularity is proxied by blog frequency, which only approximates real-world tourism pressure.

Future work could explore embedding-based retrieval (e.g., vector search over sentence embeddings), learning-to-rank approaches that jointly optimize attribute and context signals, and tighter integration between S3-hosted data, MLflow experiments, and deployment scripts in deployment/. At the front-end level, we could extend personalization by adding user profiles or history-aware recommendations.

Overall, the project demonstrates that combining classical IR, structured attributes, popularity corrections, LLM explanations, and a thoughtfully designed UI—backed by Docker and AWS can produce a compelling prototype for discovering truly off-the-beaten-path travel destinations.