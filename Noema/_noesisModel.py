class NoesisModel:
    
    def __init__(self,variable,type,value,annotation):
        self.variable = variable
        self.type = type
        self.original_value = value
        self.value = value
        self.annotation = annotation
        
    def display_var(self):
        return "#"+self.variable.upper()+":"
    
    def __repr__(self):
        return f"{self.variable} {self.type} = {self.value} @{self.annotation}"
    
