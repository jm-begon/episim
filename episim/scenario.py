import datetime
import os

from .data import State, Outcome
from .parameters import PopulationBehavior, Confine
from .virus import SARSCoV2Th


class Scenario(object):
    @classmethod
    def default_initial_state(cls, population_size, date=None):
        if date is None:
            date = cls.default_initial_date()
        I = 20
        return State(population_size-I, 0, I, 0, date, n_infection=I)

    @classmethod
    def default_initial_date(cls):
        return datetime.date(2020, 1, 1)


    def __init__(self, title=None):
        self.title = self.__class__.__name__ if title is None else title

    def run_model(self, model_factory):
        pass

    def multiline(self, ls):
        return os.linesep.join(ls)




class OneYearNoIntervention(Scenario):
    def run_model(self, model_factory):
        n_year = 10
        n_step = int(n_year * 365)
        # n_step = 30
        N = 11.5 * 1e6
        initial_state = self.__class__.default_initial_state(N)
        virus = SARSCoV2Th()
        population = PopulationBehavior()
        start_date = self.__class__.default_initial_date()

        model = model_factory(initial_state,  virus, population, 0.1)
        print(virus)
        print(model)

        return Outcome.from_model(model, n_step, start_date)


class Confinement(Scenario):
    def run_model(self, model_factory):
        n_days, n_days_after_confine, n_days_after_lift = 30, 60, 40

        N = 11.5 * 1e6
        initial_state = self.__class__.default_initial_state(N)
        virus = SARSCoV2Th()
        population = PopulationBehavior()

        model = model_factory(initial_state, virus, population, 0.1)
        # print(virus)
        # print(population)
        # print(model)

        descr_ls = [
            "Total population size: {:d}".format(int(N)),
            "{}".format(str(virus)),
            "Pop.: {}".format(str(population)),
            "Model: {}".format(str(model))
        ]


        outcome = Outcome.from_model(model, n_days, self.multiline(descr_ls))
        print("First", outcome.state_history[0])
        print("Last", outcome.state_history[-1])

        population = Confine(population, .9)

        model = model_factory(outcome.last_state, virus, population, 0.1)
        descr_ls = [
            "Confinement: {}".format(str(population)),
            "New model: {}".format(model)
        ]
        # print(model)
        outcome = outcome.concat(
            Outcome.from_model(model, n_days_after_confine,
                               self.multiline(descr_ls))
        )


        population = PopulationBehavior()
        model = model_factory(outcome.last_state, virus, population, 0.1)

        descr_ls = [
            "Deconfinement: {}".format(str(population)),
            "New model: {}".format(model)
        ]

        outcome = outcome.concat(
            Outcome.from_model(model, n_days_after_lift,
                               self.multiline(descr_ls))
        )


        return outcome

