import heapq
def a_star_graph(graph, heuristic, start, goal):
    open_list = []
    heapq.heappush(open_list, (0, start))

    g_cost = {node: float('inf') for node in graph}
    g_cost[start] = 0

    parent = {start: None}
    visited_order = []   

    while open_list:
        current_cost, current = heapq.heappop(open_list)
        if current in visited_order:
            continue

        visited_order.append(current)

        if current == goal:
            path = []
            while current:
                path.append(current)
                current = parent[current]
            path.reverse()
            return path, g_cost[goal], visited_order

        for neighbor, cost in graph[current]:
            new_cost = g_cost[current] + cost

            if new_cost < g_cost[neighbor]:
                g_cost[neighbor] = new_cost
                priority = new_cost + heuristic.get(neighbor, 0)
                heapq.heappush(open_list, (priority, neighbor))
                parent[neighbor] = current

    return None, float('inf'), visited_order

def main():
    graph = {}
    heuristic = {}

    n = int(input("Enter number of nodes: "))
    for _ in range(n):
        node = input("Enter node name: ")
        graph[node] = []

    e = int(input("Enter number of edges: "))
    for _ in range(e):
        u, v, cost = input("Enter edge (u v cost): ").split()
        cost = int(cost)
        graph[u].append((v, cost))
        graph[v].append((u, cost))

    print("Enter heuristic values:")
    for node in graph:
        heuristic[node] = int(input(f"h({node}): "))

    start = input("Enter start node: ")
    goal = input("Enter goal node: ")

    path, cost, visited = a_star_graph(graph, heuristic, start, goal)

    

    print("\nVisited Nodes (Expansion Order):")
    print(visited)

    if path:
        print("\nShortest Path:", path)
        print("Minimum Cost:", cost)
    else:
        print("\nNo path found!")


if __name__ == "__main__":
    main()