import datetime

from .data import State, Outcome
from .parameters import PopulationBehavior
from .virus import SARSCoV2Th


class Scenario(object):
    @classmethod
    def default_initial_state(cls, population_size):
        I = 20
        return State(population_size-I, 0, I, 0, n_infection=I)

    @classmethod
    def default_initial_date(cls):
        return datetime.datetime(2020, 3, 1)


    def __init__(self, title=None):
        self.title = self.__class__.__name__ if title is None else title

    def run_model(self, model_factory):
        pass




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

        return Outcome.from_model(model, n_step, start_date,
                                  initial_state)
