import udt
from config import *
import packet_utils
import time
import thread

# Go-Back-N reliable transport protocol.
class GoBackN:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_port, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.base = 0
        self.nextseqnum = 0
        self.buffer = list()
        # lock for accessing self.buffer
        self.buffer_lock = thread.allocate_lock()
        # lock for timer status changing
        self.timer_lock = thread.allocate_lock()
        self.current_time = time.time()
        self.status = MSG_STAU_READY
        self.expectedseqnum = 0
        self.done = False

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        self.send_by_type(MSG_TYPE_DATA, msg)
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
            # print 'remote: %d, expected:%d' % (fields[1], self.expectedseqnum)
            if not packet_utils.is_expected(fields[1], self.expectedseqnum):
                print 'out-of-order data pkt received, resend last ack'
                self.network_layer.send(packet_utils.make_ack_pkt(self.nextseqnum, self.expectedseqnum))
                self.nextseqnum += 1
                return
            self.msg_handler(fields[3])
            self.expectedseqnum += 1
            self.network_layer.send(packet_utils.make_ack_pkt(self.nextseqnum, self.expectedseqnum))
            self.nextseqnum += 1

            # received FIN pkt, which means this is running as server-side
            if fields[0] == MSG_TYPE_FIN:
                self.done = True
            # debug
            # print 'sent seq: %d, ack: %d' % (self.local_seq_num, 1 - fields[1])

        elif fields[0] == MSG_TYPE_ACK:
            ack = packet_utils.extract_ack(fields[3])
            # debug
            # print 'ack: %d, local:%d' % (ack, self.local_seq_num)
            if ack is None:
                print 'corrupt ack packet received, do nothing'
                return
            if ack < self.base:
                print 'out of order ack pkt received'
                return

            print 'ack #%d received' % ack
            self.buffer_lock.acquire()

            # remove elements before current ACK#, which are confirmed received
            while self.base < ack and self.base < self.nextseqnum:
                self.buffer.pop(0)
                self.base += 1
            self.buffer_lock.release()
            if self.base == self.nextseqnum:
                self.timer_lock.acquire()
                # if timer is running, change timer status
                if self.status != MSG_STAU_TM_EXIT:
                    self.status = MSG_STAU_TM_STOP
                    # wait until timer exit
                    while self.status != MSG_STAU_TM_EXIT:
                        pass
                self.timer_lock.release()

    # Cleanup resources.
    def shutdown(self):
        # TODO: cleanup anything else you may have when implementing this
        # class.

        # wait until all pkts in buffer are delivered
        while len(self.buffer) > 0:
            pass
        # not self.done means this side is client, which is going to
        # start the shutdown process for this communication
        if not self.done:
            self.send_by_type(MSG_TYPE_FIN, "")
            current_time = time.time()
            try_times = 20
            # a simple strategy to shutdown when get ACK of FIN or tried certain times
            while self.status != MSG_STAU_READY:
                if (time.time() - current_time) * 1000 > try_times * TIMEOUT_MSEC:
                    self.status = MSG_STAU_READY

        self.network_layer.shutdown()

    # method to send a specific type of message
    def send_by_type(self, msg_type, msg):
        while self.base + WINDOWN_SIZE <= self.nextseqnum:
            pass
        # debug
        # print 'base: %d, nextseqnum: %d, msg: %s' % (self.base, self.nextseqnum, msg)
        pkt = packet_utils.make_pkt(msg_type, self.nextseqnum, msg)
        self.buffer_lock.acquire()
        self.buffer.append(packet_utils.BufferUnit(self.nextseqnum, pkt))
        self.buffer_lock.release()
        self.current_time = time.time()
        self.network_layer.send(pkt)
        self.timer_lock.acquire()
        # start timer
        if self.base == self.nextseqnum:
            thread.start_new_thread(self.timer, ())
        self.timer_lock.release()
        self.nextseqnum += 1

    # send out all the buffered pkts
    def send_all_buffer(self):
        self.buffer_lock.acquire()
        for buf in self.buffer:
            self.network_layer.send(buf.pkt)
        self.buffer_lock.release()

    def timer(self):
        if self.status == MSG_STAU_TM_RUNNING:
            print 'already running, exit'
            return
        self.status = MSG_STAU_TM_RUNNING
        while self.status == MSG_STAU_TM_RUNNING:
            if (time.time() - self.current_time) * 1000 > TIMEOUT_MSEC:
                print 'Timeout...'
                self.send_all_buffer()
                self.current_time = time.time()
        self.status = MSG_STAU_TM_EXIT
        print 'timer exiting'

