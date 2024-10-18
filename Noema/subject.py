from guidance import models
class Subject:
    def __init__(self, llm_path):
        self.data = {}
        self.namespace_stack = []
        self.llm = models.LlamaCpp(
            llm_path,
            n_gpu_layers=99,
            n_ctx=512*8,
            echo=False
        )
        self.noema = ""
        
    def add(self, var):
        var.execute(self)

    def set(self, key, value, extend = False):
        if self.namespace_stack:
            namespace = self.namespace_stack[-1]
            if namespace not in self.data:
                self.data[namespace] = {}
            
            if key not in self.data[namespace].keys():
                self.data[namespace][key] = []
            
            if extend:
                if isinstance(self.data[namespace][key], list):
                    if isinstance(value, list):
                        tmp = self.data[namespace][key]
                        tmp.extend(value)
                        self.data[namespace][key] = tmp
                    else:
                        tmp = self.data[namespace][key]
                        tmp.append(value)
                        self.data[namespace][key] = tmp
                else:
                    if isinstance(value, list):
                        tmp = [self.data[namespace][key]]
                        tmp.extend(value)
                        self.data[namespace][key] = tmp
                    else:
                        tmp = [self.data[namespace][key]]
                        tmp.append(value)
                        self.data[namespace][key] = tmp
            else:
                self.data[namespace][key] = value
        else:
            if key not in self.data.keys():
                self.data[key] = []
            if extend:
                if isinstance(self.data[key], list):
                    if isinstance(value, list):
                        tmp = self.data[key]
                        tmp.extend(value)
                        self.data[key] = tmp
                    else:
                        tmp = self.data[key]
                        tmp.append(value)
                        self.data[key] = tmp
                else:
                    if isinstance(value, list):
                        tmp = [self.data[key]]
                        tmp.extend(value)
                        self.data[key] = tmp
                    else:
                        tmp = [self.data[key]]
                        tmp.append(value)
                        self.data[key] = tmp
            else:
                self.data[key] = value


    def get(self, key, default=None):
        if self.namespace_stack:
            namespace = self.namespace_stack[-1]
            return self.data.get(namespace, {}).get(key, default)
        return self.data.get(key, default)

    def enter_namespace(self, namespace):
        self.namespace_stack.append(namespace)
        if namespace not in self.data:
            self.data[namespace] = {}

    def exit_namespace(self):
        if self.namespace_stack:
            self.namespace_stack.pop()

    def __str__(self):
        return str(self.data)