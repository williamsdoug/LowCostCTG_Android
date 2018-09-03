# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

#
# Overall database and persistence management functions
#
#  Includes:
#   - Path to root directory and dub directories
#   - Catalog of Patients and identification of current patient
#   - Catalog of per-patient recordings and identification of current recording
#




import os
import sys
from os.path import sep, expanduser, isdir, dirname
import uuid
import shutil
from pprint import pprint
import pickle as pickle
import time

from AppWithParams import AppWithParams


DB_NAME = 'ctg_db'
REMOTE_DB_NAME = 'GitHub' + sep + 'Malawi_ctg_db'
DEMO_DB_NAME = 'GitHub' + sep + 'demo_ctg_db'

def get_db_path(user_uuid=None, rec_uuid=None, useRemote=False):
    """Gets paths for ctg database.  By default returns directory for database.
       Providing user_uuid results in user-specific directory.   Providing both returns
       path for recording.  Function creates directories if not already present"""

    user_path = AppWithParams.getParam('recording_path')
    print 'user_path', user_path
    if not user_path:
        print 'Exception during get_db_path'
        if sys.platform == 'win':
            user_path = dirname(expanduser('~'))
        else:
            user_path = expanduser('~')

        user_path = user_path + sep + 'Documents' + sep + DB_NAME

        # AppWithParams.setParam('recording_path', user_path)


    if not os.path.exists(user_path) and not AppWithParams.getParam('readonly'):
        os.makedirs(user_path)


    if user_uuid is not None:
        user_path += sep + user_uuid
        if not os.path.exists(user_path) and not AppWithParams.getParam('readonly'):
            os.makedirs(user_path)
        if rec_uuid is not None:
            user_path += sep + rec_uuid

    return user_path

    pass


class PersistenceManager(object):
    """Managed state associated with a persistent list of entries visible via dropdown menu"""

    def __init__(self, dropdown_list, on_update=None):
        self.dropdown_list = dropdown_list
        self.on_update = on_update
        self.clear()
        self.dropdown_list.register_callback(self.select_callback)


    def clear(self):
        self.data = {}
        self.data_map = {}
        self.current_uuid = None
        self.dropdown_list.update_dropdown([])
        self.dropdown_list.text = ''


    def select_callback(self, x):
        print 'select_callback:', x
        print 'current selection:', self.dropdown_list.text
        if self.dropdown_list.text not in self.data_map:
            print 'Error:  Unable to locate entry in ', self.dropdown_list.text
            self.current_uuid = None
            self.dropdown_list.text = ''
        else:
            self.current_uuid = self.data_map[self.dropdown_list.text]
        if self.on_update:
            self.on_update(self.current_uuid)


    def uuid_to_desc(self, this_uuid):
        """Creates drop-down descriptor from  data using uuid as key"""
        raise Exception('uuid_to_desc not implemented')


    def get_metadata_file_path(self):
        """Abstract method to get name of medadata file"""
        raise Exception('get_path not implemented')


    def load_data(self):
        """load data from disk"""
        try:
            self.data_file = self.get_metadata_file_path()
            print 'data file:', self.data_file

            with open(self.data_file, 'r') as fd:
                self.data = pickle.load(fd)

            # print 'Loading Data:'
            # pprint(self.data)
            self.update_list()

        except Exception:
            print 'Initializing Data'
            self.data = {}
            self.update_data()


    def update_data(self):
        """Updated on-disk data and reflects changes in drop-down menu"""
        if not AppWithParams.getParam('readonly'):
            with open(self.data_file, 'w') as fd:
                pickle.dump(self.data, fd)
        self.update_list()


    def update_list(self):
        """Update drop-down menu after changes in data, refresh selected entry if needed"""
        entries = [(self.uuid_to_desc(this_uuid), this_uuid) for this_uuid in self.data.keys()]
        pprint(entries)
        self.data_map = dict(entries)
        self.dropdown_list.update_dropdown(sorted([x[0] for x in entries],
                                                  key=lambda x:x.lower()))

        if self.current_uuid is None:
            self.dropdown_list.text = ''
        elif self.current_uuid not in self.data:
            self.current_uuid = None
            self.dropdown_list.text = ''
        else:
            self.dropdown_list.text = self.uuid_to_desc(self.current_uuid)
        if self.on_update:
            self.on_update(self.current_uuid)


    def get_selected_uuid(self):
        if self.current_uuid is not None:
            return self.current_uuid
        else:
            return None


    def get_selection(self):
        if self.current_uuid is not None:
            return self.data[self.current_uuid]
        else:
            return None


    def update_selection(self, entry):
        if entry is not None:
            self.current_uuid = entry['uuid']
            self.data[entry['uuid']] = entry
            self.update_data()


    def delete_selection(self):
        del self.data[self.current_uuid]
        self.current_uuid = None
        self.update_data()
        if self.on_update:
            self.on_update(self.current_uuid)


class PatientPersistenceManager(PersistenceManager):
    """Managed state associated with a persistent list of patient entries visible bia dropdown menu"""

    def uuid_to_desc(self, this_uuid):
        """Creates drop-down descriptor from  data using uuid as key"""
        e = self.data[this_uuid]

        return '{}, {} -- age: {}'.format(e['last_name'], e['first_name'], e['age'])


    def get_metadata_file_path(self):
        """Get name of patients metadata file"""
        return os.path.join(get_db_path(), 'patient_data.p')



class RecordingsPersistenceManager(PersistenceManager):
    """Managed state associated with a persistent list of recording entries visible via dropdown menu"""

    def __init__(self, *args, **kwargs):
        super(RecordingsPersistenceManager, self).__init__(*args, **kwargs)
        self.parent_uuid = None


    def clear(self):
        super(RecordingsPersistenceManager, self).clear()
        self.parent_uuid = None


    def uuid_to_desc(self, this_uuid):
        """Creates drop-down descriptor from recording data using uuid as key"""
        e = self.data[this_uuid]

        desc = '{} -- {:0.1f} min'.format(time.ctime(e['date']), e['duration'])

        if 'name' in e:
            desc = e['name'] + '  ' + desc

        if 'comment' in e:
            desc =  desc + '  ' + e['comment']

        return desc


    def get_metadata_folder_path(self):
        """Get name of recordings metadata file"""
        return get_db_path(user_uuid=self.parent_uuid)


    def get_metadata_file_path(self):
        """Get name of recordings metadata file"""
        return os.path.join(self.get_metadata_folder_path(), 'recordings_data.p')


    def change_folder(self, parent_uuid):
        if parent_uuid == self.parent_uuid:  # skip if no change
            return
        self.clear()
        self.parent_uuid = parent_uuid
        if parent_uuid is not None:
            # make sure recordings directory exists, create if needed
            current_data_dir = self.get_metadata_folder_path()
            if current_data_dir and not os.path.exists(current_data_dir)  and not AppWithParams.getParam('readonly'):
                os.makedirs(current_data_dir)
            self.load_data()
        else:
            self.current_data_dir = None


    def remove_folder(self, parent_uuid):
        print 'calling remove_folder', parent_uuid
        if parent_uuid is None:
            return
        self.parent_uuid = parent_uuid
        current_data_dir = self.get_metadata_folder_path()
        if current_data_dir and os.path.exists(current_data_dir)  and not AppWithParams.getParam('readonly'):
            print 'deleting directory', current_data_dir
            shutil.rmtree(current_data_dir)
        self.clear()
