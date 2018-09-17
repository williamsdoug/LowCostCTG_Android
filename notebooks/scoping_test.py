
print 'scoping_test importing scoping'
import scoping
print 'scoping_test importing scoping2'
import scoping2

def test():
    print 'scoping_test', scoping.FOO
    print 'scoping_test', scoping.getFOO()
    print
    scoping2.test()
    print
    print 'setting FOO'
    scoping.setFOO('New Value')
    print
    print 'scoping_test', scoping.FOO
    print 'scoping_test', scoping.getFOO()
    print
    scoping2.test()
    print
    print  scoping == scoping2.scoping

if __name__ == '__main__':
    test()