# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from paramsDecel import FEATURE_EXTRACT_PARAMS


# The following imports only needed for dummy_XXX functions
from libDecel import extractAllDecels as _extractAllDecels
from libDecel import summarizeDecels as _summarizeDecels
import cPickle as pickle


#
# Non RPC Debug Versions
#

def extractAllDecels(*args, **vargs):
    debug = True
    if debug:
        print 'extractAllDecels'

    # allExtractorParams contains functions, so won't properly  serialize
    if 'allExtractorParams' in vargs:
        assert vargs['allExtractorParams'] == FEATURE_EXTRACT_PARAMS
        del vargs['allExtractorParams']

    if debug:
        print 'args:'
        for i,v in enumerate(args):
            print 'arg: {}'.format(i)
            pickle.dumps(v)

        print 'vargs'
        for k, v in vargs.items():
            print 'arg: {}'.format(k)
            pickle.dumps(v)
        print

    message = pickle.dumps(['extractAllDecels', args, vargs])
    _, args1, vargs1 = pickle.loads(message)
    vargs['allExtractorParams'] = FEATURE_EXTRACT_PARAMS
    return _extractAllDecels(*args, **vargs)


def summarizeDecels(*args, **vargs):
    debug = True
    if debug:
        print 'summarizeDecels'
        print 'args:'
        for i,v in enumerate(args):
            print 'arg: {}'.format(i)
            pickle.dumps(v)

        print 'vargs'
        for k, v in vargs.items():
            print 'arg: {}'.format(k)
            pickle.dumps(v)
        print
    message = pickle.dumps(['summarizeDecels', args, vargs])
    _, args1, vargs1 = pickle.loads(message)
    return _summarizeDecels(*args, **vargs)




