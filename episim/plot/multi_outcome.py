import numpy as np

from .plot import Plot, Dashboard
from .single_outcome import DescriptionPlot

def index_color_outcome(convention, outcomes):
    for i, (c, o) in enumerate(zip(convention.yield_colors(len(outcomes)),
                                  outcomes)):
        yield i, c, o


class MultiOutputPlot(Plot):
    def __call__(self, *outcomes):
        for i, c, o in index_color_outcome(self.convention, outcomes):
            self.plot_outcome(o, color=c, label="Outcome {:d}".format(i+1))
            self.set_dates(o.dates)
        self.pack()
        return self

    def pack(self):
        pass

class ReproductionNumberMPlot(MultiOutputPlot):
    def plot_outcome(self, outcome, color="k", label=None, **kwargs):
        states = outcome.state_history
        t = np.arange(len(states))
        R = np.array([s.reproduction_number for s in states])

        self.axes.plot(t, R, color=color, label=label)

    def pack(self):
        self.axes.set_title("Reproduction number")
        self.axes.axhline(1, 0, 1, linestyle="--", alpha=.5)
        self.axes.grid(True)



class InfectedMPlot(MultiOutputPlot):
    def plot_outcome(self, outcome, color="k", label=None, **kwargs):
        t = np.arange(len(outcome))

        # rates
        i = np.array([s.infected for s in outcome])

        self.axes.plot(t, i, color=color, label=label)

    def pack(self):
        self.axes.set_title("Number of infections (E+I)")
        self.axes.grid(True)


class InfectionNumberMPlot(MultiOutputPlot):
    def plot_outcome(self, outcome, color="k", label=None, **kwargs):
        states = outcome.state_history
        N = outcome.population_size
        t = np.arange(len(states))
        R = np.array([s.n_infection for s in states]) / N

        self.axes.plot(t, R, color=color)


    def pack(self):
        self.axes.set_title("Percentage of cumulative infection")
        self.axes.grid(True)






class ComparatorDashboard(Dashboard):
    def __call__(self, *outcomes):
        if len(outcomes) > 3:
            raise ValueError("At most 3 outcomtes for this dashboard")

        all_axes = self.figure.subplots(3, 2, sharex=True)

        # First Column
        InfectedMPlot(all_axes[0, 0], self.convention)(*outcomes)
        InfectionNumberMPlot(all_axes[1, 0], self.convention)(*outcomes)
        ReproductionNumberMPlot(all_axes[2, 0], self.convention)(*outcomes)

        for i, c, o in index_color_outcome(self.convention, outcomes):
            title = o.name if o.name else "Outcome {:d}".format(i+1)
            DescriptionPlot(all_axes[i, 1],
                            self.convention).plot_outcome(o, color=c, title=title)

        for i in range(3-len(outcomes)+1, 3):
            all_axes[i, 1].axis("off")

        return self








