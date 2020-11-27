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




