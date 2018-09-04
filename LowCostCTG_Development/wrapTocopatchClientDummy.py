# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from wrapTocopatchServer import TocoListener as _TocoListener
#
# Non RPC Debug Versions
#

class TocoListener:
    def __init__(self, *args, **kwargs):

        if 'connection_callback' in kwargs:
            self.connection_callback = kwargs['connection_callback']
            kwargs['connection_callback'] = self.proxy_connection_callback
        else:
            self.connection_callback = None

        if 'update_callback' in kwargs:
            self.update_callback = kwargs['update_callback']
            kwargs['update_callback'] = self.proxy_update_callback
        else:
            self.update_callback = None

        if 'completion_callback' in kwargs:
            self.completion_callback = kwargs['completion_callback']
            kwargs['completion_callback'] = self.proxy_completion_callback
        else:
            self.completion_callback = None

        self.proxy = _TocoListener(*args, **kwargs)
        print 'server TocoListener returning from init'


    def proxy_connection_callback(self, *args, **kwargs):
        self.connection_callback(*args, **kwargs)


    def proxy_update_callback(self, *args, **kwargs):
        self.update_callback(*args, **kwargs)


    def proxy_completion_callback(self, *args, **kwargs):
        self.completion_callback(*args, **kwargs)


    def update_skew(self, *args, **kwargs):
        return self.proxy.update_skew(*args, **kwargs)


    def go(self, *args, **kwargs):
        return self.proxy.go(*args, **kwargs)


    def stop(self, *args, **kwargs):
        return self.proxy.stop(*args, **kwargs)


    def wait(self, *args, **kwargs):
        return self.proxy.wait(*args, **kwargs)


    def get_start_time(self, *args, **kwargs):
        return self.proxy.get_start_time(*args, **kwargs)


    def get_sample_rate(self, *args, **kwargs):
        return self.proxy.get_sample_rate(*args, **kwargs)


    def getData(self, *args, **kwargs):
        return self.proxy.getData(*args, **kwargs)


    def teardown(self, *args, **kwargs):
        return self.proxy.teardown(*args, **kwargs)

