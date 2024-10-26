class MemoryFragment:
    def __init__(self, text, subject, metadata, distance=None):
        self.value = text
        self.subject = subject
        self.metadata = metadata
        self.distance = distance

    def __repr__(self):
        return f"MemoryFragment(text={self.value}, subject={self.subject}, metadata={self.metadata}, distance={self.distance})"