import math

import datetime

from .data import State


class EulerSimulator(object):
    """
    Explicit Euler method
    """
    def __init__(self, *dx_dt, step_size=1.):
        self.step_size = step_size
        self.dx_dt = dx_dt

    def __call__(self, *x, dt=1):
        next = list(x)
        n_steps_per_dt = int(1./self.step_size)
        for i in range(int(dt)):
            for t in range(n_steps_per_dt):
                for i, dxi_dt in enumerate(self.dx_dt):
                    next[i] += (self.step_size * dxi_dt(*x))
                x = tuple(next)
            yield x

        # yield x


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

    def _compute_reproduction_number(self, n_susceptible, n_total):
        return 0



    def set_state(self, state):
        R = self._compute_reproduction_number(state.susceptible,
                                              state.population_size)
        state.reproduction_number = R
        self.current_state = state
        return self


    def run(self, n_steps=1):
        for i in range(n_steps):
            yield self.current_state






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


        def S2E_f(S, E, I, R, _):
            # little hack to get the number of infected
            N = S + E + I + R
            return self.beta * S * I / N

        def dS_dt(S, E, I, R, _):
            N = S + E + I + R
            S2E = self.beta * S * I / N
            R2S = self.ksi * R
            return -S2E + R2S

        def dE_dt(S, E, I, R, _):
            N = S + E + I + R
            S2E = self.beta * S * I / N
            E2I = self.kappa * E
            return S2E -E2I

        def dI_dt(S, E, I, R, _):
            E2I = self.kappa * E
            I2R = self.gamma * I
            return E2I - I2R

        def dR_dt(S, E, I, R, _):
            R2S = self.ksi * R
            I2R = self.gamma * I
            return I2R - R2S



        self.simulator = EulerSimulator(dS_dt, dE_dt, dI_dt, dR_dt, S2E_f,
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



    def _compute_reproduction_number(self, n_susceptible, n_total):
        return self.beta / self.gamma * n_susceptible / float(n_total)


    def run(self, n_steps=1):
        S, E, I, R = self.current_state
        N = self.current_state.population_size
        date = self.current_state.date
        plus_one = datetime.timedelta(days=1)
        n_infection = self.current_state.n_infection

        for Sp, Ep, Ip, Rp, n_new_infection in self.simulator(S, E, I, R, n_infection, dt=n_steps):
            S, E, I, R = Sp, Ep, Ip, Rp


            date = date + plus_one
            state = State(S, E, I, R, date, n_infection=n_new_infection)

            if math.fabs(N - S - E - I - R) > 1e-5:
                raise ValueError("Conservation error: {} =/= {}".format(N, S + E + I + R))

            self.set_state(state)

            yield state





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

        def dS_dt(S, I, R):
            N = S + I + R
            S2I = self.beta * S * I / N
            return -S2I

        def dI_dt(S, I, R):
            N = S + I + R
            S2I = self.beta * S * I / N
            I2R = self.gamma * I
            return S2I - I2R

        def dR_dt(S, I, R):
            I2R = self.gamma * I
            return I2R

        self.simulator = EulerSimulator(dS_dt, dI_dt, dR_dt,
                                        step_size=resolution)

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



    def run(self, n_steps=1):

        S, E, I, R = self.current_state
        N = self.current_state.population_size
        n_infection = self.current_state.n_infection
        date = self.current_state.date
        plus_one = datetime.timedelta(days=1)

        for Sp, Ip, Rp in self.simulator(S, I, R, dt=n_steps):
            n_infection += (S - Sp)
            S, I, R = Sp, Ip, Rp

            date = date + plus_one
            state = State(S, E, I, R, date, n_infection=n_infection)

            if math.fabs(N - S - E - I - R) > 1e-5:
                raise ValueError("Conservation error: {} =/= {}".format(N, S + E + I + R))

            self.set_state(state)

            yield state

