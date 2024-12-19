from Noema import *

@Noema
def simple_task():
    """Instruct prompt """
    
    letter_index = SemPy("Open a window with a textfield and a submit button, using pyqt5.")("Popup title","Name...") 
    print(letter_index.value)
    
Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf",verbose=True)
simple_task()