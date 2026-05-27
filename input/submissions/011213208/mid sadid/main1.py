import heapq


def a_star(graph,heuris,start,goal):

    pq = [(heuris[start], start)]
    
    g = {start: 0}
    h = heuristic(start, goal, coords)
    f = g + h
    
    heapq.heappush(pq, (f, g, start, [start]))
    
    while pq:
        f, g, current, path = heapq.heappop(pq)
        

        if current == goal:
            print("Solution path:", " - ".join(path))
            print("Solution cost:", g)
            return
        

        for neighbor, cost in adjlist[current]:
            new_g = g + cost
            new_h = heuristic(neighbor, goal, coords)
            new_f = new_g + new_h
            
            heapq.heappush(pq, (new_f, new_g, neighbor, path + [neighbor]))


