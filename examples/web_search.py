from pendulum import Date
from Noema import *
from capabilities import *

class WebSearch(Noesis):
    
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
        date = Date.today().format("YYYY-MM-DD")
        current_date:Information = f"The current date is: {date}"
        knowledge_reflexion:Fill = ("Thinking about the task.",
                                f"""I have to think about the task: '{task.value}'.
                                Based on the date and my knowledge, can I Know the answer? {Bool:known_answer}.
                                """)
        if knowledge_reflexion.known_answer:
            answer:Sentence = "Producing the answer."
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
answer,source = WebSearch("What is the population of France?").constitute(subject)
print("\n\n")
print(subject)
print("\n\n")
print(answer)
print(source)
