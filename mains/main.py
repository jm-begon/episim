import datetime

from episim.data import Outcome, State
from episim.scenario import Scenario, OneYearNoIntervention, Confinement
from episim.plot import StateDashboard, FullDashboard
from episim.model import SEIRS, SIR


class SIRsc(Scenario):
    """
    From https://www.statsandr.com/blog/covid-19-in-belgium/ (15/11/2020)
    """
    def run_model(self, model_factory=None):
        # Basic SIR model
        n_days = 360
        N = 11.5 * 1e6
        I = 20
        initial_state = State(N-I, 0, I, 0, n_infection=I)


        model = SIR(
            beta=0.58,
            gamma=0.41,
        ).set_state(initial_state)

        model.resolution = 0.1


        return Outcome.from_model(model, n_days)

class SEIRSsc(Scenario):
    def run_model(self, model_factory=None):
        # Basic SIR model
        # n_days = 30
        n_days = 400
        N = 11.5 * 1e6
        I = 20
        initial_state = State(N-I, 0, I, 0, n_infection=I)
        print(initial_state)


        model = SEIRS(
            beta=0.5,
            kappa=0.25,
            gamma=1/7.,
            ksi=0.0021,
        ).set_state(initial_state)


        model.resolution = 10


        return Outcome.from_model(model, n_days)

if __name__ == '__main__':
    # outcome = SIRsc().run_model()
    # outcome = SEIRSsc().run_model()
    # outcome = OneYearNoIntervention().run_model(SEIRS.factory)
    outcome = Confinement().run_model(SEIRS.factory)
    # print(len(outcome.state_history))
    # plot = StatePlot()
    # plot = CumulStatePlot()
    # plot = StateDashboard()
    plot = FullDashboard()
    plot(outcome).show()


