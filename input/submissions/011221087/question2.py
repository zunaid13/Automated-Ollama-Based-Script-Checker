import heapq
graph = {
 'A': {'B': (2, True), 'C': (5, True)},
 'B': {'A': (2, True), 'D': (3, False), 'E': (4, True)},
 'C': {'A': (5, True), 'F': (3, True)},
 'D': {'B': (3, False), 'E': (1, True)},
 'E': {'B': (4, True), 'D': (1, True), 'G': (2, True)},
 'F': {'C': (3, True), 'G': (4, True)},
 'G': {'E': (2, True), 'F': (4, True)}
}
heuristic = {
 'A': 7,
 'B': 6,
 'C': 5,
 'D': 4,
 'E': 3,
 'F': 2,
 'G': 0
}
start = 'A'
goal = 'G'


 while pq:
     f, cost, node, path = heapq.heappop(pq)

     if node == goal:
        return path,cost

    if node in visited:

        continue

    visited.add(node)



print("Optimal path:", " -> ".join(path))
print("Total cost:", cost)