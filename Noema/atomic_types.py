from .Generator import Generator

class Word(Generator):
    regex = r"[a-z]* | [A-Z][a-z]* | [a-z]+(_[a-z0-9]+)* | [a-z]+(\.[a-z0-9]+)* | [a-z]+([A-Z][a-z0-9]*)*"
    hint = "Response format: a single word"
    return_type = str
    max_tokens = 8

class Int(Generator):
    regex = r"\d+$"
    hint = "Response format: Integer number"
    return_type = int
    max_tokens = 8
    
class Float(Generator):
    regex = r"\d+\.\d+$"
    hint = "Response format: Float number"
    return_type = float
    max_tokens = 8
    
class Bool(Generator):
    regex = "(True|False)$"
    hint = "Response format: Boolean value"
    return_type = bool
    max_tokens = 4
    
class Date(Generator):
    regex = r"\d{4}-\d{2}-\d{2}$"
    hint = "Response format: YYYY-MM-DD"
    return_type = str
    max_tokens = 12
    
class DateTime(Generator):
    regex = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    hint = "Response format: YYYY-MM-DD HH:MM:SS"
    return_type = str
    max_tokens = 24
    
class Time(Generator):
    regex = r"\d{2}:\d{2}:\d{2}$"
    hint = "Response format: HH:MM:SS"
    return_type = str
    max_tokens = 12
    
class Phone(Generator):
    regex = r"\d{10}$"
    hint = "Response format: 10 digits"
    return_type = str
    max_tokens = 16
    
class Email(Generator):
    regex = r"[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*\.[a-zA-Z]+$"
    return_type = str
    hint = "Response format: email address" 
    max_tokens = 48
