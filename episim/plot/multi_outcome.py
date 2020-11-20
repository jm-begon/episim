import numpy as np
from matplotlib import pyplot as plt

from .plot import Plot, Convention


class Colormap(Convention):
    # https://matplotlib.org/tutorials/colors/colormaps.html
    def __init__(self, n_colors, plt_name="tab10"):
        self.cmap = plt.get_cmap(plt_name)

    def yield_colors(self, n_colors):
        colors = self.cmap(np.linspace(0., 1., n_colors))
        for color in colors:
            yield color


class MultiOutputPlot(Plot):
    def __init__(self, ax=None, colormap=None):
        if colormap is None:
            colormap = Colormap()
        super().__init__(ax, colormap)


class FromSingle(Plot):
    def __call__(self, *outcomes):
        for color, outcome in zip(self.convention.yield_colors(len(outcomes)),
                                  outcomes):
            self.plot_outcome(outcome, color=color)
            self.set_dates(outcomes[0].dates)
            return self
