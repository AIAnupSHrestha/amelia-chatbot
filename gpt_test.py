import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(
  api_key=OPENAI_KEY
)
yes_no_prompt = """
    Is the following answer relevant to the question {current_question}: '{user_answer}'? Answer with 'yes' or 'no' OR 'true' or 'false', without any additional explanation..
    """
def prompt_engineering(prompt):
    response = client.chat.completions.create(
        model="GPT-Model",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content

current_question = "How will the mandatory core period be enforced, and what tools or systems will be used to track employee hours"
user_answer = "The mandatory core period will be enforced through automated time-tracking software integrated with attendance systems to monitor and record employee hours."

prompt = yes_no_prompt.format(current_question=current_question, user_answer=user_answer)

# print(prompt)

answer_relevance = prompt_engineering(prompt=prompt)

print(answer_relevance)

