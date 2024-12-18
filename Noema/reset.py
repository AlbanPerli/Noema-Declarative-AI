from .Subject import Subject

class Reset:

    def __init__(self):
        Subject().shared().llm.reset()