
from .predicates import compare_value, contains_value


class BaseGenerator():
    
    def __init__(self):
        self.value = None
        self.noesis = None
        self.noema = None

    def __eq__(self, other):
        return compare_value(self, "==", other)

    def __ne__(self, other):
        return compare_value(self, "!=", other)

    def in_(self, options):
        return contains_value(self, options)

    def not_in(self, options):
        return contains_value(self, options, negate=True)

    def _record_automaton_value(self):
        try:
            from .automaton import record_current_value
        except ImportError:
            return
        record_current_value(self)
