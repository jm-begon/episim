import datetime

from episim.data import Outcome, State
from episim.parameters import PopulationBehavior, Confine, WearingMask
from episim.plot.multi_outcome import ComparatorDashboard
from episim.scenario import Scenario
from episim.plot import FullDashboard
from episim.model import SEIRS
from episim.virus import SARSCoV2Th
from copy import deepcopy

N = 11.5 * 1e6
I = 20
INITIAL_STATE = State(N-I, 0, I, 0, datetime.date(2020, 1, 1), n_infection=I)
N_DAYS = 30, 60, 40
VIRUS = SARSCoV2Th()
POP = PopulationBehavior()



class NoIntervention(Scenario):
    def run_model(self, model_factory):
        n_days = sum(N_DAYS)
        initial_state = deepcopy(INITIAL_STATE)


        model = model_factory(initial_state, VIRUS, POP, 0.1)
        descr_ls = [
            "Total population size: {:d}".format(int(N)),
            "Initial state: {}".format(initial_state),
            "{}".format(VIRUS),
            "Pop.: {}".format(POP),
            "Model: {}".format(model)
        ]
        outcome = Outcome.from_model(model, n_days, self.multiline(descr_ls))
        return outcome


class Mask(Scenario):
    def run_model(self, model_factory):
        without_mask = N_DAYS[0]
        with_mask = sum(N_DAYS) - without_mask

        initial_state = deepcopy(INITIAL_STATE)

        model = model_factory(initial_state, VIRUS, POP, 0.1)
        descr_ls = [
            "Total population size: {:d}".format(int(N)),
            "Initial state: {}".format(initial_state),
            "{}".format(VIRUS),
            "Pop.: {}".format(POP),
            "Model: {}".format(model)
        ]
        outcome = Outcome.from_model(model, without_mask, self.multiline(descr_ls))

        virus = WearingMask(VIRUS)
        model = model_factory(outcome.last_state, virus, POP, 0.1)
        descr_ls = [
            "Wearing masks: {}".format(virus),
            "NEw model: {}".format(model)
        ]

        outcome = outcome.concat(
            Outcome.from_model(model, with_mask,
                               self.multiline(descr_ls))
        )

        return outcome


class Confinement(Scenario):
    def run_model(self, model_factory):
        n_days, n_days_after_confine, n_days_after_lift = N_DAYS
        initial_state = deepcopy(INITIAL_STATE)


        model = model_factory(initial_state, VIRUS, POP, 0.1)

        descr_ls = [
            "Total population size: {:d}".format(int(N)),
            "Initial state: {}".format(initial_state),
            "{}".format(VIRUS),
            "Pop.: {}".format(POP),
            "Model: {}".format(model)
        ]


        outcome = Outcome.from_model(model, n_days, self.multiline(descr_ls))

        population = Confine(POP, .9)

        model = model_factory(outcome.last_state, VIRUS, population, 0.1)
        descr_ls = [
            "Confinement: {}".format(population),
            "New model: {}".format(model)
        ]

        outcome = outcome.concat(
            Outcome.from_model(model, n_days_after_confine,
                               self.multiline(descr_ls))
        )

        model = model_factory(outcome.last_state, VIRUS, POP, 0.1)

        descr_ls = [
            "Deconfinement: {}".format(str(population)),
            "New model: {}".format(model)
        ]

        outcome = outcome.concat(
            Outcome.from_model(model, n_days_after_lift,
                               self.multiline(descr_ls))
        )


        return outcome


if __name__ == '__main__':
    # TODO args
    # TODO save in pdf

    outcomes = []
    for scenario in NoIntervention(), Mask(), Confinement():
        outcomes.append(scenario.run_model(SEIRS.factory))

    for outcome in outcomes:
        FullDashboard()(outcome).show()

    ComparatorDashboard()(*outcomes).show()
