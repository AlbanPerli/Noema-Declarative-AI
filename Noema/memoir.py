from importlib import *
import importlib
import os
import types
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import time
import hashlib
import uuid
import base64
import ast
import inspect
from inspect import _empty
import autopep8
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import *
from .memoryFragment import MemoryFragment
from .executableMemoryFragment import ExecutableMemoryFragment

class Memoir:
    
    def __init__(self, collection_name="default", chroma_data_path="memoir_data/", persist_directory="db1", embed_model="all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory or os.getenv('PERSIST_DIRECTORY')
        if not self.persist_directory:
            raise ValueError("Please set the PERSIST_DIRECTORY environment variable")
        
        self.chroma_settings = Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=True
        )
        
        self.chroma_data_path = chroma_data_path if chroma_data_path != "memoir_data/" else os.path.join(os.getcwd(), chroma_data_path)
        self.embed_model = embed_model
        self.collection_name = f"memoir_{collection_name}"
        self.focused_subject = None
        
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.embed_model)
        self.client = chromadb.PersistentClient(self.chroma_data_path, self.chroma_settings)
        self.add_collection(self.collection_name, metadata={"start": "empty"})
        
        self.model = SentenceTransformer(self.embed_model)

    def create_id(self):
        return base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b'=').decode('utf-8')

    def create_hash(self, document):
        return hashlib.md5(document.encode()).hexdigest()

    def document_exists(self, hash_value):
        result = self.collection.query(
            query_texts=[""],
            where={"hash": {"$eq": hash_value}},
            n_results=1
        )
        return len(result["documents"][0]) > 0

    def add_collection(self, collection_name, metadata={"start": "empty"}):
        existing_collections = [col.name for col in self.client.list_collections()]
        if collection_name in existing_collections:
            self.collection = self.client.get_collection(collection_name)
        else:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_func,
                metadata=metadata
            )

    def clear_memory(self):
        self.client.delete_collection(name=self.collection_name)
        self.add_collection(self.collection_name)

    def add(self, text: str, subject: str = None, metadata=None) -> str:
        if metadata is None:
            metadata = {}

        subject = subject or self.focused_subject
        hash_value = self.create_hash(text)

        if self.document_exists(hash_value):
            print(f"Document already exists with hash: {hash_value}")
            return "Document already exists"

        doc_id = self.create_id()
        metadata.update({
            "subject": subject,
            "hash": hash_value,
            "timestamp": time.time()
        })

        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return "Memory added successfully."

    def retrieve(self, text, subject=None):
        query_params = {
            "query_texts": [text],
            "include": ["metadatas", "distances", "documents"]
        }

        if subject or self.focused_subject:
            query_params["where"] = {"subject": {"$eq": subject or self.focused_subject}}

        result = self.collection.query(**query_params)

        if result["documents"] and result["metadatas"]:
            first_doc = result["documents"][0][0]
            first_meta = result["metadatas"][0][0]
            if subject == 'function':
                return ExecutableMemoryFragment(first_meta.get("code"), first_meta.get("subject"), first_meta)
            else:
                return MemoryFragment(first_doc, first_meta.get("subject"), first_meta)
        return None
    
    def retrieves(self, text, subject=None, threshold=1.27, limit=3):
        query_params = {
            "query_texts": [text],
            "include": ["metadatas", "distances", "documents"]
        }

        if subject or self.focused_subject:
            query_params["where"] = {"subject": {"$eq": subject or self.focused_subject}}

        result = self.collection.query(**query_params)

        results = []
        if result["documents"] and result["metadatas"]:
            for i in range(len(result["documents"][0])):
                distance = result["distances"][0][i]
                if distance < threshold:
                    if subject == 'function':
                        fragment = ExecutableMemoryFragment(
                        text=result["metadatas"][0][i].get("code", None),
                        subject=result["metadatas"][0][i].get("subject", None),
                        metadata=result["metadatas"][0][i],
                        distance=distance
                    )
                    else:
                        fragment = MemoryFragment(
                        text=result["documents"][0][i],
                        subject=result["metadatas"][0][i].get("subject", None),
                        metadata=result["metadatas"][0][i],
                        distance=distance
                    )
                    results.append(fragment)

            results = sorted(results, key=lambda x: x.distance)

            results = results[:limit]

        return results


    def all_about(self, subject: str = None, idea: str = None):
        if subject:
            return self.all_subject(subject)
        if idea:
            return self.all_ideas(idea)
        return None

    def all_subject(self, subject: str):
        result = self.collection.get(
            where={"subject": {"$eq": subject}},
            include=["metadatas", "documents"]
        )
        return self._format_result(result)

    def all_ideas(self, idea: str):
        result = self.collection.query(
            query_texts=[idea],
            include=["metadatas", "distances", "documents"]
        )
        return self._format_result(result, with_distance=True)

    def _format_result(self, result, with_distance=False):
        output = []
        for i in range(len(result["documents"])):
            fragment = MemoryFragment(
                text=result["documents"][i],
                subject=result["metadatas"][i].get("subject", None),
                metadata=result["metadatas"][i],
                distance=result["distances"][0][i] if with_distance else None
            )
            output.append(fragment)
        return sorted(output, key=lambda x: x.metadata.get("timestamp", 0))

    def context(self, subject: str):
        self.focused_subject = subject

    def add_qa(self, question: str, answer: str):
        embedding = self.model.encode([question])[0]
        self.collection.add(
            documents=[question],
            embeddings=[embedding.tolist()],
            metadatas=[{"answer": answer, "type": "qa"}],
            ids=[self.create_id()]
        )

    def get_answer(self, question: str):
        query_embedding = self.model.encode([question])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=1,
            include=["distances", "metadatas"]
        )
        if results["distances"][0][0] < 0.4:
            return results["metadatas"][0][0]["answer"]
        return "I don't know."

    def add_context(self, context: str):
        self.collection.add(
            documents=[context],
            metadatas=[{"type": "context", "key": context}],
            ids=[self.create_id()]
        )

    def get_context(self, context: str):
        result = self.collection.query(
            query_texts=[context],
            where={"type": {"$eq": "context"}},
            include=["metadatas", "documents", "distances"]
        )

        if result["distances"][0][0] < 1.0:
            return result["metadatas"][0][0]["key"]
        return None

    def forget_about(self, question: str):
        query_embedding = self.model.encode([question])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=1,
            include=["distances"]
        )

        if len(results['ids']) > 0:
            self.collection.delete(ids=results['ids'][0])
            print("Question has been forgotten.")
        else:
            print("Question not found.")
            

    def normalize_type(self,type_obj):
        if isinstance(type_obj, type):
            return type_obj.__name__ 
        elif hasattr(type_obj, '__origin__'):  
            origin = type_obj.__origin__
            args = type_obj.__args__
            if origin is list:
                return f"List[{', '.join(self.normalize_type(arg) for arg in args)}]"
            elif origin is dict:
                return f"Dict[{self.normalize_type(args[0])}, {self.normalize_type(args[1])}]"
            else:
                return str(type_obj)
        return str(type_obj)


    def add_function(self, function_str: str, scope:str = "global") -> str:
        try:
            formatted_function_str = autopep8.fix_code(function_str)
            compiled_function = compile(formatted_function_str, "<string>", "exec")
            exec(compiled_function)
            parsed_function = ast.parse(formatted_function_str).body[0]

            if isinstance(parsed_function, ast.FunctionDef):
                func_name = parsed_function.name
                docstring = func_name + "\n" + ast.get_docstring(parsed_function)
                exec(formatted_function_str) 
                signature = inspect.signature(eval(func_name))
                param_types = {param: self.normalize_type(signature.parameters[param].annotation) 
                            if signature.parameters[param].annotation != _empty else "unknown"
                            for param in signature.parameters}

                return_type = self.normalize_type(signature.return_annotation) if signature.return_annotation != _empty else "unknown"
                param_types_str = json.dumps(param_types)
                metadata = {
                    "type": "function",
                    "name": func_name,
                    "scope": scope,
                    "code": formatted_function_str,
                    "param_types": param_types_str,  
                    "return_type": return_type, 
                    "timestamp": time.time()
                }

                self.add(docstring, subject="function", metadata=metadata)
                return f"Function '{func_name}' added successfully."
            else:
                raise ValueError("Invalid function string")
            
        except SyntaxError as e:
            print(f"Error adding function: invalid syntax - {e}")
            print(f"Function content: {formatted_function_str}")
            return "Error adding function: invalid syntax"
        except Exception as e:
            print(f"Error adding function: {e}")
            return "Error adding function"


    def run(self,description:str):
        return self.retrieve(description,subject='function')
    
    def retrieve_functions_for_steps(self,steps_description:str):
        steps = steps_description.split("\n")
        
        functions = []
        for step in steps:
            near_functions = self.retrieves(step,subject='function',limit=1)
            for f in near_functions:
                if f.value not in [func.value for func in functions]:
                    functions.append(f)
            
        return functions
    
    def load_functions_from_module(self, module_name: str):
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, types.FunctionType):
                    function_source = inspect.getsource(obj)
                    result = self.add_function(function_source, scope=module_name)

            return f"Functions from '{module_name}' are loaded."

        except ModuleNotFoundError:
            return f"Module '{module_name}' not found."
        except Exception as e:
            return f"Error loading functions from '{module_name}': {e}"
