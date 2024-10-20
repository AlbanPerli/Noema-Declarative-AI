
import sys
import os
import unittest

# Add the project directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Noema import *

class TestNoema(unittest.TestCase):
    def setUp(self):
        self.subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")
    
    # Test Horizon creation
    # Test var creation and storage
    # Test Sentence creation
    # Test Int creation
    # Test Float creation
    # Test Bool creation
    # Test Select creation
    # Test IF/ELSE
    # Test Sentence creation from var
    # Test Int creation from var
    # Test Float creation from var
    # Test Bool creation from var
    # Test Select creation from var
    # Test IF/ELSE from var
    # Ajouter un SelectOneOrMore
    
if __name__ == '__main__':
    unittest.main()
