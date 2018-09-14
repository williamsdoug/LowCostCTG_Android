# Porting Zeromq Code To Use JeroMQ


### Interoperability Issues

- Python string/uncode issues preclude direct use of xmq socket.recv_pyobj() and xmq socket.send_pyobj()
  - Causes pickle deserialization to fail when unicode received on zeromq side from jeromq source
  - Solution:  zeromq_compat.py / jeromq_compat.py to implement alternative recv_pyobj() and send_pyobj() with necessary unicode clean-up.
 
- Unable to perform socket.subscribe([]) fromPython using pyjnius
  - Zero-byte array not properly passed to jeromq via pyjnius
  - Work-around:  Use JeromqFixer (jeromqfixer.py) to perform subscription using java code
  - Coude located in `./java` directory in this repo
  - Build envirinment: `/Users/doug/IdeaProjects/JavaTest`

### Porting compatability library

- Include import
  - `from zeromq_compat import recv_pyobj, send_pyobj`
- Replace `socket.recv_pyobj()`
  - `socket.recv_pyobj()` becomes `recv_pyobj(socket)`
  - `socket.recv_pyobj(flags=zmq.NOBLOCK)` becomes `recv_pyobj(socket, blocking=False)`
  
- Replace `socket.send_pyobj()`
  - `socket.send_pyobj(message)` becomes `send_pyobj(socket, message)`
  
  
### Porting Details

- Remove `import zmq`
- Add imports
```buildoutcfg
from jeromq_compat import recv_pyobj, send_pyobj, jmqAgain
from jnius import autoclass
ZMQ = autoclass('org/zeromq/ZMQ')
ZContext = autoclass('org.zeromq.ZContext')
```
- Replace `context = zmq.Context()` with `context = ZContext()`
- Replace `socket = context.socket(zmq.*)` with `socket = context.createSocket(ZMQ.*)`
  - Replace all `zmq.*` constants with `ZMQ.*`
  - includes `PUB`,`SUB`,`REQ`,`REP`

- Replace `socket.recv_pyobj()`
  - `socket.recv_pyobj()` becomes `recv_pyobj(socket)`
  - `socket.recv_pyobj(flags=zmq.NOBLOCK)` becomes `recv_pyobj(socket, blocking=False)`
    - `except zmq.Again:` becomes `except jmqAgain:`
- Replace `socket.send_pyobj()`
  - and Exception: `socket.send_pyobj(message)` becomes `send_pyobj(socket, message)`
  
- Replace `context.term()` with `context.destroy()`

- Replace `socket.subscribe()` with `Subscriber.subscribe(socket)`
  - Requires: `Subscriber = autoclass('com.ddw_gd.jeromqfixer.JeromqFixer')`

### Configuring Java
- Define Java related environment variables either externally or internally:
  - Externally
  ```buildoutcfg
$ export JAVA_HOME=`/usr/libexec/java_home`
$ export CLASSPATH="/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromq-0.4.3.jar"

  ```
  - Internally
  ```buildoutcfg
import os
os.environ['JAVA_HOME'] = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar"
  ```
  - Note:   
    - `JAVA_HOME` defines path to java sdk on your system 
    - `CLASSPATH` must include location of jeromq jar file
    - `JAVA_HOME` and `CLASSPATH` must be declared prior to importing jnius

- Subscribe operation requires additional library (jar) in `CLASSPATH`
```buildoutcfg
os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar" \
                          + ":" + "/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromqfixer.jar"
```