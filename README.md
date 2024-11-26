<p align="center">
  <img src="logoNoema.jpg" alt="ReadMe Banner"/>
</p>


**Noema is a new way of programming, using seamless integration between python and llm's generations.**

# Background:

**Noema is an application of the [*declarative* programming](https://en.wikipedia.org/wiki/Declarative_programming) paradigm to a langage model.** 

With Noema, you can control the model and choose the path it will follow. This framework aims to enable developpers to use **LLM as a though interpretor**, not as a source of truth.

Noema is built on [llamacpp](https://github.com/ggerganov/llama.cpp) and [guidance](https://github.com/guidance-ai/guidance)'s shoulders.


- [Concept](#Concept)
- [Installation](#installation)
- [Features](#features)


## Concept

- **Noesis**: can be seen as the description of a function
- **Noema**: is the representation (step by step) of this description
- **Constitution**: is the process of transformation Noesis->Noema.
- **Subject**: the object producing the Noema via the constitution of the noesis. Here, the LLM.

**Noema**/**Noesis**, **Subject**, and **Constitution** are a pedantic and naive application of concept borrowed from [Husserl's phenomenology](https://en.wikipedia.org/wiki/Edmund_Husserl).


## ReAct prompting:
We can use ReAct prompting with LLM.

`ReAct` prompting is a powerful way for guiding a LLM.

### ReAct example:
```You are in a loop of though.
Question: Here is the question 
Reflexion: Thinking about the question
Observation: Providing observation about the Reflexion
Analysis: Formulating an analysis about your current reflexion
Conclusion: Conclude by a synthesis of the reflexion.

Question: {user_input}
Reflexion:
```

In that case, the LLM will follow the provided steps: `Reflexion,Observation,Analysis,Conclusion`

`Thinking about the quesion` is the **Noesis** of `Reflexion`

The content *generated* by the LLM corresponding to `Reflexion` is the **Noema**.

### Noema let you write python code that automagically:
1. Build the ReAct prompt
2. Let you intercepts (constrained) generations
3. Use it in standard python code

# Full example:
```python
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
            search_results = google_search(task.value) # contained in capabilities module
            results:Information = f"The search results are: {search_results}"
            manage_results:Fill = ("Managing the search results.",
                                    f"""Selecting the best result: {SubString:infos}.
                                    Extracting the best link: {SubString:link}
                                    Producing the answer based on the information: {Sentence:answer}.
                                    """)
            elaborate:Paragraph = "Using the information of the selected result, I elaborate the answer."
            return elaborate.value, manage_results.link
            
subject = Subject("path/to/your/model.gguf")
answer,source = WebSearch("What is the population of France?").constitute(subject)

print(answer) 
# The current population of France is 66,589,408 as of Sunday, November 24, 2024, based on Worldometer's elaboration of the latest United Nations data1.
print(source)
# 'https://www.worldometers.info/world-population/france-population/'
```

# Usage:
## Installation

```bash
pip install Noema
```

## Features

### Create the Subject

```python
from Noema import *

subject = Subject("path/to/your/model.gguf") # Full Compatibiliy with LLamaCPP.
```

### Create a way of thinking: 

#### 1. Create a class that inherits from Noesis
#### 2. Add a method named `description`
#### 3. Add a system prompt using the python docstring
#### 4. Write python code


```python
from Noema import *

subject = Subject("path/to/your/model.gguf")

class WayOfThinking(Noesis):
    
    def description(self):
        """
        Here write the system prompt, describing the role/task of the system.
        In the same way as for a classical prompt, you can use multiline.
        """
        task_list = ["Task description 1", "Task description 2"]
        reflexions = []
        for task_description in task_list:
            task:Information = f"{task_description}" # Insert description
            thought:Fill = ("""Thinking about the task.
                            Here you can write the different steps of the thought process.
                            1. Step 1: I do this.
                            2. Step 2: I do that.
                            3. Step 3: I do this other thing.
                            """,
                            f"""Step 1: {Sentence:step1}
                            Step 2: {Sentence:step2}
                            Step 3: {Sentence:step3}
                            """)
            print(thought.step1) # easy access to the though variables (step1,step2,step3)
            reflexion:Paragraph = "Here you can write a reflexion about the thought process."
            reflexions.append(reflexion.value)
        return reflexions

wot = WayOfThinking()
reflexions = wot.constitute(subject)
print(reflexions) # contains the reflexions produced by the LLM
```

## Generators
Generators are used to generate content from the subject (LLM) through the noesis (the task description).

They always produce the corresponding python type.

### Simple Generators

| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| Int  | int  | `number:Int = "Give me a number between 0 and 10"`  |
| Float  | float  | `number:Float = "Give me a number between 0.1 and 0.7"`  |
| Bool  | bool  | `truth:Bool = "Are local LLMs better than online LLMs?"`  |
| Word  | str  | `better:Word = "Which instruct LLM is the best?"`  |
| Sentence  | str  | `explaination:Sentence = "Explain why"`  |
| Paragraph  | str  | `long_explaination:Paragraph = "Give mode details"`  |

### Example:
```python
class WayOfThinking(Noesis):
    
    def description(self):
        """
        You are a nice assistant.
        """
        found = False
        hello:Word = "Say 'hello' in French"
        while(not found):
            nb_letter:Int = f"How many letter in {hello.value}"
            verification:Bool = f"Does {hello.value} really contains {nb_letter.value} letters?"
            if verification.value:
                print("Verification done!")
                found = True

        return hello.value, nb_letter.value

wot = WayOfThinking()
reflexions = wot.constitute(subject, verbose=True)
print(reflexions)
```

### Composed generators

List of simple Generators can be built.
| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| IntList  | [int]  | `number:IntList = "Give me a list of number between 0 and 10"`  |
| FloatList  | [float]  | `number:FloatList = "Give me a list of number between 0.1 and 0.7"`  |
| BoolList  | [bool]  | `truth:BoolList = "Are local LLMs better than online LLMs, and Mistral better than LLama?"`  |
| WordList  | [str]  | `better:WordList = "List the best instruct LLM"`  |
| SentenceList  | [str]  | `explaination:SentenceList = "Explain step by step why"`  |


### Fill-in-the-blanks generator
| Noema Type | Python Type 
|-----------|-----------|
| Fill  | {key:value}  | 

```python
though:Fill = ("Categorizing user comment",
                """The user language is {Word:language}
                From a psychologist point of view, this comment is {Sentence:psycho}"""

# Property are added to though
# though.language 
# thought.psycho
```


### Reflexion generator:

Reflexion generators provide a simple way to make the LLM *think* about something.

| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| Reflexion  | str  | `builder:Reflexion = "How to build a house in the forest?"`  |

It will follow an *abstract thinking* prompt:

```
[INST]How to build a house in the forest?
 Follow these steps of reasoning, using a loop to determine whether the process should continue or if the reflection is complete:
1. Initial Hypothesis: Provide a first answer or explanation based on your current knowledge.
2. Critical Analysis: Evaluate the initial hypothesis. Look for contradictions, weaknesses, or areas of uncertainty.
3. Conceptual Revision: Revise or improve the hypothesis based on the critiques from the Critical Analysis.
4. Extended Synthesis: Develop a more complete and nuanced response by incorporating additional perspectives or knowledge.
5. Loop or Conclusion: Return to the Decision Point. If the answer is now coherent and well-justified, you repond 'satisfying' and move to the Conclusion. If further refinement is needed, respond 'loop again' and go to the Critical Analysis. 
6. Final Conclusion: Once the reflection is considered complete, provide a final answer, clearly explaining why this response is coherent and well-justified, summarizing the key steps of the reasoning process.
7. Quality of the reflection: Provide a quality assessment of the reflection process. 
Done.
[/INST]
```

### Information

The type Information is useful to insert some context to the LLM at the right time in the reflexion process.

| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| Information  | str  | `tips:Information = "Here you can inject some information in the LLM"`  |

Here we use a simple string, but we can also insert a string from a python function call, do some RAG or any other tasks.

## Noesis / Noema / Value

Every generator as the following properties by default:
```python
from Noema import *

subject = Subject("path/to/your/model.gguf")

class WayOfThinking(Noesis):
    
    def description(self):
        """
        You are a specialist in nice house building.
        """
        builder:Reflexion = "How to build a house in the forest?"
        print("Noesis:")
        print(builder.noesis)
        print("-"*50)
        print("Noema:")
        print(builder.noema)
        print("-"*50)
        print("Value:")
        print(builder.value)
        print("-"*50)

WayOfThinking().constitute(subject)
```

Produce the following output:

```
Noesis:
How to build a house in the forest?
--------------------------------------------------
Noema:

        ***Initial Hypothesis: To build a house in the forest, you need to find a suitable location, clear the area of trees and debris, and then construct the house using materials such as wood, stone, and metal. You may also need to consider factors such as water supply, electricity, and waste disposal.
While this initial hypothesis provides a general outline of the process, it lacks specific details and considerations. For example, it does not address the importance of selecting a location with good drainage to prevent flooding, or the need to obtain necessary permits and approvals from local authorities.
To build a house in the forest, you should first research and select a suitable location, taking into account factors such as soil type, drainage, and proximity to water sources. You should also obtain necessary permits and approvals from local authorities. Once you have a clear plan, you can begin clearing the area of trees and debris, and then construct the house using sustainable materials such as wood, stone, and metal. You should also consider installing a water filtration system, a solar-powered electricity system, and a composting toilet to minimize your impact on the environment.
Building a house in the forest requires careful planning and consideration of environmental factors. You should research and select a location that is suitable for building, taking into account factors such as soil type, drainage, and proximity to water sources. You should also obtain necessary permits and approvals from local authorities. Once you have a clear plan, you can begin clearing the area of trees and debris, and then construct the house using sustainable materials such as wood, stone, and metal. You should also consider installing a water filtration system, a solar-powered electricity system, and a composting toilet to minimize your impact on the environment. Additionally, you may want to consider building a greenhouse or garden to grow your own food and reduce your reliance on outside resources.
loop again
Building a house in the forest requires careful planning and consideration of environmental factors. You should research and select a suitable location, taking into account factors such as soil type, drainage, and proximity to water sources. You should also obtain necessary permits and approvals from local authorities. Once you have a clear plan, you can begin clearing the area of trees and debris, and then construct the house using sustainable materials such as wood, stone, and metal. You should also consider installing a water filtration system, a solar-powered electricity system, and a composting toilet to minimize your impact on the environment. Additionally, you may want to consider building a greenhouse or garden to grow your own food and reduce your reliance on outside resources. This response is coherent and well-justified because it takes into account the importance of selecting a suitable location, obtaining necessary permits and approvals, and using sustainable materials and systems to minimize the impact on the environment.
Reflexion loop completed.
--------------------------------------------------
Value:
Building a house in the forest requires careful planning and consideration of environmental factors. You should research and select a suitable location, taking into account factors such as soil type, drainage, and proximity to water sources. You should also obtain necessary permits and approvals from local authorities. Once you have a clear plan, you can begin clearing the area of trees and debris, and then construct the house using sustainable materials such as wood, stone, and metal. You should also consider installing a water filtration system, a solar-powered electricity system, and a composting toilet to minimize your impact on the environment. Additionally, you may want to consider building a greenhouse or garden to grow your own food and reduce your reliance on outside resources. This response is coherent and well-justified because it takes into account the importance of selecting a suitable location, obtaining necessary permits and approvals, and using sustainable materials and systems to minimize the impact on the environment.

--------------------------------------------------
```