import os

import numpy as np

from .plot import Plot, Dashboard, TwoAxesPlot


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


class DescriptionPlot(Plot):
    def set_dates(self, dates):
        return self

    def plot_outcome(self, outcome, color="k", title=None):
        # TODO better cut of lines
        limit = False
        text = []
        tab = "    > "
        contd = "       "
        for date, descr in outcome.date2descr.items():
            text.append(date.strftime("%d/%m/%y"))
            for line in descr.split(os.linesep):
                suffix = tab
                while len(line) > 85:
                    limit = True
                    text.append("{}{}".format(suffix, line[:85]))
                    suffix = contd
                    line = line[85:]
                text.append("{}{}".format(suffix, line))

        text = os.linesep.join(text)
        self.axes.text(0, 0, text, verticalalignment="bottom", color=color)  # TODO max size ~90
        # TODO https://matplotlib.org/3.1.1/gallery/pyplots/text_layout.html#sphx-glr-gallery-pyplots-text-layout-py

        if limit:
            # self.axes.axvline(len(outcome.state_history), linestyle=":", alpha=.1)
            pass

        if title is None:
            title = "Description"
        self.axes.set_title(title, color=color)
        self.axes.axis("off")

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
        # all_axes[0, 1].axis("off")
        # all_axes[0, 1].text(0.5, 0.5, "Population size: {}".format(outcome.population_size))
        title = "Description"
        if outcome.name:
            title = "{} -- {}".format(title, outcome.name)
        DescriptionPlot(all_axes[0, 1], self.convention)(outcome,
                                                         title=title)
        InfectionNumberPlot(
            all_axes[1, 1],
            self.convention
        )(outcome)
        InfectedPlot(all_axes[2, 1], self.convention)(outcome)
        self.figure.subplots_adjust(wspace=0.3)
        return self


