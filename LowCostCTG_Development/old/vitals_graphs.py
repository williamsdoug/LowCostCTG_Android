
from kivy_garden_graph import Graph, MeshLinePlot, LinePlot
from kivy_garden_graph import SmoothLinePlot
from plot_extensions import ScatterPlot

from kivy.utils import get_color_from_hex as rgb
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label

#from kivy.input.motionevent import MotionEvent

from kivy.lang import Builder

import copy
from pprint import pprint


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

kv_string = """
#:kivy 1.0

<VitalsGraphNavigation>:
    orientation: 'horizontal'

    Button:
        text: 'Default'
        on_press: root.button_pressed('default')

    Button:
        text: 'Back'
        on_press: root.button_pressed('back')

    Button:
        text: 'Forward'
        on_press: root.button_pressed('forwards')

    Button:
        text: 'Zoom'
        on_press: root.button_pressed('zoom')

    Button:
        text: 'Pan'
        on_press: root.button_pressed('pan')
"""
Builder.load_string(kv_string)



class VitalsBaseGraph(Graph):

    def __init__(self, max_duration=None, max_datapoints=2000, graphspec={}):

        # pass along generic graph parameters to parent class
        # after merging with default graph format
        merged_graphspec = copy.deepcopy(GRAPH_THEME)
        for k, v in graphspec.items():
            merged_graphspec[k] = v
        super(VitalsBaseGraph, self).__init__(xmin=0, **merged_graphspec)
        self.max_duration = max_duration
        self.max_datapoints = max_datapoints
        self.tStart = 0


    def update_timescale(self, t):
        """Update x-axis space and adjust tick scale accordingly.  """

        if self.max_duration is None:
            tStart = 0
        else:
            tStart = max(0, t-self.max_duration)
        self.xmax = t

        deltaT = t - tStart
        if deltaT <= 50:
            self.x_ticks_minor = 5
            self.x_ticks_major =  5
            granularity = 5
        elif deltaT <= 200:
            self.x_ticks_minor = 2
            self.x_ticks_major =  10
            granularity = 10
        else:
            self.x_ticks_minor = 2
            self.x_ticks_major =  20
            granularity = 20

        self.tStart =  int(tStart/granularity)*granularity
        self.xmin = int(self.tStart)

    def filterDatapointsRange(self, data):
        return [(x, y) for x, y in data
                if x >= self.xmin and x <= self.xmax]

    def filterResolution(self, data):
        """Limits data range and downsample if necessary"""
        # no filtering needed if below limit
        if len(data) <= self.max_datapoints:
            return data

        # limit timespan and check for bit
        data = self.filterDatapointsRange(data)
        if len(data) <= self.max_datapoints:
            return data

        downsample = int(round(len(data)/float(self.max_datapoints)))
        if downsample > 1:
            return [data[i] for i in range(0, len(data), downsample)]
        else:
            return data


class VitalsScatterGraph(VitalsBaseGraph):

    def __init__(self,
                 upperLimit=None, lowerLimit=None, ymin=None, ymax=None,
                 margin=5, force_ymin=None, **kwargs):

        # pass along generic graph parameters to parent class
        super(VitalsScatterGraph, self).__init__(**kwargs)

        # save customization parameters
        self.upperLimit = upperLimit
        self.lowerLimit = lowerLimit
        self.force_ymin = force_ymin
        self.margin = margin

        # Factor thresholds into Y-span calculations
        if lowerLimit is not None:
            if ymin is None:
                ymin = lowerLimit - 10
            else:
                ymin = min(ymin, lowerLimit - 10)

        if upperLimit is not None:
            if ymax is None:
                ymax = upperLimit + 10
            else:
                ymax = max(ymax, upperLimit + 10)

        self._ymin = ymin
        self._ymax = ymax

        self.allPlots = {}   # remember all component plots within graph

        # Plot for data within range
        plot = ScatterPlot(color=COLORS['green'], pointsize=2, points=[])
        self.allPlots['main'] = plot
        self.add_plot(plot)

        # Plot for data outside range
        plot = ScatterPlot(color=COLORS['red'], pointsize=2, points=[])
        self.allPlots['outlier'] = plot
        self.add_plot(plot)

        # Upper and Lower Bounds plots
        if upperLimit:
            plot = LinePlot(color=COLORS['red'], pointsize=5, points=[])
            self.allPlots['upperLimit'] = plot
            self.add_plot(plot)

        if lowerLimit:
            plot = LinePlot(color=COLORS['red'], pointsize=5, points=[])
            self.allPlots['lowerLimit'] = plot
            self.add_plot(plot)


    def updatePlot(self, data, t):
        """Update datapoints on scatter plot"""
        self.update_timescale(t)
        if len(data) == 0:
            return
        # Avoid any numpy format conversion problems by explicitly converting to float
        data = [(float(x), float(y)) for x, y in data]

        # Compute Y-axis Span
        all_y = [y for x, y in data]
        ymax_local= max(all_y)+self.margin

        if self._ymax:
            ymax_local = max(ymax_local, self._ymax)

        if self.force_ymin is not None:
            ymin_local = self.force_ymin
        else:
            ymin_local = min(all_y)-self.margin
            if self._ymin:
                ymin_local = min(ymin_local, self._ymin)

        self.ymax = ymax_local
        self.ymin = ymin_local

        # Classify datapoints for plotting based on upper and lower bounds
        outliers = []
        filtered_data = data

        if self.upperLimit:
            self.allPlots['upperLimit'].points = [(0, self.upperLimit), (t, self.upperLimit)]
            outliers += [(x, y) for x, y in filtered_data
                         if y > self.upperLimit]
            filtered_data = [(x, y) for x, y in filtered_data
                             if y <= self.upperLimit]

        if self.lowerLimit:
            self.allPlots['lowerLimit'].points = [(0, self.lowerLimit), (t, self.lowerLimit)]

            outliers += [(x, y) for x, y in filtered_data
                         if y < self.lowerLimit]
            filtered_data = [(x, y) for x, y in filtered_data
                             if y >= self.lowerLimit]

        self.allPlots['main'].points = filtered_data
        self.allPlots['outlier'].points = outliers
        return


