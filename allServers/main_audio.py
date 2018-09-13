# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from AudioServer import AudioServer, getAudioServer


# start server
if __name__ == '__main__':
    #svr = AudioServer(ZMQ_AUDIO_SERVER_ADDRESS_SPEC, ZMQ_AUDIO_PUB_ADDRESS_SPEC)
    svr = getAudioServer()
    if True:
        svr.serve()
    else:
        svr.start()
        svr.wait()
