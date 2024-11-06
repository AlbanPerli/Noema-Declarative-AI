import sys
import linecache
import re
import os

class MyClass:
    def __init__(self):
        self.counter = 0  # Compteur pour les lignes exécutées

    def trace_func(self, frame, event, arg):
        if event == 'line':
            filename = frame.f_code.co_filename
            module_filename = os.path.abspath(__file__)

            # Vérifier que nous sommes dans le fichier du module courant
            if os.path.abspath(filename) != module_filename:
                return

            lineno = frame.f_lineno
            line = linecache.getline(filename, lineno).strip()
            self.counter += 1

            # Logique d'interception
            pattern = r'^print'
            try:
                if re.match(pattern, line):
                    print(f"[{self.counter}] Interception de la ligne {lineno}: {line}")

                    # Accéder aux variables locales
                    local_vars = frame.f_locals

                    # Vérifier si 'code_by_step' est dans les variables locales
                    if 'code_by_step' in local_vars:
                        code_by_step = local_vars['code_by_step']
                        # Vérifier que c'est un dictionnaire (objet mutable)
                        if isinstance(code_by_step, dict):
                            # Modifier le contenu du dictionnaire
                            code_by_step[f"line_{lineno}"] = f"Interception à la ligne {lineno}"
                        else:
                            print("La variable 'code_by_step' n'est pas un dictionnaire.")
                    else:
                        print("La variable 'code_by_step' n'est pas présente dans les variables locales.")
                else:
                    print(f"[{self.counter}] Exécution de la ligne {lineno}: {line}")
            except Exception as e:
                print(f"Erreur lors de l'interception de la ligne {lineno}: {e}")
        return self.trace_func


    def run(self):
        def local_trace(frame, event, arg):
            return self.trace_func(frame, event, arg)

        try:
            sys.settrace(local_trace)
            self.description()
        except Exception as e:
            print(f"Erreur lors de l'exécution de 'description': {e}")
        finally:
            sys.settrace(None)
            print("Le traçage a été désactivé dans 'finally'.")

        print(f"Nombre total de lignes exécutées : {self.counter}")



class SubClass(MyClass):
    
    def description(self):
        steps = ["fonctionnalités", "appels réseau", "gestion des données"]
        code_by_step = {}  # Dictionnaire mutable
        for step in steps:
            print(step)
            if step == "appels réseau":
                print("Traitement spécial pour les appels réseau")
        print("Fin de la description")



# Utilisation
if __name__ == "__main__":
    my_instance = SubClass()
    my_instance.run()
