
# graph = {
#     0: [1, 2],
#     1: [3, 4],
#     2: [5],
#     3: [],
#     4: [],
#     5: []
# }

# O(V + E) time and O(V) space

def dfs(graph, node, visited):
    if node in visited:
        return

    print(node,end=" ")
    visited.add(node)

    for neighbor in graph[node]:
        dfs(graph, neighbor, visited)


graph = {
    0: [1, 2],
    1: [3],
    2: [4, 5],
    3: [0, 6],   # cycle back to 0
    4: [2],      # self-cycle via 2 → 4 → 2
    5: [6, 7],
    6: [1],      # cycle back to 1
    7: []
}

visited=set()
dfs(graph,0,visited)

# 0 1 3 4 2 5



