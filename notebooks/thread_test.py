import time
import threading
import sys



def background(*args, **kwards):
    while True:
        print '.',
        sys.stdout.flush()
        time.sleep(1)

def test():
    print 'starting backgrount thread'
    thread = threading.Thread(target=background)
    thread.daemon = True
    thread.start()
    time.sleep(15)
    print 'Stopping',
    sys.stdout.flush()

if __name__ == '__main__':
    test()