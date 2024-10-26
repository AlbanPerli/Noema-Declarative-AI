from .generators import *
from .step import ReflexiveStep

class Reflexion(ReflexiveStep):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(value, dest, output_type="A sentence representing the reflexion.")
        self.value = value
        self.reflexion_var = dest
        
    def execute(self, state):
        super().execute(state)
        state.update_noesis(f"""{self.display_step_name} Apply reflexion loop on: '{self.current_llm_input}'""")
        state.update_noema(f"""{self.display_step_name} Start reflexion loop on: '{self.current_llm_input}'""")
        
        prompt = f"""[INST]For the following question: {self.current_llm_input}, follow these steps of reasoning, using a loop to determine whether the process should continue or if the reflection is complete:
1. Initial Hypothesis: Provide a first answer or explanation based on your current knowledge.
2. Critical Analysis: Evaluate the initial hypothesis. Look for contradictions, weaknesses, or areas of uncertainty.
3. Decision Point: Is the current response coherent, clear, and sufficiently justified? If yes, proceed to the conclusion. If no, continue to the next step.
4. Conceptual Revision: Revise or improve the hypothesis based on the critiques from the Critical Analysis.
5. Extended Synthesis: Develop a more complete and nuanced response by incorporating additional perspectives or knowledge.
6. Loop or Conclusion: Return to the Decision Point. If the answer is now coherent and well-justified, you repond 'satisfying' and move to the Conclusion. If further refinement is needed, respond 'loop again' and repeat the loop. 
7. Final Conclusion: Once the reflection is considered complete, provide a final answer, clearly explaining why this response is coherent and well-justified, summarizing the key steps of the reasoning process.
Done.
[/INST]

"""
        print(self.current_llm_input)
        tmp_copy = str(state.llm)
        lm = state.llm
        lm += prompt + "1. Initial Hypothesis: " + gen(name="reflexion",stop=["2. Critical Analysis:"]) 
        state.update_noema("        ***Initial Hypothesis: " + lm["reflexion"].strip())
        lm += "2. Critical Analysis:" +gen(name="critic",stop=["3. Decision Point:"]) 
        state.update_noema("        ***Critical Analysis: " + lm["critic"].strip())
        counter = 3
        loop_count = 0
        while True:
            lm += f"{counter}. Decision Point:" + capture(select(['yes', 'no']),name="decision") 
            counter += 1
            if lm["decision"] == "yes":
                lm += f"{counter}. Final Conclusion: " + gen(name="response",stop=["Done.","\n"])
                state.update_noema("        ***Final Conclusion: " + lm["response"].strip())
                break
            else:
                lm += f"{counter}. Conceptual Revision: " 
                state.update_noema("        ***Conceptual Revision: " + lm["reflexion"].strip())
                counter += 1
                lm += gen(name="conceptual",stop=[f"{counter}. Extended Synthesis:"]) 
                state.update_noema("        ***Extended Synthesis: " + lm["conceptual"].strip())
                counter += 1
                lm += f"{counter}. Extended Synthesis: " 
                counter += 1
                lm += gen(name="synthesis",stop=[f"{counter}. Loop or Conclusion:"]) 
                state.update_noema("        ***Extended Synthesis: " + lm["synthesis"].strip())
                counter += 1
                lm += f"{counter}. Loop or Conclusion: " 
                counter += 1
                lm += capture(select(['satisfying', 'loop again']),name="finished")
                state.update_noema("        ***Loop or Conclusion: " + lm["finished"].strip())
                loop_count += 1
                if loop_count >= 5:
                    lm += f"{counter}. Final Conclusion: " + gen(name="response",stop=["Done.","\n"])
                    state.update_noema("        ***Final Conclusion: " + lm["response"].strip())
                    break
        state.update_noema("Reflexion loop completed.")
        reflexion_value = lm["response"]
        state.set_prop(self.reflexion_var, reflexion_value)
        lm.reset()
        state.llm += tmp_copy + f"\n{self.display_step_name}: {reflexion_value}\n"
        return reflexion_value
    
    def list_steps(self,state):
        return [self.display_step_name+" "+self.value] if self.should_include_in_list() else []
