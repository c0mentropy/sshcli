from collections import OrderedDict


class InnerDict(OrderedDict):
    def __getattr__(self, name):
        if name not in self.keys():
            return None
        return self[name]
    
    def __setattr__(self, name, value):
        self[name] = value
    
    def __str__(self):
        # return f"InnerDict({dict(self)})"
        return f"{list(self.keys())}"

    def __repr__(self):
        return f"InnerDict({repr(dict(self))})"
