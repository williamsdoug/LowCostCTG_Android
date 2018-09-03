# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#



import kivy
from kivy.uix.popup import Popup
from kivy.lang import Builder

Builder.load_string("""

<ConfirmRecordingPopup>:
    msg: msgID

    auto_dismiss: False
    title: 'Confirmation'
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: msgID
            size_hint: 1, 0.9

        GridLayout:
            size_hint: 1, 0.1
            cols: 2
            rows: 1
            Button:
                text: 'Yes'
                on_release: root.process_ok()
            Button:
                text: 'No'
                on_release: root.dismiss()

""")


class ConfirmRecordingPopup(Popup):
    def __init__(self, callback, msg='', *args, **kwargs):
        super(ConfirmRecordingPopup, self).__init__(*args, **kwargs)
        self.callback = callback
        self.msg.text = msg

    def process_ok(self):
        self.dismiss()
        self.callback()
