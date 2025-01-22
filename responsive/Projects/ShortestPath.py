import heapq

# node class taht has a name, weight, parent and a list of neighbors

class Node:
    def __init__(self, name):
        self.name=name
        self.weight=float('inf')
        self.parent=None
        self.neighbors=[]



def Dijkstra(G, s):
    dist, prev, Q = Initialize_source(G, s)
    
    while Q:
        try:
            min_vertex = heapq.heappop(Q)
        except IndexError:
            break

        # get the second value of the tuple. i did not do this and it took me 3hrs to fix 
        node = G.getNode(min_vertex[1])

        if node is None:
            print(f"Node {min_vertex} does not exist in the graph3.")
            continue
        # iterate over the neighbors of the node and calculate the distance between them and the current
        for neighbor, weight in node.neighbors:
            shorter = dist[min_vertex[1]] + weight

            # id the distance is shorter update the distance and the predecessor
            if shorter < dist[neighbor.name]:
                dist[neighbor.name] = shorter
                prev[neighbor.name] = min_vertex[1]

                # update the new distance and neighbor for future 
                heapq.heappush(Q, (dist[neighbor.name], neighbor.name))
    
    # this returns the dictionaries with the shortests distances and the predecessors
    return dist, prev


def Initialize_source(G,s):
    # make a dictionary for both distance and predecessors of the nodes
    dist = {name: float('inf') for name in G.nodes}
    prev = {name: None for name in G.nodes}

    # distance of the node to itself is 0 of course
    dist[s] = 0


    Q = [(0, s)]

    # heapify it to maintain the property 
    heapq.heapify(Q)
    return dist, prev, Q


def shortestPath(graph, source, target):
    dist, prev= Dijkstra(graph, source)
    # print("Distances:", dist)
    # print("Predecessors:", prev)
    
    print(f'This is our target: {target}')
    print(f' is our target an inf distance away?: {dist.get(target, float("inf")) == float("inf")}')
    if not target :
     return None, float('inf')

    path = []
    visited = set()
    current = target
    while current is not None:
        if current in visited:
            print("Cycle detected!")
            return None, float('inf')
        visited.add(current)
        path.insert(0, current)
        current = prev.get(current)
    
    return path, dist.get(target, float('inf'))



class GraphOfDict:

    def __init__(self):
        self.nodes={}

    def add_ver(self, name):
        if name not in self.nodes:
            self.nodes[name]=Node(name)

    def getNode(self, name):
        if name in self.nodes:
            return self.nodes[name]
        else:
            return None
    
    def add_edge(self, v1, v2):
        if len(v1)!= len(v2):
            return

        dif=sum(1 for c1, c2 in zip(v1, v2) if c1 != c2)
        
        if dif==1:
            self.add_ver(v1)
            self.add_ver(v2)
            self.nodes[v1].neighbors.append((self.nodes[v2], dif))
            self.nodes[v2].neighbors.append((self.nodes[v1],dif))
        # print(f"Added edge between {v1} and {v2}")


def main():
    # Create an instance of the GraphOfDict class
    graph = GraphOfDict()

    print("Generating graph, please wait one moment...")
    # Read words from the dictionary file and construct the graph
    with open('Dict.txt', "r") as file:
        for line in file:
            word = line.strip()
            graph.add_ver(word)

    for word in graph.nodes:
        for i in range(len(word)):
            for c in range(ord('a'), ord('z')+1):
                new_word = word[:i] + chr(c) + word[i+1:]
                if new_word in graph.nodes and new_word != word:
                    graph.add_edge(word, new_word)

    print('Graph generated')
    # User interaction loop
    while True:
        start = input("Enter the starting word: ")
        end = input("Enter the ending word: ")

        start_node = graph.getNode(start)
        end_node = graph.getNode(end)

        # Check if both words are of equal length and exist in the graph
        if len(start) != len(end) or not start_node or not end_node:
            print("Note: Both words must be of equal size and exist in the graph.")
            continue

        # Find and display the shortest path between the two words
        path, length = shortestPath(graph, start, end)
        if path:
            print("Shortest path:", ' -> '.join(path))
            print("Length:", length)
        else:
            print("Path doesn't exist.")

main()

