class NoesisModel:
    
    def __init__(self,variable,type,value,annotation=None,var_and_values={}):
        self.variable = variable
        self.type = type
        self.original_value = value
        self.value = value
        self.annotation = annotation
        self.next_model = None
        self.var_and_values = var_and_values
        
    def display_var(self):
        return "#"+self.variable.upper()+":"
    
    def stops(self):
        if self.next_model is not None:
            v = self.next_model.variable
            return [self.next_model.display_var()]
        else:
            return []
    
    def __repr__(self):
        return f"{self.variable} {self.type} = {self.value} @{self.annotation} | {self.var_and_values}"
    
