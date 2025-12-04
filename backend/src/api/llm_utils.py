import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
# import logging_utils


# Create HuggingFace Hub Link
load_dotenv()
hf_token = os.getenv('HF_TOKEN')
# logger.info("Retrieved HuggingFace Token")

client = InferenceClient(
    api_key=hf_token,
)
# logger.info("Built Clinet")

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


def explain_results(query, post):

    prompt = build_prompt(query, post)
    # logger.info("Built Prompt")

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