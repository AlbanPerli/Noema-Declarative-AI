from datetime import date
from Noema import *
from capabilities import *

class WebSearch(Noema):
    
    def __init__(self,request):
        super().__init__()
        self.request = request
    
    def description(self):
        """
        You are a specialist in information retrieval.
        Always looking for the best information to answer a question.
        If you don't know the answer, you are able to find it by searching on the web.
        """
        task:Information = f"{self.request}"
        current_date = date.today().strftime("%d-%m-%Y")
        current_date_info:Information = f"The current date is: {current_date}"
        knowledge_reflexion:Fill = ("Thinking about the task.",
                                f"""I have to think about the task: '{task.value}'.
                                Based on the date and my knowledge, can I Know the answer? {Bool:known_answer}.
                                """)
        if knowledge_reflexion.known_answer:
            answer:Sentence = "Producing the answer."
            return answer,None
        else:
            search_results = google_search(task.value)
            results:Information = f"The search results are: {search_results}"
            manage_results:Fill = ("Managing the search results.",
                                    f"""Selecting the best result: {SubString:infos}.
                                    Extracting the best link: {SubString:link}
                                    Producing the answer based on the information: {Sentence:answer}.
                                    """)
            elaborate:Paragraph = "Using the information of the selected result, I elaborate the answer."
            return elaborate.value, manage_results.link
            
subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")
answer,source = WebSearch("What is the population of France?").constitute(subject, verbose=True)

print(answer) 
print(source)