class VitalsSpanGraph(VitalsBaseGraph):
    # map format:
    #
    # map = {
    #         name : {'legend': 'weak', 'color': 'red', 'row': 1 },
    #         ... }
    # where:
    #     - name is name used in dataset
    #     - legend is name used in legend
    #     - color is color of span marker
    #     - row is the y elevation when displaying data
    #
    # data series format:
    #
    # data = [
    #         {name: name, 'start': val, 'end': val }
    #         ...]
    #
    def __init__(self, map=None, line_width=2, **kwargs):

        # pass along generic graph parameters to parent class
        super(VitalsSpanGraph, self).__init__(**kwargs)

        if map is None:
            raise Exception('Missing Map')

        self.map = map

        # set y limits
        self.ymax = 1 + max([x['row'] for x in map.values()])
        self.ymin = 0
        self.line_width = line_width

        self.allPlots = []   # remember all component plots within graph


    def updatePlot(self, data, t):
        """Update datapoints on scatter plot"""
        self.update_timescale(t)
        for plot in self.allPlots:
            self.remove_plot(plot)
        self.allPlots = []

        if len(data) == 0:
            return

        for entry in data:
            #         {name: name, 'start': val, 'end': val }
            name = entry['name']
            assert name in self.map
            desc = self.map[name]
            row = desc['row']
            plot = LinePlot(color=COLORS[desc['color']], line_width=self.line_width,
                            points = [[entry['start'], row], [entry['end'], row]])
            self.allPlots.append(plot)
            self.add_plot(plot)

        return




class VitalsMappedPointsGraph(VitalsBaseGraph):
    # map format:
    #
    # map = {
    #         name : {'legend': 'weak', 'color': 'red', 'row': 1 },
    #         ... }
    # where:
    #     - name is name used in dataset
    #     - legend is name used in legend
    #     - color is color of span marker
    #     - row is the y elevation when displaying data
    #
    # data series format:
    #
    # data = [
    #         (time, category)
    #         ...]
    #
    def __init__(self, map=None, line_width=2, **kwargs):

        # pass along generic graph parameters to parent class
        super(VitalsMappedPointsGraph, self).__init__(**kwargs)

        if map is None:
            raise Exception('Missing Map')

        self.map = map

        # set y limits
        self.ymax = 1 + max([x['row'] for x in map.values()])
        self.ymin = 0
        self.line_width = line_width

        self.allPlots = {}   # remember all component plots within graph
        for name, desc in map.items():
            plot = ScatterPlot(color=COLORS[desc['color']], pointsize=2, points=[])
            self.allPlots[name] = plot
            self.add_plot(plot)


    def updatePlot(self, data, t):
        """Update datapoints on scatter plot"""
        self.update_timescale(t)
        if len(data) == 0:
            return
        # update plots for each mapped category
        for name, desc in self.map.items():
            row = desc['row']
            points = [(t, row) for t, category in data
                      if category == name]
            self.allPlots[name].points = points


class VitalsGraphNavigation(BoxLayout):

    def __init__(self, callback=None, **kwargs):
        super(VitalsGraphNavigation, self).__init__(**kwargs)
        self.callback = callback

    def button_pressed(self, val):
        if self.callback is not None:
            self.callback(val)
        else:
            print 'button_pressed -- no callback for:', val



