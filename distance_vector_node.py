import copy

from simulator.node import Node
import json

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.neighbors = {}
        self.dv = {}
        self.rtable = {}
        self.seq_num = 0
        self.msg_pool = {}
        self.neighbors_dv = {}

        #initialize
        self.dv[id] = [0,[]]
        self.rtable[id] = id


    # Return a string
    def __str__(self):
        return f"Node: {self.id}, Neighbors: {self.neighbors}, Routing Table: {self.rtable}, Distance Vector: {self.dv}"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        if latency == -1:
            if neighbor in self.neighbors:
                del self.neighbors[neighbor]
            if neighbor in self.neighbors_dv:
                del self.neighbors_dv[neighbor]

        else:
            self.neighbors[neighbor] = latency

        # compute the self dv
        old = copy.deepcopy(self.dv)
        self.dv = {}
        self.dv[self.id] = [0, []]

        for neighbor, cost in self.neighbors.items():
            self.dv[neighbor] = [cost, [neighbor]]
            self.rtable[neighbor] = neighbor

        # we update every destination in neighbor dvs
        for neighbor, dv in self.neighbors_dv.items():
            for destination, [cost, path] in dv.items():

                if neighbor in self.neighbors.keys():
                    newcost = self.neighbors[neighbor] + cost
                    if newcost < self.dv.get(destination, [float('inf'), []])[0]:
                        self.dv[destination] = [newcost, [neighbor] + path]
                        self.rtable[destination] = neighbor

        if old != self.dv:
            msg = json.dumps({
                "id": self.id,
                "dv": self.dv,
                "seq_num": self.seq_num,
            })

            # print(self.__str__())
            for neighbor in self.neighbors:
                self.send_to_neighbor(neighbor, msg)

            self.seq_num += 1


    def process_incoming_routing_message(self, m):
        m = json.loads(m)
        updated = False
        newdv = m["dv"]
        n = m["id"]
        # update the neighbor dv dictionary
        if n not in self.neighbors_dv:
            self.neighbors_dv[n] = {}

        # make sure it is the latest message  from the specific neighbor
        if m["seq_num"] > self.msg_pool.get(m["id"], -1):
            self.msg_pool[m["id"]] = m["seq_num"]

            # copy the old neighbor dv of n
            oldndv = copy.deepcopy(self.neighbors_dv[n])
            self.neighbors_dv[n] = {}

            for destination, [cost1, path1] in newdv.items():
                destination = int(destination)

                if self.id not in path1:
                    self.neighbors_dv[n][destination] = [cost1, path1]

            if oldndv != self.neighbors_dv[n]:
                updated = True

            if updated:
                # compute the dv
                old = copy.deepcopy(self.dv)
                self.dv = {}
                self.dv[self.id] = [0,[]]

                for neighbor, cost in self.neighbors.items():
                    self.dv[neighbor] = [cost, [neighbor]]
                    self.rtable[neighbor] = neighbor

                # we update every destination in neighbor dvs
                for neighbor, dv in self.neighbors_dv.items():
                    # print(neighbor, dv)
                    for destination, [cost, path] in dv.items():
                        if neighbor in self.neighbors.keys():
                            newcost = self.neighbors[neighbor] + cost
                            if newcost < self.dv.get(destination, [float('inf'), []])[0]:
                                self.dv[destination] = [newcost, [neighbor] + path]
                                self.rtable[destination] = neighbor

                # print("within updated: ", self.__str__())

                if old != self.dv:
                    msg = json.dumps({
                        "id": self.id,
                        "dv": self.dv,
                        "seq_num": self.seq_num,
                    })

                    # print(self.__str__())
                    for neighbor in self.neighbors:
                        self.send_to_neighbor(neighbor, msg)
                    self.seq_num += 1



    def get_next_hop(self, destination):
        # print("\n the end: \n", self.__str__())
        if destination in self.rtable.keys():
            return self.rtable[destination]
        else:
            return -1



