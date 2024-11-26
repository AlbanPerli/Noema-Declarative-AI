from Noema import *

class MailCreator(Noesis):
    
    def description(self):
        """
        You have to find the adress mail of a person.
        """
        email_list = []
        task:Information = "The person is called Jean Dupont."
        for i in range(4):
            if thought.strategy != None:
                last_strategy:Information = f"{thought.strategy}"
            
            thought:Fill = ("""Thinking about a new strategy.
                            Reformulate the strategy: I reformulate the strategy.
                            Criticize the strategy: I criticize the strategy.
                            Define a new strategy: I define a new strategy.
                            Conclusion: here, I provide a conclusion, synthesizing the strategy.""",
                            f"""Reformulate the strategy: {Sentence:reformulation}
                            Criticize the strategy: {Sentence:criticism}
                            Define a new strategy: {Sentence:definition}
                            Conclusion: {Sentence:strategy}
                            """)
            reflexion:Paragraph = "Thinking about a new strategy, describing why and how it is different from the previous one."
            email:Email = f"Writing a new possible gmail adress based on the strategy. The email is different from the previous one."
            email_list.append(email.value)
            print(thought.noema)
            
        return email_list
                   
subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")
emails = MailCreator().constitute(subject, verbose=True)
print("\n\n")
print(emails)

