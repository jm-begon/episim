from copy import deepcopy as clone
from collections import OrderedDict

class State(object):
    def __init__(self, susceptible, exposed, infectious, recovered, date,
                 reproduction_number=None, n_infection=0):
        self.susceptible = susceptible
        self.exposed = exposed
        self.infectious = infectious
        self.recovered = recovered
        self.date = date
        self.reproduction_number = reproduction_number
        self.n_infection = n_infection

    @property
    def infected(self):
        return self.exposed + self.infectious

    @property
    def population_size(self):
        return self.susceptible + self.exposed + self.infectious + self.recovered

    def __repr__(self):
        return "{}({}, {}, {}, {}, {}, {}, {})".format(
            self.__class__.__name__,
            repr(self.susceptible),
            repr(self.exposed),
            repr(self.infectious),
            repr(self.recovered),
            repr(self.date),
            repr(self.reproduction_number),
            repr(self.n_infection)
        )

    def __iter__(self):
        yield self.susceptible
        yield self.exposed
        yield self.infectious
        yield self.recovered

    def __sub__(self, other):
        S1, E1, I1, R1 = self
        RN1, NI1 = self.reproduction_number, self.n_infection

        S2, E2, I2, R2 = other
        RN2, NI2 = other.reproduction_number, other.n_infection

        if RN1 is None or RN2 is None:
            dRN = None
        else:
            dRN = RN1-RN2

        return StateDelta(S1-S2, E1-E2, I1-I2, R1-R2, dRN, NI1-NI2)


class Compartment(object):
    def __init__(self, name):
        self.name = name
        self.parent = None
        self.cumul = None

    @property
    def size(self):
        return 0

    def __iter__(self):
        return self,


class Leaf(Compartment):
    def __init__(self, name, size):
        super().__init__(name)
        self._size = size

    @property
    def size(self):
        return self._size


class Node(Compartment):
    def __init__(self, name, *children):
        super().__init__(name)
        self.children = list(children)
        for child in self.children:
            child.parent = self

    @property
    def size(self):
        return sum(child.size for child in self.children)

    def __iter__(self):
        for child in self.children:
            for x in child:
                yield x

    def add_child(self, compartment):
        self.children.append(compartment)


class Hierarchy(object):
    def __init__(self):
        self.root = Node("population")
        self.shorcut = {}

    def __setattr__(self, key, value):
        if key in {"root", "shortcut"}:
            return super().__setattr__(key, value)



    def __getattr__(self, key):
        # https://stackoverflow.com/questions/3278077/difference-between-getattr-vs-getattribute
        compartment = self.shorcut.get(key)
        if compartment is None:
            pass  # TODO look everywhere

        if compartment is not None:
            return compartment

        raise AttributeError("'{}' object has no attribute '{}'"
                             "".format(self.__class__.__name__, key))





class StateDelta(State):
    pass






class Outcome(object):
    @classmethod
    def from_model(cls, model, steps, description=""):
        history = [model.current_state]
        start_date = model.current_state.date
        for state in model.run(steps):
            history.append(state)
        return cls(history, start_date, description)

    def __init__(self, state_history, start_date, description=""):
        self.state_history = state_history
        self.date2descr = OrderedDict()
        self.date2descr[start_date] = description
        self.name = None

    @property
    def last_state(self):
        return self.state_history[-1]

    @property
    def dates(self):
        return list(self.date2descr.keys())

    @property
    def start_date(self):
        for date in self.date2descr.keys():
            return date

    @property
    def n_infection(self):
        return self.state_history[-1].n_infection

    @property
    def population_size(self):
        return self.state_history[0].population_size

    def concat(self, outcome, copy=True):
        o = self
        if copy:
            o = clone(o)
        o.state_history.extend(outcome.state_history[1:])
        for date, descr in outcome.date2descr.items():
            o.date2descr[date] = descr
        return o

    def get_dated_descriptions(self):
        import os
        # TODO datetime + move
        return os.linesep.join(["{} - {}".format(k, v) for k, v in self.date2descr.items()])




