# This example is using Python 2.7
import os.path
import socket

import table
import thread
import util
import net_util

_CONFIG_UPDATE_INTERVAL_SEC = 5
_MESSAGE_SEND_PERIOD_SEC = 15

_MAX_UPDATE_MSG_SIZE = 1024
_BASE_ID = 8000


def _ToPort(router_id):
    return _BASE_ID + router_id


def _ToRouterId(port):
    return port - _BASE_ID


class Router:
    def __init__(self, config_filename):
        # ForwardingTable has 3 columns (DestinationId,NextHop,Cost). It's
        # threadsafe.
        self._forwarding_table = table.ForwardingTable()
        # Config file has router_id, neighbors, and link cost to reach
        # them.
        self._config_filename = config_filename
        self._router_id = None
        self.config = {}
        # Socket used to send/recv update messages (using UDP).
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        # Start a periodic closure to update config.
        self._config_updater = util.PeriodicClosure(
            self.load_config, _CONFIG_UPDATE_INTERVAL_SEC)
        self._config_updater.start()
        # TODO: init and start other threads.
        while not self._router_id:
            continue
        self._message_sender = util.PeriodicClosure(self.send_updates, _MESSAGE_SEND_PERIOD_SEC)
        self._message_sender.start()
        while True:
            data, addr = self._socket.recvfrom(_MAX_UPDATE_MSG_SIZE)
            thread.start_new(self.handler, (data, addr,))

    def handler(self, data, addr):
        message = net_util.read_message(data)
        next_hop_id = _ToRouterId(addr[1])
        print 'Received update Message from', next_hop_id, ': ', message
        if self.compute_forwarding_table(message, next_hop_id):
            print 'Compute forwarding table:', self._forwarding_table.snapshot()
            self.send_updates()

    def stop(self):
        if self._config_updater:
            self._config_updater.stop()
        # TODO: clean up other threads.
        self._config_updater.stop()
        self._message_sender.stop()

    def load_config(self):
        assert os.path.isfile(self._config_filename)
        costs = {}
        with open(self._config_filename, 'r') as f:
            router_id = int(f.readline().strip())
            # Only set router_id when first initialize.
            if not self._router_id:
                self._socket.bind(('localhost', _ToPort(router_id)))
                self._router_id = router_id
            # TODO: read and update neighbor link cost info.
            for line in f:
                neighbor_id, cost = [int(x.strip()) for x in line.split(',')]
                costs[neighbor_id] = cost

        # Update forwarding table when config file changes
        if not self.config or self.config != costs:
            self.config = costs
            self.update_forwarding_table(self.config)
            print 'Update forwarding table:', self._forwarding_table.snapshot()

            # Each time updating table, send messages to neighbors
            self.send_updates()

    # update self's forwarding table
    # happens every 5s to update from config file
    def update_forwarding_table(self, costs):
        # Initialize forwarding table, next hops are set to self
        entries = self._forwarding_table.snapshot()
        for id in costs.keys():
            if not id in entries.keys() or entries[id][1] != costs[id]:
                entries[id] = (self._router_id, costs[id])
        self._forwarding_table.reset(entries)

    # compute self's forwarding table
    # happens when received message from neighbor
    def compute_forwarding_table(self, message, next_hop_id):
        table_updated = False
        entries = self._forwarding_table.snapshot()
        cost_to_next_hop = entries[next_hop_id][1]
        for id in message.keys():
            if id is self._router_id:
                continue

            if id not in entries.keys() or message[id] + cost_to_next_hop < entries[id][1]:
                table_updated = True
                entries[id] = (next_hop_id, message[id] + cost_to_next_hop)
            elif next_hop_id == entries[id][0]:
                tmp = entries[id][1]
                if id not in self.config.keys() or message[id] + cost_to_next_hop < self.config[id]:
                    entries[id] = (next_hop_id, message[id] + cost_to_next_hop)
                else:
                    entries[id] = (self._router_id, self.config[id])
                if tmp != entries[id][1]:
                    table_updated = True
        self._forwarding_table.reset(entries)
        return table_updated
    def send_updates(self):
        for neighbor_id in self.config.keys():
            self.send_updates_to_neighbors(neighbor_id)

    # send updated table info to neighbors
    # happens once table info has been changed
    def send_updates_to_neighbors(self, neighbor_id):
        message = self.extract_message_from_table()
        data = net_util.construct_message(message)
        self._socket.sendto(data, ('localhost', _ToPort(neighbor_id)))
        print 'Sending message to ', neighbor_id, ': ', message

    # extract message to be sent to neighbors
    def extract_message_from_table(self):
        message = {}
        entries = self._forwarding_table.snapshot()
        for id in entries.keys():
            message[id] = entries[id][1]
        return message
