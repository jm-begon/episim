import argparse, sys
import datetime

from episim.data import Outcome, State
from episim.parameters import PopulationBehavior, Confine
from episim.plot.multi_outcome import ComparatorDashboard
from episim.scenario import Scenario
from episim.plot import FullDashboard
from episim.model import SEIRS, SIR
from episim.virus import SARSCoV2Th


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--population_size", default=int(7 * 1e6),
                        type=int)
    parser.add_argument("-I", "--n_infectious", default=20, type=int)
    parser.add_argument("--n_days_total", default=243, type=int)
    parser.add_argument("--n_days_before_sanity_measures", default=30, type=int)
    parser.add_argument("--n_days_before_confinement", default=30, type=int)
    parser.add_argument("--n_days_confinement_duration", default=60, type=int)
    parser.add_argument("--sanitary_measure_effect", default=.5, type=float,
                        help="Factor by which the transmission rate is "
                             "multiplied (0 < x < 1")
    parser.add_argument("--confinement_effect", default=.1, type=float,
                        help="Factor by which the number of average daily"
                             "contact is multiplied (0 < x < 1)")
    parser.add_argument("-r", "--solver_resolution", default=0.1, type=float)
    parser.add_argument("--factory", choices=["SIR", "SEIRS"], default="SEIRS")


    args = parser.parse_args(argv)
    print(args)

    if args.factory == "SIR":
        factory = SIR.factory
    else:
        factory = SEIRS.factory


    N = args.population_size
    I = args.n_infectious
    res = args.solver_resolution
    T = args.n_days_total

    nd_bs = args.n_days_before_sanity_measures
    nd_as = T - nd_bs

    nd_bc = args.n_days_before_confinement
    nd_cd = args.n_days_confinement_duration
    nd_adc = T - nd_bc - nd_cd


    outcomes = []
    for scenario in NoIntervention(T, N, I, res), \
                    SanityMeasure(args.sanitary_measure_effect,
                                  nd_bs, nd_as, N, I, res), \
                    Confinement(args.confinement_effect,
                                nd_bc, nd_cd, nd_adc, N, I, res):
        outcomes.append(scenario.run_model(factory))

    ComparatorDashboard()(*outcomes).show()#.save("comparison.png")

    for i, outcome in enumerate(outcomes):
        FullDashboard()(outcome).show()#.save("dashboard_{}.png".format(i))

    # ComparatorDashboard()(*outcomes[1:]).show()


class BaseScenario(Scenario):
    def __init__(self, population_size, n_infectious, resolution,
                 virus=None, population=None, initial_date=None):
        self.resolution = resolution
        N = population_size
        I = n_infectious
        if initial_date is None:
            initial_date = datetime.date(2020, 1, 1)
        self.initial_state = State(N-I, 0, I, 0, initial_date, n_infection=I)
        if virus is None:
            virus = SARSCoV2Th()
        self.virus = virus
        if population is None:
            population = PopulationBehavior()
        self.population = population

    def get_model(self, factory, state=None, virus=None, population=None,
                  resolution=None):
        if state is None:
            state = self.initial_state
        if virus is None:
            virus = self.virus
        if population is None:
            population = self.population
        if resolution is None:
            resolution = self.resolution
        return factory(state, virus, population, resolution)


    def starting_description(self, model):
        descr_ls = [
            "Number of infectious    {:d} / {:d}    total population size"
            "".format(self.initial_state.infectious,
                      self.initial_state.population_size),
            "{}".format(self.virus),
            "Pop.: {}".format(self.population),
            "Model: {}".format(model)
        ]
        return self.multiline(descr_ls)



class NoIntervention(BaseScenario):
    def __init__(self, n_days, population_size, n_infectious, resolution):
        super().__init__(population_size, n_infectious, resolution)
        self.n_days = n_days

    def run_model(self, model_factory):
        model = self.get_model(model_factory)

        outcome = Outcome.from_model(model, self.n_days,
                                     self.starting_description(model))
        outcome.name = "Do nothing"
        return outcome


class SanityMeasure(BaseScenario):
    def __init__(self, measure_effect, n_days_before_measures,
                 n_days_after_measures, population_size, n_infectious,
                 resolution):
        super().__init__(population_size, n_infectious, resolution)
        self.n_days_1 = n_days_before_measures
        self.n_days_2 = n_days_after_measures
        self.measure_effect = measure_effect

    def run_model(self, model_factory):
        model = self.get_model(model_factory)
        outcome = Outcome.from_model(model, self.n_days_1,
                                     self.starting_description(model))

        model.beta *= self.measure_effect
        descr_ls = [
            "Sanity measures: dividing transmission rate by "
            "{:.2f}".format(1./self.measure_effect),
            "New model: {}".format(model)
        ]

        outcome = outcome.concat(
            Outcome.from_model(model, self.n_days_2,
                               self.multiline(descr_ls))
        )

        outcome.name = "Sanity measure (lower transmission rate)"
        return outcome


class Confinement(BaseScenario):
    def __init__(self, confinement_effect, n_days_before_confinement,
                 n_days_confinement, n_days_after_confinement,
                 population_size, n_infectious, resolution):
        super().__init__(population_size, n_infectious, resolution)
        self.confinement_efficiency = 1 - confinement_effect
        self.n_days_1 = n_days_before_confinement
        self.n_days_2 = n_days_confinement
        self.n_days_3 = n_days_after_confinement

    def run_model(self, model_factory):
        model = self.get_model(model_factory)

        outcome = Outcome.from_model(model, self.n_days_1,
                                     self.starting_description(model))

        population = Confine(self.population, self.confinement_efficiency)

        model = self.get_model(model_factory, state=outcome.last_state,
                               population=population)

        descr_ls = [
            "Confinement: {}".format(population),
            "New model: {}".format(model)
        ]

        outcome = outcome.concat(
            Outcome.from_model(model, self.n_days_2,
                               self.multiline(descr_ls))
        )

        model = self.get_model(model_factory, state=outcome.last_state)

        descr_ls = [
            "Deconfinement: {}".format(str(population)),
            "New model: {}".format(model)
        ]

        outcome = outcome.concat(
            Outcome.from_model(model, self.n_days_3,
                               self.multiline(descr_ls))
        )

        outcome.name = "Confine/deconfine"
        return outcome


if __name__ == '__main__':
    main()
    # TODO save in pdf




