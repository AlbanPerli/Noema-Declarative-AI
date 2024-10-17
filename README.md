<p align="center">
  <img src="logoNoema.png" alt="ReadMe Banner"/>
</p>

**Noema is an application of the [*declarative* programming](https://en.wikipedia.org/wiki/Declarative_programming) paradigm to a langage model.** With Noema, you can control the model and choose the path it will follow. This framework aims to enable developpers to use LLM as an interpretor, not as a source of truth. Noema is built on [llamacpp](https://github.com/ggerganov/llama.cpp) and [guidance](https://github.com/guidance-ai/guidance)'s shoulders.

- [Concept](#Concept)
- [Installation](#installation)
- [Features](#features)
- [Examples](#exemples)
- [Licence](#licence)

## Concept

- Noesis: can be seen as the description of a function
- Noema: is the representation (step by step) of this description
- Constitution: is the process of transformation Noesis->Noema.
- (Transcendantal) Subject: the object producing the Noema via the constitution of the noesis. Here, the LLM.
- Horizon: the environement of the subject, in other words, a context.

**Noema**/**Noesis**, **Subject**, **Horizon** and **Constitution** are a pedantic and naive application of concept borrowed from [Husserl's phenomenology](https://en.wikipedia.org/wiki/Edmund_Husserl).

## Installation

```bash
pip install git+https://github.com/AlbanPerli/Noema-Declarative-AI
```

## Features

### Create the Subject

```python
from Noema import *

subject = Subject("model.gguf") # Full Compatibiliy with LLamaCPP.

subject.add(Var("Time is the only problem", "{thougth}")) # store "Time is the only problem" in {thougth}
```

### Create an horizon

```python
from Noema import *

horizon = Horizon(
  Sentence("You explain why {thougth}","{thougth_explanation}"), # The sentence produced is stored in {thougth_explanation}
  Int("Give a note between 0 and 10 to qualify the quality of your explanation.","{explanation_note}"), # The model produce an python integer that is stored in {explanation_note}
)
```

### Constitution

```python
from Noema import *

subject = horizon.constituteWith(subject) # The horizon is constituted by the LLM

# Read the noema
print(subject.noema)
# You are functioning in a loop of thought. Here is your reasoning step by step:
#   #THOUGTH_EXPLANATION: Explain why '{thougth}'.
#   #EXPLANATION_NOTE: Give a note between 0 and 10 to qualify the quality of your explanation.

# Here is the result of the reasoning:
#  #THOUGTH_EXPLANATION: The reason is that time is the only thing that is constant and cannot be changed.
#  #EXPLANATION_NOTE: 10

# Acces to each constitution separatly
print(subject.data["explanation_note"] * 2) # The value of 'explanation_note' is an int.
# 20
```

### Simple generators

Generators can be used to generate content from the subject (LLM) through the noesis (here, the task description).

```python
from Noema import *

horizon = Horizon(
  Sentence("task description","{var_name}") # Produce a sentence stored in {var_name}
  Word("task description","{var_name}")     # Produce a word stored in {var_name}
  Int("task description","{var_name}")      # Produce an int stored in {var_name}
  Float("task description","{var_name}")    # Produce a float stored in {var_name}
  Bool("task description","{var_name}")     # Produce a bool stored in {var_name}
)
```

### Composed generators

ListOf can be built with simple generators or a custom `Step`.

```python
from Noema import *

horizon = Horizon(
  ListOf(Word, "task description","{var_name}")  # Produce a list of Word stored in {var_name}
  ListOf(Int, "task description","{var_name}")   # Produce a list of int stored in {var_name}
  ...
)
```

### Selector

```python
from Noema import *

horizon = Horizon(
  Select("Are local LLMs the future?", ["Yes of course","Never!"], "{this_is_the_future}"), # The model can only choose between "Yes of course" and "Never!". 
)
```

### Information

```python
from Noema import *

subject = Horizon(
    Information("You act like TARS in interstellar."),
    Sentence("Tell a short joke.","{joke}"),
    Print("{joke}")
).constituteWith(subject)
```

### Control Flow

#### IF/ELSE

```python
from Noema import *

subject = Horizon(
    Sentence("Explain why '{thougth}'.","{thougth_explanation}"), 
    Int("Give a note between 0 and 10 to qualify the quality of your explanation.","{explanation_note}"), 
    IF("{explanation_note} < 5", [
        Select("Do some auto-analysis, and choose a word to qualify your note", ["Fair","Over optimistic","Neutral"], "{auto_analysis}"),
    ],ELSE=[
       Select("Do some auto-analysis, and choose a word to qualify your note", ["Over optimistic","Neutral"], "{auto_analysis}"),
       IF("'{auto_analysis}' == 'Over optimistic'", [  # Note the " ' " around {auto_analysis}
            Int("How many points do you think you should remove to be fair?","{points_to_remove}"),
            Sentence("Explain why you think you should remove {points_to_remove} points.","{points_explanation}"),
       ])
    ])
).constituteWith(subject)

print(subject.data["auto_analysis"])      # "Over optimistic"
print(subject.data["points_to_remove"])   # 1
print(subject.data["points_explanation"]) # "The explanation is not clear enough, and the note is too high."
```

#### ForEach
```python
from Noema import *

subject = Horizon(
    ListOf(Sentence, "What are the problems you are facing (in order of difficulty)?","{problems}"), # The model produce a list of sentence that is stored in {problems}
    ForEach("{problems}","{item}","{count}", [
        Sentence("Explain why '{item}' is the problem No {count}.","{item_explanation}"), # The sentence produced is stored in {item_explanation}
        Print("Pb Nb {count}: {item}. Explanation: {item_explanation}")
    ])
).constituteWith(subject)
# DEBUG: Pb Nb 1: I can't find a solution to the problem.. Explanation: Because if you can't find a solution, you can't make progress.
# DEBUG: Pb Nb 2: I don't know where to start.. Explanation: Because if you don't know where to start, you can't make any progress either.
# DEBUG: Pb Nb 3: I'm overwhelmed by the complexity of the problem.. Explanation: Because if you're overwhelmed, you can't focus on finding a solution or even knowing where to start.
```

#### While
```python
from Noema import *

subject = Horizon(
    Information("You have to choose a job name."),
    Var(0,"{word_length}"),
    While("{word_length} < 7",[
        Word("Give a good job name:","{job_name}"),
        Int("How many letters are in the word {job_name}?","{word_length}"),
        Print("Selected job {job_name}"),
        Information("You have to choose a new job name each time."),
    ]),
    Print("The word {job_name} has more than 10 letters."),
    PrintNoema()
).constituteWith(subject)
```


### NOESIS

The Noesis is the descriptive process of a thought.
You can think about it as a set of rules aiming to attain a goal.
In a function we think about steps, here you have to think about how to think about steps.

```python
from Noema import *

subject = Horizon(
    Information("You act like TARS in interstellar."),
    Sentence("Tell a short joke.","{joke}"),
    Print("{joke}")
).constituteWith(subject)
```