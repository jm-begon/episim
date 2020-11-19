from abc import ABCMeta

import datetime
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

import numpy as np


class Convention(object):
    @property
    def susceptible_color(self):
        return "limegreen"

    @property
    def exposed_color(self):
        return "orange"

    @property
    def infectious_color(self):
        return "crimson"

    @property
    def infected_color(self):
        return "magenta"

    @property
    def recovered_color(self):
        return "dodgerBlue"

class BasePlot(object):
    def __init__(self, convention=None):
        if convention is None:
            convention = Convention()
        self._convention = convention

    @property
    def convention(self):
        return self._convention

    def __call__(self, outcome):
        return self

    def show(self):
        plt.show()
        return self

    def close(self):
        pass


class Dashboard(BasePlot):
    def __init__(self, fig=None, convention=None):
        self._own_fig = False
        if fig is None:
            fig = plt.figure(figsize=(20, 10))  # https://stackoverflow.com/questions/12439588/how-to-maximize-a-plt-show-window-using-python
            self._own_fig = True

        self._fig = fig

        super().__init__(convention)



    def close(self):
        if self._own_fig:
            plt.close(self._fig)


    @property
    def figure(self):
        return self._fig


class CustomDashboard(Dashboard):
    def __init__(self, fact_array, fig=None, convention=None):
        super().__init__(fig, convention)
        n_rows = len(fact_array)
        n_cols = len(fact_array[0])
        all_axes = self.figure.subplots(n_rows, n_cols, sharex=True)

        self.plots = []

        for r, row in enumerate(fact_array):
            for c, factory in enumerate(row):
                ax = all_axes[r, c]
                plot = factory(ax)
                self.plots.append(plot)

    def __call__(self, outcome):
        for plot in self.plots:
            plot.plot_outcome(outcome)
        return self




class Plot(BasePlot, metaclass=ABCMeta):
    def __init__(self, ax=None, convention=None):
        self._layout = None
        if ax is None:
            self._layout = Dashboard()
            ax = self._layout.figure.gca()
        self._axes = ax

        super().__init__(convention)

    @property
    def axes(self):
        return self._axes


    def close(self):
        if self._layout is not None:
            self._layout.close()

    def set_dates(self, dates):
        xticks = self.axes.get_xticks()
        start_date = dates[0]
        tick_dates = [start_date + datetime.timedelta(days=x) for x in xticks]
        date_strs = [d.strftime("%d/%m/%y") for d in tick_dates]
        self.axes.set_xticklabels(date_strs, rotation="vertical")

        for date in dates[1:]:
            x = (date-start_date).days
            self.axes.axvline(x, color="k", alpha=.5, linestyle="--")

    def __call__(self, outcome):
        self.plot_outcome(outcome)
        self.set_dates(outcome.dates)
        return self

    def plot_outcome(self, outcome):
        return self




class TwoAxesPlot(Plot):
    def __init__(self, ax, factory_1, color_1, factory_2, color_2,
                 title="",
                 convention=None):
        super().__init__(ax, convention=convention)
        self.plot1 = factory_1(ax, convention=convention)
        self.plot2 = factory_2(ax.twinx(), convention=convention)
        self.color_1 = color_1
        self.color_2 = color_2
        self.title = title

    def plot_outcome(self, outcome):
        self.plot1.plot_outcome(outcome, color=self.color_1, title="")
        self.plot2.plot_outcome(outcome, color=self.color_2, title="")
        self.axes.set_title(self.title)




class StatePlot(Plot):
    def plot_outcome(self, outcome):
        states = outcome.state_history
        t = np.arange(len(states))
        N = outcome.population_size


        # rates
        s = np.array([s.susceptible for s in states]) / N
        e = np.array([s.exposed for s in states]) / N
        i = np.array([s.infectious for s in states]) / N
        r = np.array([s.recovered for s in states]) / N

        self.axes.plot(t, s, color=self.convention.susceptible_color,
                       label="Susceptible")
        if e.max() > 0:
            self.axes.plot(t, e, color=self.convention.exposed_color,
                           label="Exposed")
        self.axes.plot(t, i, color=self.convention.infectious_color,
                       label="Infectious")
        self.axes.plot(t, r, color=self.convention.recovered_color,
                       label="Recovered")

        self.axes.set_ylabel("Percentage of population")

        self.set_dates(outcome.dates)

        self.axes.grid(True)
        self.axes.legend(loc="best")
        self.axes.set_title("State distribution with respect to time")
        return self




class CumulStatePlot(Plot):
    def plot_outcome(self, outcome):
        alpha = .25
        states = outcome.state_history
        t = np.arange(len(states))
        N = outcome.population_size

        # rates
        s = np.array([s.susceptible for s in states]) / N
        e = np.array([s.exposed for s in states]) / N
        i = np.array([s.infectious for s in states]) / N
        r = np.array([s.recovered for s in states]) / N

        lower = 0
        higher = lower + s
        self.axes.plot(t, higher, label="Susceptible",
                       color=self.convention.susceptible_color)
        self.axes.fill_between(t, lower, higher,
                               color=self.convention.susceptible_color,
                               alpha=alpha)
        lower = higher
        higher = higher + e
        if e.max() > 0:
            self.axes.plot(t, higher, label="Exposed",
                           color=self.convention.exposed_color)
            self.axes.fill_between(t, lower, higher,
                                   color=self.convention.exposed_color,
                                   alpha=alpha)

        lower = higher
        higher = higher + i
        self.axes.plot(t, higher, label="Infectious",
                       color=self.convention.infectious_color)
        self.axes.fill_between(t, lower, higher,
                               color=self.convention.infectious_color,
                               alpha=alpha)

        lower = higher
        higher = higher + r
        self.axes.plot(t, higher, label="Recovered",
                       color=self.convention.recovered_color)
        self.axes.fill_between(t, lower, higher,
                               color=self.convention.recovered_color,
                               alpha=alpha)

        self.axes.set_ylabel("Percentage of population")

        self.axes.grid(True)
        self.axes.legend(loc="lower left")
        self.axes.set_title("Cumulative distribution with respect to time")
        return self


