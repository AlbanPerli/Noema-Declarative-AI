<p align="center">
  <img src="logoNoema.jpg" alt="ReadMe Banner"/>
</p>

<div align="center"> 
<span style="font-size: 29px;">Seamless integration between Python and LLM generations.</span>
<p><span style="font-size: 29px;">
With Noema, you can control the model and choose the path it will follow. 
<br>This framework aims to enable developers to use **LLMs as thought interpreters**, not as a source of truth.

Noema is built on the shoulders of [llama.cpp](https://github.com/ggerganov/llama.cpp) and [guidance](https://github.com/guidance-ai/guidance).
</span></p>
</div>

## Installation

```bash
pip install noema
```

Install [llama-cpp-python](https://github.com/abetlen/llama-cpp-python?tab=readme-ov-file#supported-backends) using the correct backend.

## Basic Example

```python
from Noema import *

# Create a subject (LLM)
Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf", verbose=True)

@Noema
def think(task):
    """
    You are a simple thinker.
    You have a task to perform and are always looking for the best way to perform it.
    """
    povs = []
    task = Information(f"{task}")
    for i in range(4):
        step_nb = i + 1
        reflection = Sentence("Providing a reflection about the task.", step_nb)
        consequence = Sentence("Providing the consequence of the reflection.", step_nb)
        evaluate = Sentence("Evaluating the consequence.", step_nb)
        point_of_view = Sentence(
            f"Providing a point of view about the task different from {povs}",
            step_nb,
        )
        qualification = Word(
            f"Qualify the point of view with a word different from: {povs}",
            step_nb,
        )
        povs.append(qualification.value)
        creativity = Float(
            f"How creative is this point of view: {povs[-1]} (between 0 and 10)",
            step_nb,
        )
        if creativity.value < 8.0:
            Information("I need to be more creative!")
    conclusion = Paragraph(
        "Provide a conclusion synthesizing the previous steps."
    )
    return conclusion.value

conclusion = think("How to write a good iOS application?")
print(conclusion)
```

## Background

**Noema is an application of the *declarative programming* paradigm to language models.**

### Concept

- **Noesis**: the description of a function
- **Noema**: the step-by-step representation of this description
- **Constitution**: the transformation process from Noesis to Noema
- **Subject**: the entity producing the Noema through constitution (the LLM)

These concepts are a naive and pedagogical borrowing from Husserl's phenomenology.

## Features

- Declarative control over LLM reasoning
- ReAct-style prompting
- Typed generators (int, float, bool, text, code, etc.)
- Dynamic code generation (SemPy)
- Optional reasoning visualization (PlantUML / Mermaid)

## License

MIT
