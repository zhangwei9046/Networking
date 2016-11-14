import udt
from config import *
import packet_utils
import time


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_port, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.local_seq_num = 0
        self.current_time = time.time()
        self.status = MSG_STAU_READY
        self.done = False

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.

        # while self.status != MSG_STAU_READY:
        #     pass
        self.local_seq_num = 1 - self.local_seq_num
        # debug
        # print 'local_seq: %d, msg: %s' % (self.local_seq_num, msg)
        packet = packet_utils.make_pkt(MSG_TYPE_DATA, self.local_seq_num, msg)
        self.current_time = time.time()
        self.network_layer.send(packet)
        self.status = MSG_STAU_WAITACK
        self.timing_monitor(packet)
        return True

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        msg = self.network_layer.recv()
        # TODO: impl protocol to handle arrived packet from network layer.
        # call self.msg_handler() to deliver to application layer.

        fields = packet_utils.extract_pkt(msg)
        if fields is None:
            print 'corrupt packet received, do nothing'
            return
        if fields[0] == MSG_TYPE_DATA or fields[0] == MSG_TYPE_FIN:
            # debug
            # print 'remote: %d, local:%d' % (fields[1], self.local_seq_num)
            if not packet_utils.verify_ss_order(fields[1], self.local_seq_num):
                print 'duplicated data pkt received, resend last ack'
                self.network_layer.send(packet_utils.make_ack_pkt(1-self.local_seq_num, 1 - fields[1]))
                return
            self.msg_handler(fields[3])
            self.network_layer.send(packet_utils.make_ack_pkt(self.local_seq_num, 1 - fields[1]))
            # debug
            # print 'sent seq: %d, ack: %d' % (self.local_seq_num, 1 - fields[1])
            self.local_seq_num = 1 - self.local_seq_num

            # received FIN pkt, which means this is running as server-side
            if fields[0] == MSG_TYPE_FIN:
                self.done = True

        elif fields[0] == MSG_TYPE_ACK:
            ack = packet_utils.extract_ack(fields[3])
            # debug
            # print 'ack: %d, local:%d' % (ack, self.local_seq_num)
            if ack is None:
                print 'corrupt ack packet received, do nothing'
                return
            if ack == self.local_seq_num:
                print 'out of order ack pkt received'
                return
            self.status = MSG_STAU_READY

    # Cleanup resources.
    def shutdown(self):
    # TODO: cleanup anything else you may have when implementing this
    # class.

        # not self.done means this side is client, which is going to
        # start the shutdown process for this communication
        if not self.done:
            self.local_seq_num = 1 - self.local_seq_num
            # debug
            # print 'local_seq: %d, msg: %s' % (self.local_seq_num, msg)
            packet = packet_utils.make_pkt(MSG_TYPE_FIN, self.local_seq_num, "")
            self.current_time = time.time()
            self.network_layer.send(packet)
            self.status = MSG_STAU_WAITACK
            self.timing_monitor(packet)
            current_time = time.time()
            try_times = 8
            # a simple strategy to shutdown when get ACK of FIN or tried certain times
            while self.status != MSG_STAU_READY:
                if (time.time() - current_time) * 1000 > try_times * TIMEOUT_MSEC:
                    self.status = MSG_STAU_READY

        self.network_layer.shutdown()

    def timing_monitor(self, packet):
        while self.status == MSG_STAU_WAITACK:
            if (time.time() - self.current_time) * 1000 > TIMEOUT_MSEC:
                print 'Timeout...'
                self.network_layer.send(packet)
                self.current_time = time.time()
        self.status = MSG_STAU_READY
        # debug
        # print 'timing exit'


