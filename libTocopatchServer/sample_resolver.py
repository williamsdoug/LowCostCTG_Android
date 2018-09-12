
from os.path import dirname, join

def resolve_sample(name):
    print 'resolve_sample', join('sample_data', name)
    return join('sample_data', name)

def resolve_sample_android(name):
    import sample_data
    print 'resolve_sample_android', join(dirname(sample_data.__file__), name)
    return join(dirname(sample_data.__file__), name)