import os
import datetime

from collections import defaultdict

import numpy as np
from scipy import sparse

from episim.ontology import Ontology
from episim.plot.modeling import System, Accumulator
from .data import State


class EulerSimulator(object):
    """
    Explicit Euler method
    """
    def __init__(self, *dx_dt, step_size=1.):
        self.step_size = step_size
        self.dx_dt = dx_dt
        self.N = len(dx_dt)

    def __call__(self, *x, dt=1):
        dx = np.zeros(self.N)
        h = self.step_size
        x = np.array(x)

        n_steps_per_dt = int(1. / self.step_size)
        for i in range(int(dt)):
            for t in range(n_steps_per_dt):
                for i, dxi_dt in enumerate(self.dx_dt):
                    dx[i] = dxi_dt(*x)
                x = x + h * dx
            yield x



class LinNonLinEulerSimulator(object):
    """
    P : p
    """
    def __init__(self, dx_dt_lin, dx_dt_dict, step_size=1.):
        if hasattr(M, "tocsr"):
            dx_dt_lin = dx_dt_lin.tocsr()
        self.dx_dt_matrix = dx_dt_lin
        self.dx_dt_dict = dx_dt_dict
        self.N = len(dx_dt_lin)
        self.step_size = step_size


    def __call__(self, *x, dt=1):
        dx = np.zeros(self.N)
        x = np.array(x)
        h = self.step_size

        n_steps_per_dt = int(1. / self.step_size)
        for i in range(int(dt)):
            for t in range(n_steps_per_dt):
                dx *= 0
                # Linear part
                dx[:] = self.dx_dt_matrix.dot(x)

                # Non linear
                for i, f in self.dx_dt_dict.items():
                    dx[i] += f(*x)

                x = x + h * dx
            yield x


class F(object):
    def __init__(self, callable, label):
        self.label = label
        self.callable = callable

    def __call__(self, *args, **kwargs):
        return self.callable(*args, **kwargs)

    def __str__(self):
        return self.label


class Dynamic(object):
    @classmethod
    def from_nodes(cls, *node_and_time_deriv):
        nodes = []
        dx_dt = []
        for node, dxi_dt in node_and_time_deriv:
            nodes.append(node)
            dx_dt.append(dxi_dt)

        sorted_nodes = [x for x in nodes]
        sorted_nodes.sort(key=lambda n: n.index)
        names = [x.name for x in sorted_nodes]
        dynamic = cls(*names)

        for name, dxi_dt in zip(names, dx_dt):
            dynamic[name] = dxi_dt

        return dynamic

    def __init__(self, *variable_names):
        self.variable_names = variable_names
        self.var2idx = {s: i for i, s in enumerate(variable_names)}
        self.dx_dt = [F(lambda *x: 0, "0") for _ in range(len(variable_names))]

    def _idx(self, key):
        try:
            idx = int(key)
        except (TypeError, ValueError):
            idx = self.var2idx[key]
        return idx

    def __setitem__(self, key, value):
        self.dx_dt[self._idx(key)] = value

    def __getitem__(self, item):
        return self.dx_dt[self._idx(item)]

    def long_repr(self):
        s = ""
        for idx, name in enumerate(self.variable_names):
            s += "d{}/dt = {}{}".format(name, self.dx_dt[idx], os.linesep)

        return s

    def __iter__(self):
        return iter(self.dx_dt)



class Model(object):
    @classmethod
    def compute_parameters(cls, virus, population):
        return tuple()

    @classmethod
    def factory(cls, initial_state, virus, population, resolution=0.1):
        t = cls.compute_parameters(virus, population)
        model = cls(*t, resolution=resolution)
        return model.set_state(initial_state)


    def __init__(self, resolution=0.1):
        self.current_state = None
        self.resolution = resolution
        self.ontology = Ontology.default_ontology()

    def _compute_reproduction_number(self, n_susceptible, n_total):
        return 0


    def set_state(self, state):
        queriable = self.ontology(state)
        R = self._compute_reproduction_number(queriable.susceptible,
                                              queriable.population)
        state.reproduction_number = R
        if state.n_infection is None:
            state.n_infection = queriable.infected
        self.current_state = state
        return self

    def _state2variables(self, state):
        return tuple()

    def _variables2state(self, date, *values):
        return State(date)

    def run(self, n_steps=1):
        variables = self._state2variables(self.current_state)

        date = self.current_state.date
        plus_one = datetime.timedelta(days=1)

        for variables in self.simulator(*variables, dt=n_steps):

            date = date + plus_one

            state = self._variables2state(date, *variables)

            self.set_state(state)

            yield state







