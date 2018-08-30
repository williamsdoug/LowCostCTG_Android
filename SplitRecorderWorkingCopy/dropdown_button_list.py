
#
# Dropdown Button List Widget
#

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

class DropdownButtonList(Button):
    def __init__(self, bar_width=20, bar_color=(1,1,1,1), bar_inactive_color=(1,1,1,1),
                                  scroll_type=['content', 'bars'], **kwargs):
        super(DropdownButtonList, self).__init__(**kwargs)
        self.drop_list = None
        self.drop_list = DropDown(bar_width=bar_width, bar_color=bar_color,
                                  bar_inactive_color=bar_inactive_color, scroll_type=scroll_type)
        self.update_dropdown([])
        self.callback = None

        self.bind(on_release=self.drop_list.open)
        #self.drop_list.bind(on_select=lambda instance, x: setattr(self, 'text', x))
        self.drop_list.bind(on_select=self.do_select)


    def do_select(self, instance, x):
        setattr(self, 'text', x)
        if self.callback is not None:
            self.callback(x)


    def update_dropdown(self, entries):
        self.drop_list.clear_widgets()
        for i in entries:
            btn = Button(text=i, size_hint_y=None, height=50, valign="middle", padding_x= 5, halign='left')
            #btn.text_size = btn.size
            btn.bind(on_release=lambda btn: self.drop_list.select(btn.text))

            self.drop_list.add_widget(btn)

    def register_callback(self, callback):
        self.callback = callback