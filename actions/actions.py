# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Dict, List, Text, Union
import random
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Form, FollowupAction
from rasa_sdk import Action, FormValidationAction, forms
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import re
from fpdf import FPDF

from reportlab.pdfgen import canvas 
from reportlab.pdfbase.ttfonts import TTFont 
from reportlab.pdfbase import pdfmetrics 
from reportlab.lib import colors 

# import mysql.connector
# from mysql.connector import errorcode

load_dotenv()
OPENAI_KEY = "123456787654321" #os.getenv("OPENAI_API_KEY")
client = OpenAI(
  api_key=OPENAI_KEY
)

# config = {
#     'host': '127.0.0.1',  # or your MySQL server host
#     'user':'root', 
#     'password':"",
#     # Add 'user' and 'password' fields if your MySQL server requires them
# }
# cnx = mysql.connector.connect(**config)
# cursor = cnx.cursor()
# cursor.execute("USE amelio")

PROMPT_TEMPLATE = """
You are an expert in drafting HR policies. I am currently working on creating an {job_type}. The policy will include the following condition: {flexible_work_option}.
Based on this specific clause, please provide a list of detailed questions to consider:
Output should be a list of length 5: [Question 1, Question 2, Question 3, Question 4, Question 5]
"""

with open('actions/predefined_questions.json', 'r') as file:
    predefined_questions = json.load(file)

def get_policy_from_db(table_name, attribute_name, value):
    value = value.lower()
    query = f"SELECT * FROM {table_name} WHERE {attribute_name}='{value}'"
    # cursor.execute(query)
    # result = cursor.fetchmany()
    # Returns list of policy
    # return result



class ActionGreet(Action):

    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        messages = ["Hi there. 👋😃 It's such a pleasure to have you here. How may I help you?",
                    "Hello, 🤗 how can we assist you?"]
        
        buttons = [
            # {"payload": "/job_posting", "title": "Job Posting"},
            # {"payload": '/hr_policy', "title": "HR Policy"},
            {"payload": '/select_option{"option": "selected_hr_policy"}', "title": "HR Policy"}
        ]

        reply = random.choice(messages)
        dispatcher.utter_message(text=reply, buttons=buttons)

        return []



class ActionHrPolicy(Action):
    
        def name(self) -> Text:
            return "action_hr_policy"
    
        def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
            # buttons = [
            #     {"payload": "/hr_policy{'content_type': 'hr_policy'}", "title": "HR Policy"},
            #     {"payload": "/job_posting", "title": "Job Posting"}
            # ]
            try:
                hr_policy_type = tracker.get_slot("hr_policy_type")
            except:
                hr_policy_type = None
    
            if hr_policy_type:
                message = f"You selected: {hr_policy_type} policy."
                # policies = get_policy_from_db('hr_policy', 'policy_name', hr_policy_type)
                # Fetch all of remote work policies
                # query = f"SELECT hr_policy_type.* \
                #             FROM hr_policy_type \
                #             JOIN hr_policy ON hr_policy_type.hr_policy_id = hr_policy.id \
                #             WHERE hr_policy.policy_name = '{hr_policy_type}'; \
                #         "
                # cursor.execute(query)
                # policies = cursor.fetchmany()
                policies = [
                    ('flexible', 'Flexible Work'),
                    ('remote', 'Remote Work'),
                    ('part_time', 'Part-time Work'),
                    ('unpaid_leave', 'Unpaid Leave'),
                    ('job_sharing', 'Job Sharing')
                ]
                buttons = []
                if policies:
                    message += "\nHere are some templates for you:"
                    for p_template in policies:
                        # Suggest as button
                        buttons.append({
                            "payload": '/policy_type{"policy_name": "'+p_template[0]+'"}',
                            "title": p_template[1].capitalize()
                        })
                buttons.append(
                    {"payload": '/policy_type{"policy_name": None}', "title": "Create your own"}
                )
                dispatcher.utter_message(text=message, buttons=buttons)
            else:
                message = "You have selected HR policy. \nWhat policy would you like to create?"
                dispatcher.utter_message(text=message,)
    
            return []

class ActionPolicyType(Action):
        
        def name(self) -> Text:
            return "action_policy_type"
    
        def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            try:
                selected_policy = tracker.get_slot('policy_name')
            except:
                selected_policy = None
            # query = f"SELECT * FROM hr_policy_type WHERE {attribute_name}='{value}'"
            # cursor.execute(query)
            # result = cursor.fetchmany()
            # selected_policy = get_policy_from_db('hr_policy_type', 'policy_name', selected_policy)
            selected_policy = 'flexible'
            if selected_policy.lower() == 'flexible':
                options = predefined_questions[selected_policy]
                buttons = []
                for key, option_val in options.items():
                    # buttons.append(
                    #     {
                    #         "label" : option_val,
                    #         "value": "/select_flexible_work_option{'flexible_work_option': '"+key+"'}"
                    #     }
                    # )
                    # "/select_flexible_work_option{'flexible_work_option': 'a'}"
                # message={"payload":"dropDown","data":buttons}
                    buttons.append({
                        "payload": '/select_flexible_work_option{"flexible_work_option": "'+key+'"}',
                        "title": option_val
                    })
                dispatcher.utter_message(text="Please select your flexible work option:", buttons=buttons)
                # dispatcher.utter_message(text="Please select your flexible work option:", attachment=message)
                # dispatcher.utter_message(text="Please select your flexible work option:", json_message=message)
            else:
                dispatcher.utter_message(text="No policy type selected")
            return []

