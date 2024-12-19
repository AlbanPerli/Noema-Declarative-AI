from Noema import *

@Noema
def simple_task():
    """Instruct prompt """
    
    letter_index = SemPy("Open a window with a webview inside, using pyqt5.")("https://www.google.com") 
    print(letter_index.value)
    
Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf",verbose=True)
simple_task()