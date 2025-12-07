import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Import Logger
from .logging_utils import get_logger

logger = get_logger("llm_utils")

# Create HuggingFace Hub Link
load_dotenv()

hf_token = os.getenv('HF_TOKEN')

if hf_token:
    logger.info("Retrieved HuggingFace Token")
else:
    logger.warning("HF_TOKEN not found. LLM features may fail.")

client = InferenceClient(
    token=hf_token,
)
logger.info("Built Client")

def build_prompt(query, blog_post):
    prompt = f"""
    You are an AI assistant helping explain why the returned post about a vacation spot was retrieved for the given query.
    The results were generated through FAISS.
    
    Given the following query: '{query}'

    And the returned neighbor (blog post about travel): {blog_post}

    Explain in clear, human terms why this vacation location is a good option for the user to consider given their request query.
    The response should be a maximum of 8 sentances.
    """
    return prompt.strip()


def explain_results(query, post_text):

    prompt = build_prompt(query, post_text)
    logger.info("Built Prompt")

    if hf_token:
        try:
            completion = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3.2",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            gen_text = completion.choices[0].message['content']
            return gen_text
        except Exception as e:
            logger.error(f"LLM explanation generation failed: {e}")
            return "Explanation unavailable due to an error."
    else:
        logger.warning("Skipping LLM explanation: No token available")
        return "Explanation unavailable (No API Token)."