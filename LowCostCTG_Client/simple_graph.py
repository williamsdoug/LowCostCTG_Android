# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from kivy_garden_graph import *
#from garden_graph_new import *
from kivy.clock import Clock
from kivy.utils import get_color_from_hex as rgb

# from kivy.graphics import Line, RenderContext, Color, Ellipse, Point
#from kivy.graphics import RenderContext, Color, Point
from kivy.graphics import RenderContext, Color, Point

import numpy as np
#from plot_extensions import ScatterPlot
import copy
import math

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

GRAPH_THEME = {
    'label_options': {
        #'color': rgb('444444'),  # color of tick labels and titles
        'bold': False},
    'font_size':'10sp',
    #'background_color': rgb('f8f8f2'),  # back ground color of canvas
    'tick_color': rgb('808080'),  # ticks and grid
    #'tick_color': rgb('f8f8f2'),  # ticks and grid
    'border_color': rgb('808080'), # border drawn around each graph
    'padding':5,
}



class ScatterPlot(Plot):
    '''ScatterPlot draws using a standard Point object.
    '''

    '''Args:
    line_width (float) - the width of the graph line
    '''
    def __init__(self, pointsize=5, **kwargs):
        self._pointsize = pointsize
        super(ScatterPlot, self).__init__(**kwargs)

    def create_drawings(self):
        # from kivy.graphics import Line, RenderContext, Color, Point
        #from kivy.graphics import RenderContext, Color, Point

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


