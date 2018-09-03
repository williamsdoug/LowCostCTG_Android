# -*- coding: utf-8 -*-

#from paramsDecel import FEATURE_EXTRACT_PARAMS
from wrapClientCommon import client_common


#
# client code
#


def extractAllDecels(*args, **vargs):
    print 'called extractAllDecels'

    # allExtractorParams contains functions, so won't properly  serialize
    # if 'allExtractorParams' in vargs:
    #     assert vargs['allExtractorParams'] == FEATURE_EXTRACT_PARAMS
    #     del vargs['allExtractorParams']

    return client_common('extractAllDecels', args, vargs)


def summarizeDecels(*args, **vargs):
    print 'called summarizeDecels'
    return client_common('summarizeDecels', args, vargs)

