# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


from wrapClientCommon import client_common

#
# client code
#

def findUC(*args, **vargs):
    print 'called findUC'
    return client_common('findUC', args, vargs)

