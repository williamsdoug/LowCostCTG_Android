#
#  Copyright Douglas Williams, 2017
#  All Rights Reserved
#

from kivy_garden_graph import Graph, MeshLinePlot, LinePlot
from kivy_garden_graph import SmoothLinePlot

from kivy_garden_graph import Plot
from kivy.graphics import Line, RenderContext, Color, Ellipse, Point

from kivy.utils import get_color_from_hex as rgb

from pprint import pprint
import numpy as np
import collections
import math

# see also: https://en.wikipedia.org/wiki/Web_colors#X11_color_names
COLORS = {'white': [1, 1, 1, 1],
          'silver': [0.75, 0.75, 0.75, 1],
          'gray': [0.5, 0.5, 0.5, 1],
          'black': [0, 0, 0, 1],
          'red': [1, 0, 0, 1],
          'maroon': [0.5, 0, 0, 1],
          'yellow': [1, 1, 0, 1],
          'olive': [0.5, 0.5, 0, 1],
          'lime': [0, 1, 0, 1],
          'green': [0, 0.5, 0, 1],
          'cyan': [0, 1, 1, 1],
          'aqua': [0, 1, 1, 1],
          'teal': [0, 0.5, 0.5, 1],
          'blue': [0, 0, 1, 1],
          'navy': [0, 0, 0.5, 1],
          'fuchia': [1, 0, 1, 1],
          'magenta': [1, 0, 1, 1],
          'purple': [0.5, 0, 0.5, 1],
          'orange': [1, 0.65, 0, 1],
          'deeppink': [1, 20.0 / 255, 147.0 / 255],
          }

DEFAULT_PLOT_COLOR = 'white'


class ScatterPlot(Plot):
    '''ScatterPlot draws using a standard Point object.
    '''

    '''Args:
    line_width (float) - the width of the graph line
    '''
    def __init__(self, **kwargs):
        self._pointsize = kwargs.get('pointsize', 1)
        super(ScatterPlot, self).__init__(**kwargs)

    def create_drawings(self):
        from kivy.graphics import Line, RenderContext

        self._grc = RenderContext(
                use_parent_modelview=True,
                use_parent_projection=True)
        with self._grc:
            self._gcolor = Color(*self.color)
            self._gline = Point(pointsize=self._pointsize)

        return [self._grc]

    def draw(self, *args):
        super(ScatterPlot, self).draw(*args)
        # flatten the list
        points = []
        for x, y in self.iterate_points():
            points += [x, y]
        self._gline.points = points
