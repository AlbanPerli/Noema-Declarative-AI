from .generators import *
from .step import ReflexiveStep

class AutoCritic(ReflexiveStep):
    
    def __init__(self):
        super().__init__("", "", output_type="A sentence representing the reflexion.")
        
    def execute(self, state):
        super().execute(state)
        
        prompt = f"""[INST]You are a specialist in self-reflection.
Here is a reflection plan that you have to analyze:
{state.noesis}
--------------------------
Here is the resulting reasonning process:
{state.noema}  
--------------------------

Be critical using a this loop to determine whether the produced reflection is coherent and well-justified:
1. Analyse the reflection plan: Provide a first analysis of the reasoning process.
2. Reflection plan critical Analysis: Evaluate the reflection plan. Look for contradictions, weaknesses, or areas of uncertainty.
3. Analyse the reflection produced: Evaluate the reflection. Look for contradictions, weaknesses, or areas of uncertainty.
4. Produced reflexion critical Analysis: Evaluate the reflection. Look for contradictions, weaknesses, or areas of uncertainty.
5. Conceptual Revision: Revise or improve the hypothesis based on the critiques from the Produced reflexion critical analysis.
6. Extended Synthesis: Develop a more complete and nuanced response by incorporating additional perspectives or knowledge.
7. Change of Perspective: Consider a different angle or approach to the reflection.
8. Thinking with Others: Consider how others might view the reflection or what additional perspectives they might offer.
9. Thinking wider: Consider how the reflection should be expanded or refined.
10. Final Conclusion: provide a final answer critically explaining why this reasoning process is coherent and well-justified or if it needs further refinement. Justify your response.
11. Updated Reflection Plan: Provide a final reflection plan based on the reasoning process in the following format: 
    1. Plan step name: Plan step value.
    2. Plan step name: Plan step value.
    ...
Done.
[/INST]

"""
        state.update_noesis(f"""{self.display_step_name} Apply Auto-critic loop on: '{self.current_llm_input}'""")
        state.update_noema(f"""{self.display_step_name} Start Auto-critic loop on: '{self.current_llm_input}'""")
        
        print(prompt)
        tmp_copy = str(state.llm)
        lm = state.llm
        lm += prompt + "1. Analyse the reflection plan:" + gen(name="reflexion",stop=["2. Reflection plan critical Analysis:"]) 
        print("Analyse the reflection plan: " + lm["reflexion"].strip())
        lm += "2. Reflection plan critical Analysis:" +gen(name="critic",stop=["3. Analyse the reflection produced:"])
        print("Reflection plan critical Analysis: " + lm["critic"].strip())
        lm += "3. Analyse the reflection produced:" +gen(name="reflexion",stop=["4. Produced reflexion critical Analysis:"])
        print("Analyse the reflection produced: " + lm["reflexion"].strip())
        lm += "4. Produced reflexion critical Analysis:" +gen(name="critic",stop=["5. Conceptual Revision:"])
        print("Produced reflexion critical Analysis: " + lm["critic"].strip())
        counter = 5
        loop_count = 0
        while True:
            lm += f"{counter}. Conceptual Revision: " 
            counter += 1
            lm += gen(name="conceptual",stop=[f"{counter}. Extended Synthesis:"]) 
            print("Conceptual Revision: " + lm["conceptual"].strip())
            
            
            lm += f"{counter}. Extended synthesis: "
            counter += 1
            lm += gen(name="synthesis",stop=[f"{counter}. Change of Perspective:"])
            print("Extended synthesis: " + lm["synthesis"].strip())
            
            lm += f"{counter}. Change of Perspective: "
            counter += 1
            lm += gen(name="perspective",stop=[f"{counter}. Thinking with Others:"])
            print("Change of Perspective: " + lm["perspective"].strip())
            
            lm += f"{counter}. Thinking with Others: "
            counter += 1
            lm += gen(name="thinking",stop=[f"{counter}. Thinking wider:"])
            print("Thinking with Others: " + lm["thinking"].strip())
            
            lm += f"{counter}. Thinking wider: "
            counter += 1
            lm += gen(name="wider",stop=[f"{counter}. Final Conclusion:"])
            print("Thinking wider: " + lm["wider"].strip())

            lm += f"{counter}. Final Conclusion:" 
            counter += 1
            lm += gen(name="finished",stop=[f"{counter}. Updated Reflection Plan:"])
            print(f"{counter}. Final Conclusion: " + lm["finished"])
            break
        
        # lm += f"{counter}. Updated Reflection Plan:" + gen(name="response",stop=["Done."])
        # print(f"{counter}. Updated Reflection Plan: " + lm["response"])
        state.update_noema("Auto-critic loop completed.")
        reflexion_value = lm["finished"]
        lm.reset()
        state.llm += tmp_copy + f"\n{self.display_step_name}: {reflexion_value}\n"
        return reflexion_value
    
    def list_steps(self,state):
        return [self.display_step_name+" "+self.value] if self.should_include_in_list() else []
