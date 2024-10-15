
import sys
import os
import unittest

# Add the project directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from noema.noema import Noema

class TestNoema(unittest.TestCase):
    def setUp(self):
        self.instance = Noema()

    def test_greet(self):
        self.assertEqual(self.instance.greet(), "Hello, I am a Noema instance.")

if __name__ == '__main__':
    unittest.main()