class SEIRS(Model):
    """
    beta: float
        transmission coefficient: average number of contact per person per time,
        multiplied by the probability of disease transmission at a contact
        between a susceptible person and an infectious person

    gamma: float
        1/D, where D is the average time infectious time

    ksi:
        re-susceptibility rate (depends on the fraction of alive, recovered
        people will not develop a lasting immunity and  depends on the time
        before the immunity drops)

    """
    @classmethod
    def compute_parameters(cls, virus, population):
        beta = population.contact_frequency * virus.transmission_rate
        kappa = 1. / virus.exposed_duration
        gamma = 1. / virus.infectious_duration
        ksi = virus.immunity_drop_rate
        return beta, kappa, gamma, ksi


    def __init__(self, beta=0, kappa=0, gamma=0, ksi=0, resolution=0.1):
        if resolution is None:
            resolution = EulerSimulator
        super().__init__(resolution=resolution)
        self.beta = beta
        self.kappa = kappa
        self.gamma = gamma
        self.ksi = ksi

        self.current_state = None



        S, E, I, R = System.new("S", "E", "I", "R")
        N = S + E + I + R
        N.override_name("N")

        S2E = self.beta * S * I / N
        S2E_acc = Accumulator(S2E, self.resolution)

        E2I = self.kappa * E
        I2R = self.gamma * I
        R2S = self.ksi * R

        dS_dt = -S2E + R2S
        dE_dt = S2E_acc - E2I
        dI_dt = E2I - I2R
        dR_dt  = I2R - R2S


        self.dynamic = Dynamic.from_nodes((S, dS_dt), (E, dE_dt),
                                          (I, dI_dt), (R, dR_dt))

        self.acc_n_infect = S2E_acc


        self.simulator = EulerSimulator(*iter(self.dynamic),
                                        step_size=resolution)



    def __repr__(self):
        s = "{}(beta={}, kappa={}, gamma={}, ksi={}, resolution={})".format(
            self.__class__.__name__,
            repr(self.beta),
            repr(self.kappa),
            repr(self.gamma),
            repr(self.ksi),
            repr(self.resolution),
        )
        if self.current_state is None:
            return s

        return s + ".set_state({})".format(repr(self.current_state))

    def __str__(self):
        return  "{}(beta={:.2e}, kappa={:.2e}, gamma={:.2e}, ksi={:.2e})" \
                "".format(self.__class__.__name__,
                          self.beta, self.kappa,
                          self.gamma, self.ksi)

    # def __str__(self):
    #     return self.dynamic.long_repr()



    def _compute_reproduction_number(self, n_susceptible, n_total):
        return self.beta / self.gamma * n_susceptible / float(n_total)

    def _state2variables(self, state):
        zero = lambda x: 0 if x is None else x
        S = zero(state.susceptible)
        E = zero(state.exposed)
        I = zero(state.infectious)
        R = zero(state.recovered)

        return S, E, I, R


    def _variables2state(self, date, *values):
        S, E, I, R = values

        n_infection = self.current_state.n_infection
        n_infection += self.acc_n_infect.value
        self.acc_n_infect.reset()

        state = State(date)
        state.susceptible = S
        state.exposed = E
        state.infectious = I
        state.recovered = R
        state.n_infection = n_infection

        return state







class SIR(Model):
    @classmethod
    def compute_parameters(cls, virus, population):
        beta = population.contact_frequency * virus.transmission_rate
        gamma = 1. / (virus.exposed_duration + virus.infectious_duration)

        return beta, gamma

    def __init__(self, beta, gamma, resolution=0.1):
        super().__init__(resolution)
        self.beta = beta
        self.gamma = gamma

        S, I, R = System.new("S", "I", "R")
        N = S + I + R
        N.override_name("N")

        S2I = self.beta * S * I / N
        I2R = self.gamma * I

        dS_dt = -S2I
        dI_dt = S2I - I2R
        dR_dt = I2R

        self.dynamic = Dynamic.from_nodes((S, dS_dt), (I, dI_dt), (R, dR_dt))


        self.simulator = EulerSimulator(iter(self.dynamic), resolution)


    def __repr__(self):
        s = "{}(beta={}, gamma={}, resolution={})".format(
            self.__class__.__name__,
            repr(self.beta),
            repr(self.gamma),
            repr(self.resolution),
        )
        if self.current_state is None:
            return s

        return s + ".set_state({})".format(repr(self.current_state))


    def __str__(self):
        return  "{}(beta={:.2e}, gamma={:.2e})" \
                "".format(self.__class__.__name__,
                          self.beta, self.gamma)


    def _compute_reproduction_number(self, n_susceptible, n_total):
        return self.beta / self.gamma * n_susceptible / float(n_total)


    def _state2variables(self, state):
        zero = lambda x: 0 if x is None else x
        S = zero(state.susceptible)
        I = zero(state.infectious)
        R = zero(state.recovered)

        return S, I, R


    def _variables2state(self, date, *values):
        S, I, R = values

        n_infection = self.current_state.n_infection
        n_infection += (self.current_state.susceptible - S)

        state = State(date)
        state.susceptible = S
        state.infectious = I
        state.recovered = R
        state.n_infection = n_infection

        return state

