from .BaseGenerator import BaseGenerator
from itertools import count
from .generation import execute_generation
from varname import varname
from varname.utils import ImproperUseError


_unnamed_generator_counter = count(1)


def _unnamed_generator_id(instance):
    class_name = type(instance).__name__.lower()
    return f"{class_name}_{next(_unnamed_generator_counter)}"

def noema_generator(cls):
    class Wrapped(cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if hasattr(self, 'var') and self.var is not None:
                self.id = self.var.replace("self.", "")
                self._value = f"#{self.id.upper()}:"
                return
            try:
                self.id = varname()
            except ImproperUseError:
                self.id = _unnamed_generator_id(self)
            self.id = self.id.replace("self.", "")
            if hasattr(self, 'value') and self.value is not None:
                self.execute()

        def __str__(self):
            return self._value if hasattr(self, '_value') else super().__str__()
    return Wrapped

@noema_generator
class Generator(BaseGenerator):
    regex = None
    return_type = None
    hint = None
    stops = []
    stop_regex = None
    save_stop_text = False
    max_tokens = 64
    
    def __init__(self, value=None, idx:int = None, var: str = None, options: list = None):
        super().__init__()
        self.var = var
        self.value = value
        self.idx = idx
        self.options = options
        
    def execute(self):
        execute_generation(
            self,
            regex=self.regex,
            stop_regex=self.stop_regex,
            stops=self.stops,
            save_stop_text=self.save_stop_text,
        )



# TODO: Implement Fill class
# class Fill(Generator):
#     regex = ""
    
#     def __init__(self, header, body, value=None):
#         super().__init__(value)
#         self.header = header
#         self.body = body
