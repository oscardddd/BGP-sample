from simulator.node import Node
import json


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)

        # {frozenset(link) : [latency, sequence]}
        self.graph = {}
        self.neighbors = set()

    # Return a string
    def __str__(self):
        return f"Node {self.id} has neighbors: {self.neighbors} and routing table: {self.graph}"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        link = frozenset([self.id, neighbor])
        timestamp = self.get_time()

        if latency == -1:
            if link in self.graph:
                self.graph[link] = [latency, timestamp]
                self.neighbors.discard(neighbor)
    
        else:
            self.graph[link] = [latency, timestamp]
            self.neighbors.add(neighbor)

        
        msg = json.dumps({
            "content": "update",
            "link_state": {str(link): data for link, data in self.graph.items()},
        })

        for i in self.neighbors:
            self.send_to_neighbor(i, msg)

        
    # Fill in this function
    def process_incoming_routing_message(self, m):
        msg = json.loads(m)
        content = msg["content"]
        unparsed = msg["link_state"]

        link_state = {}
        for link, data in unparsed.items():
            key = frozenset(map(int, link.strip("frozenset({})").split(", ")))
            link_state[key] = data


        if content == "update":
            updated = False

            for link in link_state:
                cost = link_state[link][0]
                sequence = link_state[link][1]
                if cost != -1:

                    if link not in self.graph or self.graph[link][1] < sequence:
                        self.graph[link] = [cost, sequence]
                        updated = True

                        if self.id in link:
                            self.neighbors.add(next(iter(link - {self.id})))
                    
                elif cost == -1 and link in self.graph and self.graph[link][1] < sequence:
                    self.graph[link] = [cost, sequence]
                    updated = True

                    if self.id in link:
                        self.neighbors.discard(next(iter(link - {self.id})))



        if updated:
            
            msg = json.dumps({
                "content": "update",
                "link_state": {str(link): data for link, data in self.graph.items()}
            })
            for i in self.neighbors:
                self.send_to_neighbor(i, msg)

            
    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        
        # get all nodes
        nodes = set() 
        for link in self.graph:
            for node in link:
                nodes.add(node)

        # set all nodes to infinity
        dist = {node: float("inf") for node in nodes}
        dist[self.id] = 0
        prev = {}
        for node in nodes:
            prev[node] = None
        unvisited = nodes.copy()

        while unvisited:

            curr_dist = float("inf")
            curr_node = None
            for i in unvisited:
                if dist[i] < curr_dist:
                    curr_dist = dist[i]
                    curr_node = i

            # unreachable condition
            if curr_dist == float("inf"):
                break
            
            unvisited.remove(curr_node)

            curr_neighbors = set()
            for link in self.graph:
                if curr_node in link:
                    for node in link:
                        if node != curr_node:
                            curr_neighbors.add(node)
            
            for neighbor in curr_neighbors:
                temp = self.graph[frozenset([curr_node, neighbor])][0]
                if temp != -1:
                    alt = dist[curr_node] + temp

                    if alt < dist[neighbor]:
                        dist[neighbor] = alt
                        prev[neighbor] = curr_node

        #tracing back
        curr = destination
        traceback = []
        
        while prev[curr] is not None:
            traceback.insert(0, curr)
            curr = prev[curr]
            
        if not traceback:
            return -1
        
        return traceback[0]