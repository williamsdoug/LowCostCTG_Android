# ZeroMQ/JeroMQ Messaging Libraries

Includes both ZeroMQ and Java-native JeroMQ libraries

### Examples

- Request/Reply
  - Python: zmq_client.py, zmq_server.py
  - Java:   jzmq_client.py, jzmq_server.py

- Pub/Sub
  - Python: zmq_pub.py, zmq_sub.py
  - Java:   jzmq_pub.py, jzmq_sub.py
  
 - Support functions
  - common.py - generic implementations of client, server, publisher and subscriber functions
  - set_java_environment.py
  
### Platform Independent Messaging Library


#### ZeroMQ Class (2 variants below)
- Common API for both ZeroMQ and JeroMQ
- Exports socket
  - zmq content remains hidden
- Operations:
  - Initialize socket (4 variants)
    - Req: `socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.REQ)`
      - Sample address spec: `ADDRESS_SPEC = "tcp://localhost:5555"`
    - Rep: `socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.REP)`
      - Sample address spec: `ADDRESS_SPEC = "tcp://*:5555"`
    - Pub: `socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.PUB)`
      - Sample address spec: `ADDRESS_SPEC = "tcp://*:8888"`
    - Sub: `socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.SUB)`
      - Sample address spec: `ADDRESS_SPEC = "tcp://localhost:8888"`
  - Send message:
    - `socket.send_pyobj(message)`
  - Receive message:
    - `message = socket.recv_pyobj()`
    - `message = socket.recv_pyobj(blocking=False)`
      - Raises exception `ZMQ_Again` if no data
  - Close socket and context
    - `socket.close()`

#### Variants:
- ZeroMQ:
  - `from jeromq_compat import ZeroMQ, `
- JeroMQ:
  - `from jeromq_compat import ZeroMQ`
  - Note:  Requires jar files (below) to be included in `CLASSPATH`
- Common Exception:
  - `from ZMQ_Again_Exception import ZMQ_Again`
  

#### Issues addressed in library

- Python string/uncode issues preclude direct use of xmq socket.recv_pyobj() and xmq socket.send_pyobj()
  - Causes pickle deserialization to fail when unicode received on zeromq side from jeromq source
  - Solution:  zeromq_compat.py / jeromq_compat.py to implement alternative recv_pyobj() and send_pyobj() with necessary unicode clean-up.
 
- Unable to perform socket.subscribe([]) fromPython using pyjnius
  - Zero-byte array not properly passed to jeromq via pyjnius
  - Work-around:  Use JeromqFixer (jeromqfixer.py) to perform subscription using java code
  - Coude located in `./java` directory in this repo
  - Build envirinment: `/Users/doug/IdeaProjects/JavaTest`

### Configuring `JAVA_HOME` and `CLASSPATH` for Java

- Define Java related environment variables either externally or internally:
  - Externally
  ```buildoutcfg
  $ export JAVA_HOME=`/usr/libexec/java_home`
  $ export CLASSPATH="/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromq-0.4.3.jar"

  ```
  - Internally (e.g.: `set_java_environment.py`)
  ```buildoutcfg
  import os
  os.environ['JAVA_HOME'] = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
  os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/messaging/jeromq-0.4.3.jar"
  ```
- Note:   
    - `JAVA_HOME` defines path to java sdk on your system 
    - `CLASSPATH` must include location of jeromq jar file
    - `JAVA_HOME` and `CLASSPATH` must be declared prior to importing jnius

- Subscribe operation requires additional library (jar) in `CLASSPATH`
    ```buildoutcfg
    os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/messaging/jeromq-0.4.3.jar" \
                              + ":" + "/Users/doug/Documents/GitHub/LowCostCTG_Android/messaging/jeromqfixer.jar"
    ```