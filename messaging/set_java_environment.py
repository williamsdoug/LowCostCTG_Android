import os
# export JAVA_HOME=`/usr/libexec/java_home`
# export CLASSPATH="/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar"

def set_java_home_and_classpath():
    os.environ['JAVA_HOME'] = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'

    # os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromq-0.4.3.jar"

    os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/messaging/jeromq-0.4.3.jar" \
                              + ":" + "/Users/doug/Documents/GitHub/LowCostCTG_Android/messaging/jeromqfixer.jar"
