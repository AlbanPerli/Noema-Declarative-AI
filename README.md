<p align="center">
  <img src="logoNoema.jpg" alt="ReadMe Banner"/>
</p>

**Noema is an application of the [*declarative* programming](https://en.wikipedia.org/wiki/Declarative_programming) paradigm to a langage model.** With Noema, you can control the model and choose the path it will follow. This framework aims to enable developpers to use LLM as an interpretor, not as a source of truth. Noema is built on [llamacpp](https://github.com/ggerganov/llama.cpp) and [guidance](https://github.com/guidance-ai/guidance)'s shoulders.

- [Concept](#Concept)
- [Installation](#installation)
- [Features](#features)


## Concept

- **Noesis**: can be seen as the description of a function
- **Noema**: is the representation (step by step) of this description
- **Constitution**: is the process of transformation Noesis->Noema.
- **(Transcendantal) Subject**: the object producing the Noema via the constitution of the noesis. Here, the LLM.
- **Horizon**: the environement of the subject, in other words, a context.

**Noema**/**Noesis**, **Subject**, **Horizon** and **Constitution** are a pedantic and naive application of concept borrowed from [Husserl's phenomenology](https://en.wikipedia.org/wiki/Edmund_Husserl).

## Installation

```bash
pip install Noema
```

## Features

### Create the Subject

```python
from Noema import *

s = Subject("path_to_model.gguf") # Full Compatibiliy with LLamaCPP.

s.add(though = "Time is the only problem") # store "Time is the only problem" in though
```

### Create an horizon and its constitution

```python
from Noema import *

s = Subject("path_to_model.gguf") # Full Compatibiliy with LLamaCPP.
s.add(though = "Time is the only problem") # store "Time is the only problem" in though

s= Horizon(
  Sentence(though_explanation = "You explain why {though}"), # The sentence produced is stored in though_explanation
  Int(explanation_note = "Give a note between 0 and 10 to qualify the quality of your explanation."), # The model produce an python integer that is stored in explanation_note
).constituteWith(s) # The horizon is constituted by the LLM

# Read the noema
print(s.noema)
# You are functioning in a loop of though. Here is your reasoning step by step:
#   #though_EXPLANATION: Explain why '{though}'.
#   #EXPLANATION_NOTE: Give a note between 0 and 10 to qualify the quality of your explanation.

# Here is the result of the reasoning:
#  #though_EXPLANATION: The reason is that time is the only thing that is constant and cannot be changed.
#  #EXPLANATION_NOTE: 10

# Acces to each constitution separatly
print(s.explanation_note * 2) # The value of 'explanation_note' is an int.
# 20
```

### Simple generators

Generators can be used to generate content from the subject (LLM) through the noesis (here, the task description).

```python
from Noema import *

horizon = Horizon(
  Sentence(var_name = "task description"), # Produce a sentence stored in var_name
  Word(var_name = "task description"),     # Produce a word stored in var_name
  Int(var_name = "task description"),      # Produce an int stored in var_name
  Float(var_name = "task description"),    # Produce a float stored in var_name
  Bool(var_name = "task description"),     # Produce a bool stored in var_name
)
```

### Composed generators

ListOf can be built with simple generators or a custom `Step`.

```python
from Noema import *

horizon = Horizon(
  ListOf(Word, var_name = "task description",),  # Produce a list of Word stored in var_name
  ListOf(Int, var_name = "task description",),   # Produce a list of int stored in var_name
  ...
)
```

### Selector

```python
from Noema import *

s = Subject("path_to_model.gguf")

s= Horizon(
  Select(this_is_the_future = "Are local LLMs the future?", options=["Yes of course","Never!"]), # The model can only choose between "Yes of course" and "Never!". 
).constituteWith(s) # The horizon is constituted by the LLM
```

### Information

Information are useful to insert some context to the current step of the noesis.
Here we use a simple string, but we can also call a python function to do some RAG or other tasks.

```python
from Noema import *

s = Subject("path_to_model.gguf")

s= Horizon(
    Information("You act like TARS in interstellar."),
    Sentence(joke = "Tell a short joke."),
    Print("{joke}")
).constituteWith(s)
```

### Control Flow

#### IF/ELSE

```python
from Noema import *

s = Subject("path_to_model.gguf")
s.add(though = "Time is the only problem") # store "Time is the only problem" in though

s = Horizon(
    Var(final_though=None), # Create a variable final_though
    Sentence(though_explanation = "Explain why '{though}'."), 
    Int(explanation_note = "Give a note between 0 and 10 to qualify the quality of your explanation."), 
    Select(auto_analysis="Do some auto-analysis, and choose a word to qualify your note", options=["Fair","Over optimistic","Neutral"]),
    IF(lambda: s.explanation_note < 5, [
        Information("The explanation is not clear enough, and the note is too low."),
        Int(points_to_add = "How many points do you think you should add to be fair?"),
        Sentence(points_explanation = "Explain why you think you should add {points_to_add} points."),
        Var(final_though = "The explanation is not clear enough, and the note is too low. I should add {points_to_add} points."),
    ],ELSE=[
       IF(lambda: s.auto_analysis == 'Over optimistic', [  
            Int(points_to_remove ="How many points do you think you should remove to be fair?"),
            Sentence(points_explanation = "Explain why you think you should remove {points_to_remove} points."),
            Var(final_though = "The explanation is not clear enough, and the note is too low. I should remove {points_to_remove} points."),
       ],ELSE=[
            Print("The explanation is clear enough, and the note is fair."),   
            Var(final_though = "The note is fair."),
        ]),
    ])
).constituteWith(s) # The horizon is constituted by the LLM

print(s.final_though) # Print the final though
# The explanation is not clear enough, and the note is too low. I should add 5 points.
```

#### ForEach
```python
from Noema import *

s = Subject("path_to_model.gguf")

s = Horizon(
    ListOf(Sentence, problems =  "What are the problems you are facing (in order of difficulty)?"), # The model produce a list of sentence that is stored in {problems}
    ForEach(lambda: s.problems, [
        Sentence(item_explanation = "Explain why '{item}' is the problem No {idx}."), 
        Print("Pb Nb {idx}: {item}. Explanation: {item_explanation}") # Print doesn't interfere with the Noema 
    ])
).constituteWith(s) # The horizon is constituted by the LLM

# Pb Nb 1: I don't know what to do next.. Explanation: Because if you don't know what to do next, you can't make progress and achieve your goals.
# Pb Nb 2: I don't have enough information to make a decision.. Explanation: Because if you don't have enough information, you can't make an informed decision and may make a mistake that could set you back or cause problems down the line.
# Pb Nb 3: I'm not sure if I'm on the right track.. Explanation: Because if you're not sure if you're on the right track, you may be wasting time and effort on a path that won't lead to your goals, and you may not realize it until it's too late to change course.
```

#### While
```python
s = Subject("path_to_model.gguf")

s = Horizon(
    Information("You have to choose a job name in the field of computer science."),
    Var(word_length = 0 ),
    While(lambda: s.word_length < 9,[
        Word(job_name = "Give a good job name:"),
        Int(word_length = "How many letters are in the word {job_name}?"),
        Print("Selected job {job_name}"),
        Information("You have to choose a new job name each time."),
    ]),
    Print("The word {job_name} has more than 10 letters."),
    PrintNoema()
).constituteWith(s)
```


### NOESIS

The Noesis is the descriptive process of a though.
You can think about it as a set of rules aiming to attain a goal.
In a function we think about steps, here you have to *declare how to think* about the steps.

A Noesis need a description, here: "Find a job name in a field." and can take optionnal parameters. 
The `Return` is optional.

```python
from Noema import *

s = Subject("path_to_model.gguf")

find_job_name = Noesis("Find a job name in a field.",["field_name","max_length"],[
    Information("You have to choose a job name in the field of {field_name}."),
    Var(word_length = 0),
    While(lambda: s.word_length < s.max_length, [
        Word(job_name = "Give a good job name:"),
        Int(word_length = "How many letters are in the word {job_name}?"),
        Print("Selected job {job_name}"),
        Information("You have to choose a new job name each time."),
    ]),
    Return("{job_name} is a good job name in the field of {field_name}.") #Return value
])

s = Horizon(
    Constitute(job_name = lambda:find_job_name(s, field_name="IT",max_length=10)), 
    Print("{job_name} has more than 10 letters."),
).constituteWith(s) # The horizon is constituted by the LLM

# Selected job programmer
# Duration for 'Find a job name in a field.' : 00:01s
# programmer is a good job name in the field of IT. has more than 10 letters.
```


### Python Function Call

In the Noesis we can call a python function. 
The parameters can be value extracted from the context i.e. a `Var` using `{var_name}`.
Return value of the python function called can be stored in a `Var`.

```python
from Noema import *

s = Subject("path_to_model.gguf")

def count_letters(word):
    return len(word)

s = Horizon(
    Var(palindrome = "TENET"), # store "TENET" in {palindrome}
    CallFunction(word_length = lambda: count_letters(s.palindrome)), # store the result of the function count_letters in {word_length}
    Print("The word '{palindrome}' has {word_length} letters."),
).constituteWith(s)
```
