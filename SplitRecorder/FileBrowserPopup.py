import kivy

from kivy.uix.popup import Popup

from garden_filebrowser import FileBrowser

from pprint import pprint
import sys

import os
from os.path import sep, expanduser, isdir, dirname


prefix = os.path.join(os.path.join('/', *os.getcwd().split('/')[:-1]), 'recordings')


class FileBrowserPopup:
    def __init__(self, filters=['*.csv'], path=None, callback=None, title='Select file for import'):
        self.callback = callback

        if sys.platform == 'win':
            user_base = dirname(expanduser('~'))
            user_path = dirname(expanduser('~')) + sep + 'Downloads'
        else:
            user_base = expanduser('~')
            user_path = expanduser('~') + sep + 'Downloads'

        browser = FileBrowser(filters=filters, multiselect=False,
                              rootpath=user_base, path=user_path, select_string='Select')
        browser.bind(on_success=self.process_selected, on_canceled=self.process_cancel)
        self.browser_popup = Popup(title=title, content=browser)  #auto_dismiss=False
        self.browser_popup.open()


    def process_selected(self, instance):
        selection = instance.selection
        self.browser_popup.dismiss()
        if len(selection) == 1:
            print 'FileBrowserPopup selected', selection[0]
            if self.callback:
                self.callback(selection[0])
            else:
                raise Exception('Missing FileBrowserPopup callback')


    def process_cancel(self, instance):
        print 'canceled'
        self.browser_popup.dismiss()

