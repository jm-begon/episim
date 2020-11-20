import datetime
from abc import ABCMeta

from matplotlib import pyplot as plt


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

    def show(self):
        plt.show()
        return self

    def close(self):
        pass

    def __call__(self, *outcomes):
        return self



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

    def __call__(self, *outcomes):
        for plot in self.plots:
            for outcome in outcomes:
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

    def __call__(self, *outcomes):
        for outcome in outcomes:
            self.plot_outcome(outcome)
        self.set_dates(outcomes[0].dates)
        return self

    def plot_outcome(self, outcome, *args, **kwargs):
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