def prompt_engineering(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
    )
    return response.choices[0].text

class ActionSelectFlexibleWorkOption(Action):

    def name(self) -> Text:
        return "action_select_flexible_work_option"
    

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        flexible_work_option = tracker.get_slot('flexible_work_option')
        option = tracker.get_slot('option').split('_')
        option = ' '.join(option[1:])
        hr_policy_type = tracker.get_slot('hr_policy_type')
        job_type = f'{hr_policy_type} for {option} work'
        selected_policy = tracker.get_slot('policy_name')
        flexible_work_option = predefined_questions[selected_policy].get(flexible_work_option)
        prompt = PROMPT_TEMPLATE.format(job_type=job_type, flexible_work_option=flexible_work_option)
        questions = prompt_engineering(prompt=prompt)
        attachments = {
            "questions": questions,
            "payload": "question_list"
        }
        dispatcher.utter_attachment(attachments=attachments)
        # dispatcher.utter_message(text=f"You have selected: {flexible_work_option}")
        return []
        # return [SlotSet('flexible_work_option', flexible_work_option)]


class ActionGetQuestions(Action):
    def name(self) -> Text:
        return "action_get_questions"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        questions = flexible_questions["question"]
        return [{"questions": questions}]



# class QuestionForm(FormValidationAction):
#     def name(self) -> Text:
#         return "question_form"
    
#     user_response = []

#     async def required_slots(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Text]:

#         questions = tracker.get_slot("questions")
#         if not questions:
#             return ["questions"]
#         else:
#             next_question_index = len(tracker.get_slots()) - 1
#             if next_question_index < len(questions):
#                 return [f"question_{next_question_index + 1}"]
#             else:
#                 return []

#     def submit(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         answers = tracker.current_state()['slots']
#         self.user_response.append(answers)
#         dispatcher.utter_message(text=answers)
#         return []


# class QuestionForm(FormValidationAction):
#     def name(self):
#         return "question_form"
    
#     def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
#         return {
#             "response0": self.from_text(),
#             "response1": self.from_text(),
#             "response2": self.from_text(),
#             "response3": self.from_text(),
#             "response4": self.from_text(),
#             "response5": self.from_text(),
#             "response6": self.from_text(),
#             "response7": self.from_text(),
#             "response8": self.from_text(),
#             "response9": self.from_text()
#         }