class SimpleLineGraph(Graph):
    def __init__(self, theme=None,
                 dynamic_xmax=True, dynamic_xmin=True,
                 dynamic_ymax=True, dynamic_ymin=True,
                 include_plot=True, plot_type='LinePlot', color=[1, 0, 0, 1], points=[],
                 line_width=None, # LinePlot only
                 pointsize=1, # scatter only
                 **kwargs):

        # pass along generic graph parameters to parent class
        # after merging with default graph format
        if theme is None:
            merged_graphspec = copy.deepcopy(GRAPH_THEME)
        else:
            merged_graphspec = copy.deepcopy(theme)
        for k, v in kwargs.items():
            merged_graphspec[k] = v
        super(SimpleLineGraph, self).__init__(**merged_graphspec)


        self.dynamic_xmax = dynamic_xmax
        self.dynamic_xmin = dynamic_xmin
        self.dynamic_ymax = dynamic_ymax
        self.dynamic_ymin = dynamic_ymin

        if not self.dynamic_xmax:
            self.saved_xmax = self.xmax
        if not self.dynamic_xmin:
            self.saved_xmin = self.xmin
        if not self.dynamic_ymax:
            self.saved_ymax = self.ymax
        if not self.dynamic_ymin:
            self.saved_ymin = self.ymin

        self.vertical_annotations = []
        self.horizontal_annotations = []
        self.segment_annotations = []

        self.lines = {}
        self.data = {}
        self.last_xmin = None
        self.last_xmax = None
        if include_plot:
            self.add_another_plot('default', plot_type=plot_type, color=color, points=points,
                                  line_width=line_width, pointsize=pointsize)
            if points:
                self.update_xlim()


    def add_another_plot(self, plot_name, plot_type='LinePlot', color=[1, 0, 0, 1], points=[],
                         mode=None,         # used by MeshLinePlot, defaults to 'line_strip'
                         pointsize=1,
                         line_width=1):     # line_width for LinePlot only



        if plot_type not in ['MeshLinePlot', 'LinePlot', 'SmoothLinePlot', 'ScatterPlot']:
            raise Exception('Unknown plot type')
        elif plot_type == 'ScatterPlot':
            plot = ScatterPlot(color=color, pointsize=pointsize)
        elif plot_type == 'MeshLinePlot':
            if mode is None:
                mode = 'line_strip'
            elif mode not in ['points', 'line_strip', 'line_loop', 'lines', 'triangle_strip', 'triangle_fan']:
                raise Exception('Unknown VBO Mode for MeshLinePlot -- See :class:`~kivy.graphics.Mesh` for more details')
            plot = MeshLinePlot(color=color, mode=mode)
        elif plot_type == 'LinePlot':
            if line_width is None:
                plot = LinePlot(color=color)
            else:
                plot = LinePlot(color=color, line_width=line_width)
        elif plot_type == 'SmoothLinePlot':
            plot = SmoothLinePlot(color=color)


        self.data[plot_name] = points  # save full set of dataa
        plot.points = points

        self.lines[plot_name] = plot
        self.add_plot(plot)


    def clearAllPoints(self, xmax=None):
        # for plot_name in self.lines.keys():
        #     self.data[plot_name] = []
        #     self.lines[plot_name].points = []

        all_points = dict([ [plot_name, []]    for plot_name in self.lines.keys()])
        # print all_points
        self.add_points(all_points, xmax)


    def add_points(self, all_points, xmax=None, isUpdate=False, update_xmax=True):
        if isinstance(all_points, dict):
            for plot_name, points in all_points.items():
                if plot_name in self.lines:
                    if isUpdate:
                        self.data[plot_name] = self.data[plot_name] + points
                        self.lines[plot_name].points = self.lines[plot_name].points + points
                    else:
                        self.data[plot_name] = points
                        self.lines[plot_name].points = points
        else:
            if isUpdate:
                self.data['default'] = self.data['default'] + all_points
                self.lines['default'].points = self.lines['default'].points + all_points
            else:
                self.data['default'] = all_points
                self.lines['default'].points = all_points

        if update_xmax:
            if xmax is None:
                self.update_xlim()
            elif xmax == False:
                pass
            else:
                self.xmax = xmax
                self.update_horizontal_annotations()
        self.update_ylim()

    def update_x_scale(self, tStart, tEnd):
        #print 'called update_x_scale', tStart, tEnd
        if tStart == self.last_xmin and tEnd == self.last_xmax:
            #print 'skipping update_x_scale'
            return

        self.xmin = tStart
        self.xmax = tEnd
        for plot_name, plot in self.lines.items():
            if self.data[plot_name] >= 2000:
                points = [x for x in self.data[plot_name] if x[0] >= tStart and x[0] <= tEnd]
                if len(points) >= 2000:
                    # reduce number of points
                    stride = int(math.ceil(len(points) / (2000.0 - 1.0))) # slightly overestimate stride
                    points = points[::stride]
                plot.points = points
        self.update_horizontal_annotations()
        self.last_xmin = tStart
        self.last_xmax = tEnd


    def add_vertical_annotations(self, xpos, color=[0.5, 0, 0, 1], line_width=1):
        plot = LinePlot(color=color, line_width=line_width)
        plot.points=[(xpos, self.ymin), (xpos, self.ymax)]
        self.vertical_annotations.append(plot)
        self.add_plot(plot)


    def update_vertical_annotations(self):
        for plot in self.vertical_annotations:
            xpos = plot.points[0][0]
            plot.points = [(xpos, self.ymin), (xpos, self.ymax)]

    def remove_vertical_annotations(self):
        for plot in self.vertical_annotations:
            self.remove_plot(plot)
        self.vertical_annotations = []


    def add_horizontal_annotations(self, ypos, color=[0.5, 0, 0, 1], line_width=1):
        plot = LinePlot(color=color, line_width=line_width)
        plot.points=[(self.xmin, ypos), (self.xmax, ypos)]
        self.horizontal_annotations.append(plot)
        self.add_plot(plot)


    def update_horizontal_annotations(self):
        for plot in self.horizontal_annotations:
            ypos = plot.points[0][1]
            plot.points = [(self.xmin, ypos), (self.xmax, ypos)]

    def remove_horizontal_annotations(self):
        for plot in self.horizontal_annotations:
            self.remove_plot(plot)
        self.horizontal_annotations = []


    def add_segment_annotation(self, ypos, xStart, xEnd, color=[0.5, 0, 0, 1], line_width=1, is_horizontal=True):
        plot = LinePlot(color=color, line_width=line_width)
        if is_horizontal:
            plot.points = [(xStart, ypos), (xEnd, ypos)]
        else:
            plot.points = [(ypos, xStart), (ypos, xEnd)]
        self.segment_annotations.append(plot)
        self.add_plot(plot)


    def remove_segment_annotations(self):
        for ann in self.segment_annotations:
            self.remove_widget(ann)
            del ann
        self.segment_annotations = []


    def update_ylim(self):
        if not self.dynamic_ymax:
            self.ymax = self.saved_ymax
        if not self.dynamic_ymin:
            self.ymin = self.saved_ymin


    def update_y_scale(self, ymin, ymax):
        self.ymax = ymax
        self.ymin = ymin
        self.dynamic_ymin = False


    def update_xlim(self):
        # if not self.dynamic_xmax:
        #     self.xmax = self.saved_xmax
        # if not self.dynamic_xmin:
        #     self.xmin = self.saved_xmin
        #print 'calling update_xlim'

        if not (self.dynamic_xmin or self.dynamic_xmax):
            #print 'skipping update_xlim'
            return

        limits = [ (points[0][0], points[-1][0]) for line in self.lines.values() for points in [line.points] if len(points) > 0]
        if limits:
            if self.dynamic_xmin:
                self.xmin = min([x[0] for x in limits])

            if self.dynamic_xmax:
                self.xmax = max([x[1] for x in limits])

            self.update_horizontal_annotations()




