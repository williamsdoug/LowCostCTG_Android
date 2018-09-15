package com.ddw_gd.jeromqfixer;

import org.zeromq.ZMQ;
import org.zeromq.ZMQ.Socket;

public class JeromqFixer {
    public static void subscribe(Socket socket) {
        socket.subscribe(ZMQ.SUBSCRIPTION_ALL);
    }
}
