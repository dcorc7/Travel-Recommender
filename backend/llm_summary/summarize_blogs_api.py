import os
from huggingface_hub import InferenceClient
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("travel-data")

# Create HuggingFace Hub Link
load_dotenv()
hf_token = os.getenv('HF_TOKEN')
logger.info("Retrieved HuggingFace Token")

client = InferenceClient(
    api_key=hf_token,
)
logger.info("Built Clinet")

def build_prompt( query, blog_post):
    prompt = f"""
    You are an AI assistance helping explain why the returned post about a vacation spot was retrieved for the given query.
    The results were generated through FAISS.
    
    Given the following query: '{query}'

    And the returned neighbor (blog post about travel): {blog_post}

    Explain in clear, human terms why this vacation location is a good option for the user to consider given their request query.
    The response should be a maximum of 8 sentances.
    """
    return prompt.strip()


def explain_results(query, post):

    prompt = build_prompt(query, post)
    logger.info("Built Prompt")

    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return completion.choices[0].message['content']


query_text = "Im looking for a vacation spot that is a cute, quaint village in a mountain town. I would like it to have cultural aspects."

neighbor = "Continuing my icy adventures, this post will tell you about Vail, Colorado, famous famous famous for skiing and snowboarding – and well deserved!",
"After visiting Dillon’s Ice Castles on a recent Friday, my husband and I headed to Vail for what we thought was one night. Turned out to be two nights because we got 10+ inches of snow overnight and it just kept coming down! Not sorry, as you’ll see!",
"During that weekend we took the thank-god-for-this-miracle hotel shuttle to Vail Village. Official but unromantic name of the bus stop: Vail Transportation Center. Before leaving that morning, I snapped this photo at the hotel’s pool as my husband made some sort of statement about macaques in Japan:",
"Now, that’s MY kind of pool party! But I digress. Back to Vail Village. In short order, and after a stop at the Lionshead Village Welcome Center, we stepped off the bus at Vail Village. It was still snowing lightly and everything was covered in a beautiful white blanket! Here’s the scene from the deck of the transpo center – note the slopes in the background:"


print(explain_results(query_text, neighbor))