if __name__ == '__main__':
    import itertools
    from math import sin, cos, pi
    from random import randrange
    from kivy.utils import get_color_from_hex as rgb
    from kivy.uix.boxlayout import BoxLayout
    from kivy.app import App

    class TestApp(App):

        def build(self):
            b = BoxLayout(orientation='vertical')
            # example of a custom theme
            colors = itertools.cycle([
                rgb('7dac9f'), rgb('dc7062'), rgb('66a8d4'), rgb('e5b060')])
            graph_theme = {
                'label_options': {
                    'color': rgb('444444'),  # color of tick labels and titles
                    'bold': True},
                'background_color': rgb('f8f8f2'),  # back ground color of canvas
                'tick_color': rgb('808080'),  # ticks and grid
                'border_color': rgb('808080')}  # border drawn around each graph

            all_points = [(x / 10., sin(x / 50.)) for x in range(-500, 501)]
            graph = SimpleLineGraph(points=all_points, dynamic_xmax=False,
                color=next(colors),
                xlabel='Cheese',
                ylabel='Apples',
                x_ticks_minor=5,
                x_ticks_major=25,
                y_ticks_major=1,
                y_grid_label=True,
                x_grid_label=True,
                padding=5,
                xlog=False,
                ylog=False,
                x_grid=True,
                y_grid=True,
                xmin=-50,
                #xmax=50,
                xmax=100,
                ymin=-1,
                ymax=1,
                #theme=graph_theme)
                font_size='10sp',
                theme=None)


            graph.add_another_plot('cos',
                                   #plot_type='LinePlot',
                                   #plot_type='MeshLinePlot',
                                   plot_type='SmoothLinePlot',
                                   color=next(colors),
                                   line_width=5)
            self.all_points2 = [(x / 10., cos(x / 50.)) for x in range(-500, 501)]
            self.all_points2_idx = 0
            #graph.add_points({'cos':self.all_points2}, isUpdate=True)
            self.graph = graph


            pos = -9
            while pos < 10:
                #print pos
                if pos in [-5, 5]:
                    self.graph.add_horizontal_annotations(pos/10.0, color=COLORS['red'], line_width=1)
                else:
                    self.graph.add_horizontal_annotations(pos/10.0, color=COLORS['gray'], line_width=1)
                pos += 1

            self.graph.add_vertical_annotations(75)
            self.graph.add_vertical_annotations(-25)

            b.add_widget(graph)

            Clock.schedule_interval(self.update_points, 1/10.0)

            return b



        def update_points(self, *args):
            if False:
                if self.all_points2_idx < len(self.all_points2):
                    self.all_points2_idx += 1
                    self.graph.add_points({'cos': self.all_points2[:self.all_points2_idx]}, isUpdate=False)
            elif True:
                if self.all_points2_idx < len(self.all_points2):
                    self.graph.add_points({'cos': self.all_points2[self.all_points2_idx:self.all_points2_idx+2]}, isUpdate=True)
                    self.all_points2_idx += 2
            else:
                all_points = [(x / 10., cos(Clock.get_time() + x / 50.)) for x in range(-500, 501)]
                self.graph.add_points({'cos': all_points}, isUpdate=False)
            pass


    TestApp().run()
