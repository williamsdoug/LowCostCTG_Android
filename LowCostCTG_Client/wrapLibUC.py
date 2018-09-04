# -*- coding: utf-8 -*-

from wrapClientCommon import client_common

#
# client code
#

def findUC(*args, **vargs):
    print 'called findUC'
    return client_common('findUC', args, vargs)

