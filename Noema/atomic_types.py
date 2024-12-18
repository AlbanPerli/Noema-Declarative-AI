from .Generator import Generator

class Word(Generator):
    regex = "[a-z]* | [A-Z][a-z]* | [a-z]+(_[a-z0-9]+)* | [a-z]+(.[a-z0-9]+)* | [a-z]+([A-Z][a-z0-9]*)*"
    hint = "Response format: a single word"
    return_type = str

class Int(Generator):
    regex = "\d+$"
    hint = "Response format: Integer number"
    return_type = int
    
class Float(Generator):
    regex = "\d+\.\d+$"
    hint = "Response format: Float number"
    return_type = float
    
class Bool(Generator):
    regex = "(True|False)$"
    hint = "Response format: Boolean value"
    return_type = bool
    
class Date(Generator):
    regex = "\d{4}-\d{2}-\d{2}$"
    hint = "Response format: YYYY-MM-DD"
    return_type = str
    
class DateTime(Generator):
    regex = "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    hint = "Response format: YYYY-MM-DD HH:MM:SS"
    return_type = str
    
class Time(Generator):
    regex = "\d{2}:\d{2}:\d{2}$"
    hint = "Response format: HH:MM:SS"
    return_type = str
    
class Phone(Generator):
    regex = "\d{10}$"
    hint = "Response format: 10 digits"
    return_type = str
    
class Email(Generator):
    regex = "[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*\.[a-zA-Z]+$"
    return_type = str
    hint = "Response format: email address" 