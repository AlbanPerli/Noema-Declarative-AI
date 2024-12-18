from Noema.noesis_wrapper import *
from Noema.Generator import *
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton
)

Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf", 32*1024)

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QFileDialog
)
from PyPDF2 import PdfReader

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fenêtre de Chat")
        self.setGeometry(100, 100, 400, 500)
        
        # Layout principal
        self.layout = QVBoxLayout()

        # Zone d'affichage du chat
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        # Layout d'entrée de message
        self.input_layout = QHBoxLayout()

        # Zone de saisie de message
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Écrivez votre message ici...")
        self.input_layout.addWidget(self.message_input)

        # Bouton Envoyer
        self.send_button = QPushButton("Envoyer")
        self.send_button.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_button)

        # Ajout du layout d'entrée au layout principal
        self.layout.addLayout(self.input_layout)

        # Bouton pour charger un PDF
        self.load_pdf_button = QPushButton("Charger un PDF")
        self.load_pdf_button.clicked.connect(self.load_pdf)
        self.layout.addWidget(self.load_pdf_button)

        # Configuration du layout principal
        self.setLayout(self.layout)

    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            response = self.explainUser(message)
            self.chat_display.append(f"Vous: {message}")
            self.chat_display.append(f"Bot: {response}")
            self.message_input.clear()

    def load_pdf(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier PDF", "", "Fichiers PDF (*.pdf)", options=options)
        if file_path:
            try:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                self.chat_display.append(self.resume(text))
                
            except Exception as e:
                self.chat_display.append(f"Erreur lors du chargement du PDF: {e}")


    @Noema
    def resume(self, text):
        """You are a specialist of summaries."""
        summary = Free(f"Here, I summarize the following text:\n{text}")
        return summary.value

    @Noema
    def explainUser(self,question):
        """You are a specialist of explainations."""
        explanation = Sentence(f"Here, I explain why {question}")
        return explanation.value

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())