class ValidateQuestionForm(FormValidationAction):
    def name(self):
        return "validate_question_form"

    def validate_response0(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        response = tracker.get_slot("response0")

        if response:
            return {"response0": response}
        else:
            dispatcher.utter_message(text="Please enter a valid value.")
            return {"response0": None}
    
    # def validate_response1(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response1")

    #     if response:
    #         return {"response1": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response1": None}
    
    # def validate_response2(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response2")

    #     if response:
    #         return {"response2": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response2": None}
    
    # def validate_response3(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response3")

    #     if response:
    #         return {"response3": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response3": None}
    
    # def validate_response4(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response4")

    #     if response:
    #         return {"response4": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response4": None}
    
    # def validate_response5(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response5")

    #     if response:
    #         return {"response5": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response5": None}
        
    # def validate_response6(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response6")

    #     if response:
    #         return {"response6": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response6": None}
    
    # def validate_response7(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response7")

    #     if response:
    #         return {"response7": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response7": None}
        
    # def validate_response8(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response8")

    #     if response:
    #         return {"response8": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response8": None}
    
    # def validate_response9(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     response = tracker.get_slot("response9")

    #     if response:
    #         return {"response9": response}
    #     else:
    #         dispatcher.utter_message(text="Please enter a valid value.")
    #         return {"response9": None}
    

    # def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
    #     questions = flexible_questions["question"]
    #     question_index = tracker.get_slot("question_index") or 0
    #     responses = tracker.get_slot("user_response") or []

    #     if question_index < len(questions):
    #         current_question = questions[question_index]
    #         dispatcher.utter_message(text=current_question)
            
    #         question_index += 1
            
    #         return [SlotSet("question_index", question_index),
    #                 SlotSet("user_response", None)]
    #     else:
    #         dispatcher.utter_message(text="Thank you for answering all the questions!")
            
    #         return [SlotSet("question_index", None)]
        


class ActionStoreResponse(Action):
    def name(self):
        return "action_store_response"
    
    def save_pdf(self, response):
        response = response
        question = flexible_questions["question_list"]
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Policy Questions and Responses", ln=True, align='C')
        for num in range(10):
            pdf.multi_cell(200, 10, txt=question[str(num)], align='L')
            pdf.multi_cell(200, 10, txt= "Ans:" + response[num], align='L')
        pdf.output("Policy_Questions_and_Responses.pdf")
         
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # for num in range(10):
            # user_response = tracker.get_slot(f"response{num}")
            # response.append(user_response)
        dispatcher.utter_message(text="Your responses are recorded")
        response = tracker.get_slot("response")
        self.save_pdf(response)

        dispatcher.utter_message(text="Saved in 'Policy_Questions_and_Responses.pdf' file!!!")
        return []

with open('actions/flexible_questions.json', 'r') as file:
    flexible_questions = json.load(file)

class ActionSetQuestion(Action):
    def name(self) -> str:
        return "action_set_question"
    

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        question_list = {
                            "0": "How will the mandatory core period be enforced, and what tools or systems will be used to track employee hours?",
                            "1": "What provisions will be made for employees in different time zones, and how will this impact the mandatory core period?",
                            "2": "How will the policy accommodate employees with varying personal responsibilities, such as childcare or eldercare?",
                            "3": "What are the expectations for employee availability during the mandatory core period, and how will this be communicated?",
                            "4": "How will the policy handle requests for exceptions or adjustments to the core hours due to unforeseen circumstances?",
                            "5": "What guidelines will be provided for team meetings, collaboration, and communication within the flexible hours framework?",
                            "6": "How will the policy ensure that flexible hours do not negatively impact productivity, team cohesion, or project deadlines?",
                            "7": "What measures will be taken to ensure that employees do not feel pressured to work outside their chosen hours or beyond the core period?",
                            "8": "What are the legal implications of implementing flexible hours, and how does the policy comply with local labor laws and regulations?",
                            "9": "How will performance be evaluated for employees working flexible hours, and what criteria will be used to ensure fairness?"
                        }
        index = int(tracker.get_slot("question_index"))
        question_index = str(index)
        if index >= len(question_list):
            return [FollowupAction("action_store_response")]
        else:
            return [SlotSet("question0", question_list[question_index]),
                    SlotSet("question_index", index + 1),
                    FollowupAction("action_form")]
    
class ActionActivateForm(Action):
    def name(self):
        return "action_form"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:        
        return [Form("question_form")]#,
                # FollowupAction("action_custom_fallback")]
    
        # return [SlotSet("question0", question_list[0]),
        #         SlotSet("question1", question_list[1]),
        #         SlotSet("question2", question_list[2]),
        #         SlotSet("question3", question_list[3]),
        #         SlotSet("question4", question_list[4]),
        #         SlotSet("question5", question_list[5]),
        #         SlotSet("question6", question_list[6]),
        #         SlotSet("question7", question_list[7]),
        #         SlotSet("question8", question_list[8]),
        #         SlotSet("question9", question_list[9]),
        #         Form("question_form")]
    
class actionCustomFallback(Action):
    def name(self):
        return "action_custom_fallback"       
        
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any])  -> List[Dict[Text, Any]]:
        # prompt = """You are a helpful, trustworthy and informative medical assistant named 'Angela'. Please follow the following guidelines:
        #                 1. Angela should respond users query helping user to understand their health concerns and navigate users towards appropriate resources. 
        #                 2. Angela can provide general health information and symptom assessment, Angela cannot diagnose illnesses or prescribe medications.
        #                 3. Angela should reply in a short and precise content imitating real human-like conversations.
        #                 4. Angela emphasizes the importance of consulting a doctor or pharmacist for medication advice.
        #                 5. Angela avoids providing specific dosages to prevent misuse.
        #                 6. Angela can offer general information about side effects while directing the user to reliable sources like medication leaflets and healthcare professionals. 
        #                 7. Angela can not assist with any non-medical query. 
        #                 8. Angela should only give relevant information only.
        #          """

        # try:
        #     user_query = tracker.latest_message['text']
        #     response = client.chat.completions.create(
        #         model = "gpt-4o",
        #         messages=[
        #             {"role": "system", "content": prompt},
        #             {"role": "user", "content": "What's the best medication for my cough?"},
        #             {"role": "assistant", "content": "I understand you're looking for relief from your cough. While I can't recommend specific medications, I suggest consulting a doctor if your cough persists."},
        #             {"role": "user","content": user_query}
        #         ]
        #     )
        #     data = response.choices[0].message.content
        #     attachment = {
		#     	"query_response": data,
		#     	"data":[],
		#     	"type":"normal_message",
		#     	"data_fetch_status": "success"
		#     }
        # except Exception as e:
        #     data = "Can you rephrase it."
        #     attachment = {
		#     	"query_response": data,
		#     	"data":[],
		#     	"type":"normal_message",
		#     	"data_fetch_status": "failed"
		#     }
        # dispatcher.utter_message(attachment=attachment)
        user_response = tracker.latest_message['text']

        if tracker.get_slot("response"):
            updated_response = tracker.get_slot("response") + [user_response]
        else:
            updated_response = tracker.latest_message['text']
        print(user_response, updated_response)
        
        return [SlotSet("response", updated_response),
                SlotSet("response0", None),
                FollowupAction("action_set_question")]


