
from guidance import models, gen, select, capture
from Noema._Generator import Generator
from Noema._ListGenerator import ListGenerator
from Noema._patternBuilder import PatternBuilder
from Noema.cfg import G

class Reflexion(Generator):
    
    def __init__(self, ):
        pass
    
    def execute(self, noesis_model, state):
        noema = ""
        prompt = f"""[INST]For the following question: {noesis_model.value}, follow these steps of reasoning, using a loop to determine whether the process should continue or if the reflection is complete:
1. Initial Hypothesis: Provide a first answer or explanation based on your current knowledge.
2. Critical Analysis: Evaluate the initial hypothesis. Look for contradictions, weaknesses, or areas of uncertainty.
3. Decision Point: Is the current response coherent, clear, and sufficiently justified? If yes, proceed to the conclusion. If no, continue to the next step.
4. Conceptual Revision: Revise or improve the hypothesis based on the critiques from the Critical Analysis.
5. Extended Synthesis: Develop a more complete and nuanced response by incorporating additional perspectives or knowledge.
6. Loop or Conclusion: Return to the Decision Point. If the answer is now coherent and well-justified, you repond 'satisfying' and move to the Conclusion. If further refinement is needed, respond 'loop again' and repeat the loop. 
7. Final Conclusion: Once the reflection is considered complete, provide a final answer, clearly explaining why this response is coherent and well-justified, summarizing the key steps of the reasoning process.
Done.

Reflexion output: Provide an output based on the final conclusion, should be formatted as a {noesis_model.type}.
[/INST]

"""
        # print(prompt)
        lm = state.llm
        lm += prompt + "1. Initial Hypothesis: " + gen(name="reflexion",stop=["2. Critical Analysis:"]) 
        noema += "\n        ***Initial Hypothesis: " + lm["reflexion"].strip()
        # print("Initial Hypothesis:", lm["reflexion"])
        lm += "2. Critical Analysis:" +gen(name="critic",stop=["3. Decision Point:"]) 
        # print("Critical Analysis:", lm["critic"])
        noema += "\n        ***Critical Analysis: " + lm["critic"].strip()
        counter = 3
        loop_count = 0
        while True:
            lm += f"{counter}. Decision Point:" + capture(select(['yes', 'no']),name="decision") 
            # print("Decision Point: ", lm["decision"])
            counter += 1
            if lm["decision"] == "yes":
                lm += f"{counter}. Final Conclusion: " + gen(name="response",stop=["Done.","\n"])
                noema += "\n        ***Final Conclusion: " + lm["response"].strip()
                break
            else:
                lm += f"{counter}. Conceptual Revision: " 
                counter += 1
                lm += gen(name="conceptual",stop=[f"{counter}. Extended Synthesis:"]) 
                noema += "\n        ***Conceptual Revision: " + lm["conceptual"].strip()
                # print("Conceptual Revision: ", lm["conceptual"])
                lm += f"{counter}. Extended Synthesis: " 
                counter += 1
                lm += gen(name="synthesis",stop=[f"{counter}. Loop or Conclusion:"]) 
                noema += "\n        ***Extended Synthesis: " + lm["synthesis"].strip()
                # print("Extended Synthesis: ", lm["synthesis"])
                lm += f"{counter}. Loop or Conclusion: " 
                lm += capture(select(['satisfying', 'loop again']),name="finished")
                noema += "\n        ***Loop or Conclusion: " + lm["finished"].strip()
                # print("Loop or Conclusion: ", lm["finished"])
                if lm["finished"] == "satisfying":
                    lm += f"{counter}. Final Conclusion: " + gen(name="response",stop=["Done.","\n"])
                    noema += "\n        ***Final Conclusion: " + lm["response"].strip()
                    break
                loop_count += 1
                if loop_count >= 5:
                    lm += f"{counter}. Final Conclusion: " + gen(name="response",stop=["Done.","\n"])
                    noema += "\n        ***Final Conclusion: " + lm["response"].strip()
                    break
        noema += "\nReflexion loop completed."
        
        if 'list' in noesis_model.type:
            atomic_type = noesis_model.type.split("[")[1].split("]")[0]
            python_type = None
            if atomic_type == "Int":
                python_type = int
                lm += f"Reflexion output: " + capture(G.arrayOf(G.word()), name="formatted_response")
            if atomic_type == "Sentence":
                python_type = str
                lm += f"Reflexion output: " + capture(G.arrayOf(G.alphaNumPunctForSentence()), name="formatted_response")
            if atomic_type == "Word":
                python_type = str
                lm += f"Reflexion output: " + capture(G.arrayOf(G.word()), name="formatted_response")
            if atomic_type == "Float":
                python_type = float
                lm += f"Reflexion output: " + capture(G.arrayOf(G.float()), name="formatted_response")
            if atomic_type == "Bool":
                python_type = bool
                lm += f"Reflexion output: " + capture(G.arrayOf(G.bool()), name="formatted_response")
            
            res = lm["formatted_response"]
            state.llm += noesis_model.display_var() + res + "\n"
            res = res[1:-1].split(",")
            res = [python_type(el.strip()[1:-1]) for el in res]
            return res,noema, prompt
        else:
            obj = PatternBuilder.instance().objects_by_type[noesis_model.type]()
            lm += f"Reflexion output: " + capture(obj.grammar, name="formatted_response")
            res = lm["formatted_response"]
            state.llm += noesis_model.display_var()+ " " + res + "\n"
            return obj.return_type(res),noema, prompt