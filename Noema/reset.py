from .llm import current_runtime

class Reset:

    def __init__(self):
        current_runtime().llm.reset()