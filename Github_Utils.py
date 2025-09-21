import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv() 

# Load GitHub API PAT Token and endpoint
github_PAT_key = os.getenv("GITHUB_TOKEN")
github_api_url = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"

# Initialize OpenAI client
client = OpenAI(
    base_url=github_api_url,
    api_key=github_PAT_key,
)

def summarize_text(text):
    """Summarizes the text using GitHub's models API."""
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": f"Summarize the following text: {text}",
                }
            ],
            temperature=0.7,
            top_p=1.0,
            max_tokens=300,
            model=model_name
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error with GitHub API: {e}"

def ask_question_about_text(text, question):
    """Asks a question about the text using GitHub's models API."""
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": f"Based on the following text: {text}\n\n Answer this question: {question}",
                }
            ],
            temperature=0.7,
            top_p=1.0,
            max_tokens=300,
            model=model_name
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error with GitHub API: {e}"