class InfectedPlot(Plot):
    def plot_outcome(self, outcome):
        states = outcome.state_history
        t = np.arange(len(states))

        # rates
        e = np.array([s.exposed for s in states])
        i = np.array([s.infectious for s in states])

        if e.max() > 0:
            self.axes.plot(t, e, color=self.convention.exposed_color,
                           label="Exposed")
        self.axes.plot(t, i, color=self.convention.infectious_color,
                       label="Infectious")

        self.axes.set_ylabel("Number of infection")

        self.set_dates(outcome.dates)

        self.axes.grid(True)
        self.axes.legend(loc="best")
        self.axes.set_title("Number of infected people with respect to time")
        return self



class ReproductionNumberPlot(Plot):
    @property
    def default_title(self):
        return "Reproduction number (R)"

    def plot_outcome(self, outcome, color="k", title=None):
        states = outcome.state_history
        t = np.arange(len(states))
        R = np.array([s.reproduction_number for s in states])

        self.axes.plot(t, R, color=color)
        self.axes.set_ylabel("Reproduction number", color=color)
        self.axes.tick_params(axis='y', labelcolor=color)
        self.axes.grid(True, color=color, alpha=.25)
        self.axes.axhline(1, 0, 1, color=color, linestyle="--", alpha=.5)
        if title is None:
            title = self.default_title
        self.axes.set_title(title)
        return self


class InfectionNumberPlot(Plot):
    @property
    def default_title(self):
        return "Percentage of cumulattive infection"
    def plot_outcome(self, outcome, color="k", title=None):
        states = outcome.state_history
        N = outcome.population_size
        t = np.arange(len(states))
        R = np.array([s.n_infection for s in states]) / N

        self.axes.plot(t, R, color=color)
        self.axes.set_ylabel("Perc. cumul. infection", color=color)
        self.axes.tick_params(axis='y', labelcolor=color)
        self.axes.axhline(1, 0, 1, color=color, linestyle="--", alpha=.5)
        self.axes.grid(True, color=color, alpha=.25)
        if title is None:
            title = self.default_title
        self.axes.set_title(title)
        return self


class RiskyContactPlot(Plot):
    """
    Let S be the number of succeptible, I be the number of infected, k
    be the average number of daily contact between any two people and
    N be the population size.

    The number of risky contact is: RC = k S I/N
        for any succeptible individual, it has a I/N chances to have a contact
        with a infectious person and there are k of such contacts (assuming
        independence and uniform distribution)

    The total number of contact is: TC = k N
        any person has k contact (well, on average)

    So the proportion of risky contact is: RC/TC = S I / N^2
    """
    def plot_outcome(self, outcome, color="k", title=None):
        states = outcome.state_history
        t = np.arange(len(states))
        N = outcome.population_size
        # N = 1

        # rates
        s = np.array([s.susceptible for s in states])
        i = np.array([s.infectious for s in states])

        y = s * i / N**2


        self.axes.plot(t, y, color=color)
        self.axes.set_ylabel("Risky contact rate (pop. level)", color=color)
        self.axes.tick_params(axis='y', labelcolor=color)

        self.axes.grid(True, color=color, alpha=.25)

        if title is None:
            title = "TODO"
        self.axes.set_title(title)




class StateDashboard(Dashboard):

    def __call__(self, outcome):
        ax1, ax2, ax3 = self.figure.subplots(3, 1, sharex=True)
        StatePlot(ax1, self.convention)(outcome)
        CumulStatePlot(ax2, self.convention)(outcome)
        TwoAxesPlot(ax3,
                    ReproductionNumberPlot, "dodgerblue",
                    RiskyContactPlot, "orange")(outcome)


        return self


class FullDashboard(Dashboard):
    def __call__(self, outcome):
        all_axes = self.figure.subplots(3, 2, sharex=True)

        # First column
        StatePlot(all_axes[0, 0], self.convention)(outcome)
        CumulStatePlot(all_axes[1, 0], self.convention)(outcome)
        TwoAxesPlot(all_axes[2, 0],
                    ReproductionNumberPlot, "royalblue",
                    RiskyContactPlot, "darkorange")(outcome)

        # Second column
        all_axes[0, 1].axis("off")
        all_axes[0, 1].text(0.5, 0.5, "Population size: {}".format(outcome.population_size))
        InfectionNumberPlot(
            all_axes[1, 1],
            self.convention
        )(outcome)
        InfectedPlot(all_axes[2, 1], self.convention)(outcome)
        self.figure.subplots_adjust(wspace=0.3)
        return self