class VitalsPanZoomGraph(VitalsBaseGraph):
    def __init__(self, color='red', default_duration=30, min_duration=10,
                 line_width=1.25, ymin=None, ymax=None, **kwargs):

        # pass along generic graph parameters to parent class
        super(VitalsPanZoomGraph, self).__init__(max_duration=default_duration, **kwargs)

        self.plot = LinePlot(color=COLORS[color], line_width=line_width, points=[])
        self.add_plot(self.plot)
        self.data = []
        self.tCurrent = 0
        self.at_end = True
        self.default_duration = default_duration
        self.available_duration = 0
        self.min_duration = min_duration

        self._ymin = ymin
        self._ymax = ymax
        if ymax:
            self.ymax = ymax
        if ymin:
            self.ymin = ymin

    # def on_touch_down(self, touch):
    #     print 'on_touch_down:'
    #     #pprint(touch)
    #     pprint(touch.profile)
    #     pprint(touch)

    # def on_touch_move(self, touch):
    #     print 'on_touch_move:'
    #     #pprint(touch)
    #     pprint(touch.profile)
    #     #pprint(touch.a)
    #     pprint(touch)

    # def on_touch_up(self, touch):
    #     print 'on_touch_up:'
    #     #pprint(touch)
    #     pprint(touch.profile)
    #     #pprint(touch.a)
    #     pprint(touch)


    def updatePlot(self, data, tCurrent):
        self.data = data
        self.available_duration = tCurrent
        self.tCurrent = tCurrent

        if len(self.data) > 0:
            if self.at_end:
                self.refreshPlot(tCurrent)
        else:
            self.plot.points = []

    def refreshPlot(self, t):
        """Update datapoints on scatter plot"""
        self.tEnd = t
        self.update_timescale(t)
        points= self.filterResolution(self.data)
        if len(points) == 0:
            self.plot.points = []
            return

        all_y = [y for x, y in points]
        ymax = max(all_y)
        ymin = min(all_y)

        ymax = int((ymax+10)/10)*10
        ymin = int(ymin/10)*10
        ymin = min(self._ymin, ymin) if self._ymin else ymin
        ymax = max(self._ymax, ymax) if self._ymax else ymax

        self.ymax = ymax
        self.ymin = ymin

        if ymax - ymin > 100:
            self.y_ticks_major = 20
            self.y_ticks_minor = 4
        else:
            self.y_ticks_major = 10
            self.y_ticks_minor = 2

        self.plot.points = points


    def do_nav(self, val):
        # print 'do_nav called for:', val
        assert val in ['default','back','forwards','zoom','pan']

        if val == 'default':
            self.max_duration = self.default_duration
            self.at_end = True
            self.tEnd = self.tCurrent
        elif val == 'zoom':
            self.max_duration = max(self.min_duration, self.max_duration/1.3)
        elif val == 'pan':
            self.max_duration = min(self.available_duration, self.max_duration*1.3)
            if self.max_duration == self.available_duration:
                self.at_end = True
                self.tEnd = self.tCurrent
        elif val == 'back':
            self.at_end = False
            shift = self.max_duration*.7
            self.tStart = max(0, self.tStart - shift)
            self.tEnd = self.tStart + self.max_duration
        elif val == 'forwards':
            shift = self.max_duration*.7
            self.tEnd = min(self.tCurrent, self.tEnd + shift)
            if self.tEnd == self.tCurrent:
                self.at_end = True
            self.tStart = self.tEnd - self.max_duration

        self.refreshPlot(self.tEnd)


    def filterDatapointsRange(self, data):
        return [(x, y) for x, y in data
                if x >= self.tStart and x <= self.tEnd]

    def filterResolution(self, data):
        """Limits data range and downsample if necessary"""
        # no filtering needed if below limit
        if len(data) <= self.max_datapoints:
            return data

        # limit timespan and check for bit
        data = self.filterDatapointsRange(data)
        if len(data) <= self.max_datapoints:
            return data

        downsample = int(round(len(data)/float(self.max_datapoints)))
        if downsample > 1:
            return [data[i] for i in range(0, len(data), downsample)]
        else:
            return data



def addGraphLegend(map, size_hint = (None, 0.15)):
    """Creates Legend widget for VitalsSpanGraph"""

    root = StackLayout(orientation='lr-tb')
    #root = BoxLayout()
    root.add_widget(Label(text='Legend:', size_hint=size_hint))

    known = []
    for name, desc in map.items():
        #  name : {'legend': 'weak', 'color': 'red', 'row': 1 },
        legend =  desc['legend']
        color = desc['color']
        if legend in known:  # avoid duplicates for many-to-one mapping
            continue
        known.append(legend)
        root.add_widget(Label(text=legend, color=COLORS[color], size_hint=size_hint))

    return root