from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
import pprint

llm = ChatOllama(
    model="llama2",
    temperature=0,
    # other params...
)

def extract_before_comma(input_string):
    return input_string.split(',')[0]

current_question = "How will the mandatory core period be enforced, and what tools or systems will be used to track employee hours"
user_answer = "python" #"The mandatory core period will be enforced through automated time-tracking software integrated with attendance systems to monitor and record employee hours."

yes_no_prompt = f"""
    Is the following answer relevant to the question {current_question}: '{user_answer}'.Answer with 'yes' or 'no'?.
    """

messages = [
    (
        "system", "You are a helpful assistant that checks whether the user_answer is relevant to the question. Respond with 'yes' or 'no' only, without any additional explanation. ",
    ),
    ("human", yes_no_prompt),
]
# ai_msg = extract_before_comma(llm.invoke(messages).content)
ai_msg = llm.invoke(messages).content

print(ai_msg)