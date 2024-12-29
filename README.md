<p align="center">
  <img src="logoNoema.jpg" alt="ReadMe Banner"/>
</p>


<div align="center"> 
<span style="font-size: 29px;">Seamless integration between python and llm's generations.</span>
<p><span style="font-size: 29px;">
With Noema, you can control the model and choose the path it will follow. 
<br>This framework aims to enable developpers to use **LLM as a though interpretor**, not as a source of truth.

Noema is built on [llamacpp](https://github.com/ggerganov/llama.cpp) and [guidance](https://github.com/guidance-ai/guidance)'s shoulders.
</span></p>
</div>

## Installation

```bash
pip install Noema
```


# Basic:
```python
from Noema import *

# Create a subject (LLM)
Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf", verbose=True) # Llama cpp model

# Create a way of thinking
class SimpleWayOfThinking:
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        
    @Noema
    def think(self):
        """
        You are a simple thinker. You have a task to perform.
        Always looking for the best way to perform it.
        """
        povs = []
        task = Information(f"{self.task}") # inject information to the LLM
        for i in range(4):
            step_nb = i + 1
            reflexion = Sentence("Providing a reflexion about the task.", step_nb)
            consequence = Sentence("Providing the consequence of the reflexion.", step_nb)
            evaluate = Sentence("Evaluating the consequence.", step_nb)
            point_of_view = Sentence(f"Providing a point of view about the task different than {povs}", step_nb)
            point_of_view_qualification = Word(f"Qualifying the point of view, must choose a word different of: {povs}", step_nb)
            povs.append(point_of_view_qualification.value)
            creativitity_level = Float(f"How creative is this point of view: {povs[-1]}. (Between 0-10)", step_nb)
            if creativitity_level.value < 8.0:
                important = Information("I need to be more creative!")
        conclusion = Paragraph("Providing a conclusion which is a synthesis of the previous steps.")
        return conclusion.value # return the conclusion value
    
 
swot = SimpleWayOfThinking("How to write a good iOS application?")
conclusion = swot.think()
print(conclusion)
```

<details>
  <summary>LLM output:</summary>

```
[INST]
You are a simple thinker. You have a task to perform.
Always looking for the best way to perform it.        

#TASK : f'{self.task}'
#REFLEXION : Providing a reflexion about the task. (Response format: a sentence)
#CONSEQUENCE : Providing the consequence of the reflexion. (Response format: a sentence)
#EVALUATE : Evaluating the consequence. (Response format: a sentence)
#POINT_OF_VIEW : f'Providing a point of view about the task different than {povs}' (Response format: a sentence)
#IMPORTANT : I need to be more creative!
#CONCLUSION : Providing a conclusion which is a synthesis of the previous steps. (Response format: a paragraph)
[/INST]

#TASK: How to write a good iOS application?
#REFLEXION_1: Writing an iOS app requires balancing user experience with technical feasibility, which can be daunting without a structured approach.
#CONSEQUENCE_1: Without a clear roadmap, developers might overlook critical aspects like usability or performance optimization, leading to a subpar product.
#EVALUATE_1: The consequence highlights the necessity for meticulous planning and iterative testing to ensure both functionality and user satisfaction.
#POINT_OF_VIEW_1: Instead of focusing solely on coding, consider adopting a design-first approach where user stories guide the development process, ensuring alignment between vision and execution.
#POINT_OF_VIEW_QUALIFICATION_1:  Designer 
#CREATIVITITY_LEVEL_1: 7.5
#IMPORTANT: I need to be more creative!
#REFLEXION_2: The challenge lies in translating abstract design concepts into tangible iOS applications, necessitating a deep understanding of both user needs and platform capabilities.
#CONSEQUENCE_2: Ignoring user feedback during development phases could result in an application that fails to meet market expectations and user expectations, potentially causing significant financial losses and damage to brand reputation.
#EVALUATE_2: Ignoring user feedback during development phases could lead to a product that fails to resonate with its target audience, undermining both commercial success and user trust.
#POINT_OF_VIEW_2: From a developer's perspective, integrating innovative features while maintaining robustness requires a blend of creativity and technical expertise, ensuring seamless integration of cutting-edge functionalities without compromising stability.
#POINT_OF_VIEW_QUALIFICATION_2:  Architect 
#CREATIVITITY_LEVEL_2: 8.2
#CONCLUSION: Crafting a successful iOS application necessitates a multifaceted approach that harmonizes creativity with rigorous planning and iterative refinement. By adopting a design-first methodology and integrating user feedback throughout development, developers can navigate the complexities of balancing innovation with practicality, ultimately delivering applications that not only meet but exceed user expectations, thereby fostering both user satisfaction and commercial success. Emphasizing creativity alongside meticulous planning ensures that each aspect of the development process contributes meaningfully to the final product's success.
```

</details>

# Background:

**Noema is an application of the [*declarative* programming](https://en.wikipedia.org/wiki/Declarative_programming) paradigm to a language model.** 

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

## Features

### Create the Subject

```python
from Noema import *

Subject("path/to/your/model.gguf", verbose=True) # Full Compatibiliy with LLamaCPP.
```

### Create a way of thinking: 

#### 1. Add @Noema decorator to a function/method.
```python
from Noema import *

Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf", verbose=True) # Llama cpp model

@Noema
def comment_evaluation(comment):
  pass
```
#### 2. Add a system prompt using the python docstring
```python
from Noema import *

@Noema
def comment_evaluation(comment):
  """
  You are a specialist of comment analysis.
  You always produce a deep analysis of the comment.
  """
```
#### 3. Write python code
```python
from Noema import *

@Noema
def comment_evaluation(comment):
  """
  You are a specialist of comment analysis.
  You always produce a deep analysis of the comment.
  """
  comment_to_analyse = Information(f"{comment}")
  specialists = ["Psychologist", "Product manager", "Satisfaction manager"]
  analyse_by_specialists = {}
  for specialist in specialists:
    analysis = Sentence(f"Analysing the comment as a {specialist}")
    analyse_by_specialists[specialist] = analysis.value
  
  synthesis = Paragraph("Providing a synthesis of the analysis.")
  return synthesis.value, analyse_by_specialists

Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf", verbose=True) # Llama cpp model

synthesis, abs = comment_evaluation("This llm is very good at following instructions!")

print(synthesis)
```

<details>
  <summary>LLM output:</summary>
[INST]

You are a specialist of comment analysis.
You always produce a deep analysis of the comment.
  

#COMMENT_TO_ANALYSE : f'{comment}'

#ANALYSIS : f'Analysing the comment as a {specialist}' (Response format: a sentence)

#SYNTHESIS : Providing a synthesis of the analysis. (Response format: a paragraph)

[/INST]

#COMMENT_TO_ANALYSE: This llm is very good!

#ANALYSIS: The comment expresses a positive sentiment towards the LLM's capabilities, suggesting satisfaction with its performance and possibly indicating a belief in its psychological sophistication or understanding of human interaction nuances.

#ANALYSIS: As a product manager, this feedback highlights the importance of user satisfaction and perceived intelligence in LLM evaluations, indicating a focus on enhancing user experience through advanced functionalities and addressing potential psychological aspects beyond mere functionality.

#ANALYSIS: The comment reflects high user satisfaction with the LLM's performance, emphasizing its perceived intelligence and nuanced understanding, which are critical factors for product managers aiming to meet user expectations and foster trust through advanced technological capabilities.

#SYNTHESIS: The comment underscores a significant positive reception of the LLM, highlighting its perceived intelligence and nuanced understanding beyond basic functionality. This feedback is crucial for product managers as it underscores the importance of aligning technological advancements with user expectations for psychological satisfaction and trust-building. Addressing these aspects could enhance user engagement and satisfaction, positioning the LLM as a valuable asset in meeting evolving technological and psychological needs within its applications. Future iterations should focus on maintaining and potentially elevating these perceived qualities to further solidify its role as a sophisticated tool in diverse user contexts.
</details>

## Generators
Generators are used to generate content from the subject (LLM) through the noesis (the task description).

Generated value always have 3 properties:
- var_name.value -> The generated value
- var_name.noesis -> The instruction
- var_name.noema -> The generated value

They always produce the corresponding python type.

### Simple Generators

| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| Int  | int  | `number = Int("Give me a number between 0 and 10")`  |
| Float  | float  | `number = Float("Give me a number between 0.1 and 0.7")`  |
| Bool  | bool  | `truth:Bool = Bool("Are local LLMs better than online LLMs?")`  |
| Word  | str  | `better = Word("Which instruct LLM is the best?")`  |
| Sentence  | str  | `explaination = Sentence("Explain why")`  |
| Paragraph  | str  | `long_explaination = Paragraph("Give mode details")`  |
| Free  | str  | `unlimited = Free("Speak a lot without control...")`  |


### Composed Generators

List of simple Generators can be built.
| Noema Type | Generator Type  | Usage |
|-----------|-----------|-----------|
| ListOf  | [Int]  | `number = ListOf(Int,"Give me a list of number between 0 and 10")`  |
| ListOf  | [Float]  | `number = ListOf(Float,"Give me a list of number between 0.1 and 0.7")`  |
| ListOf  | [Bool]  | `truth_list = ListOf(Bool,"Are local LLMs better than online LLMs, and Mistral better than LLama?")`  |
| ListOf  | [Word]  | `better = ListOf(Word,"List the best instruct LLM")`  |
| ListOf  | [Sentence]  | `explaination = ListOf(Sentence,"Explain step by step why")`  |


### Code Generator

The `LanguageName` type provide a way to generate `LanguageName` code

| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| Python  | str  | `interface = Python("With pyqt5, genereate a window with a text field and a OK button.")`  |

<details>
  <summary>Language List</summary>

- Python
- Java
- C
- Cpp
- CSharp
- JavaScript
- TypeScript
- HTML
- CSS
- SQL
- NoSQL
- GraphQL
- Rust
- Go
- Ruby
- PHP
- Shell
- Bash
- PowerShell
- Perl
- Lua
- R
- Scala
- Kotlin
- Dart
- Swift
- ObjectiveC
- Assembly
- VHDL
- Verilog
- SystemVerilog
- Julia
- MATLAB
- COBOL
- Fortran
- Ada
- Pascal
- Lisp
- Prolog
- Smalltalk
- APL

</details>



### Information

The type Information is useful to insert some context to the LLM at the right time in the reflexion process.

| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| Information  | str  | `tips = Information("Here you can inject some information in the LLM")`  |

Here we use a simple string, but we can also insert a string from a python function call, do some RAG or any other tasks.


# Advanced:

### SemPy : Semantic python

The SemPy type is creating Python function dynamically and execute it with your parameters.
| Noema Type | Python Type  | Usage |
|-----------|-----------|-----------|
| SemPy  | depending  | `letter_place = SemPy("Find the place of a letter in a word.")("hello world","o")`  |

```python
from Noema import *

@Noema
def simple_task(task, parameters):
    """You are an incredible Python developer.
    Always looking for the best way to write code."""
    task_to_code = Information(f"I want to {task}")
    formulation = Sentence("Reformulate the task to be easily understood by a Python developer.")
    decomposition = ListOf(Sentence,"Decompose the task into smaller sub-tasks.")
    result = SemPy(formulation.value)(parameters) 
    # Generated code:
    #
    # def function_name(word):
    #     letter_counts = {}
    #     for char in word:
    #         if char.isalpha():  # Ensure only letters are counted
    #             char = char.lower()  # Convert to lowercase for uniformity
    #             if char in letter_counts:
    #                 letter_counts[char] += 1
    #             else:
    #                 letter_counts[char] = 1
    #     return letter_counts

    # def noema_func(word):
    #     return function_name(word)

    return result.value 
    
Subject("../Models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf",verbose=True)
nb_letter = simple_task("Count the occurence of letters in a word", "strawberry")
print(nb_letter)
# {'s': 1, 't': 1, 'r': 3, 'a': 1, 'w': 1, 'b': 1, 'e': 1, 'y': 1}
```

### Visualisation

Enabling reflection visualization with `write_graph = True` in the Subject init create a PlantUML and Mermaid diagram respectively in `diagram.puml` and `diagram.mmd`

```python
from Noema import *


# Create a new Subject
Subject("../Models/granite-3.1-3b-a800m-instruct-Q4_K_M.gguf", verbose=True, write_graph=True)

@Noema
def analysis_evaluation(analysis):
    """
    You are a specialist of analysis evaluation.
    You produce a numerical evaluation of the analysis, 0 is bad, 10 is good.
    Good means that the analysis is relevant and useful.
    Bad means that the analysis is not relevant and not useful.
    """
    analysis_to_evaluate = Information(f"{analysis}")
    evaluation = Float("Evaluation of the analysis, between 0 and 10")
    return evaluation.value

@Noema
def comment_note_evaluation(analysis):
    """
    You are a specialist of evaluation commenting.
    You always produce a deep analysis of the comment.
    """
    analysis_to_evaluate = Information(f"{analysis}")
    comment = Sentence("Commenting the analysis")
    return comment.value

@Noema
def comment_evaluation(comment):
  """
  You are a specialist of comment analysis.
  You always produce a deep analysis of the comment.
  """
  comment_to_analyse = Information(f"{comment}")
  specialists = ["Psychologist", "Sociologist", "Linguist", "Philosopher"]
  analyse_by_specialists = {}
  for specialist in specialists:
    analysis = Sentence(f"Analysing the comment as a {specialist}")
    analyse_by_specialists[specialist] = analysis.value
    evaluation = analysis_evaluation(analysis.value)
    comment_note_evaluation_res = comment_note_evaluation(evaluation)
    improvements = ListOf(Sentence, "List 4 improvements")
  
  synthesis = Paragraph("Providing a synthesis of the analysis.")
  sub = Substring(f"Extracting synthesis comment from {synthesis.value}")
  print(sub.value)
  return synthesis.value

synthesis = comment_evaluation("This llm is very good!")
print(synthesis)
```
<p align="center">
  <img src="visu.png" alt="Visualization example"/>
</p>


