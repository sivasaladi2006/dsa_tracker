from collections import deque


def topological_sort(nodes, edges):
    """Order nodes so every prerequisite comes before the topics that need it.

    edges is a list of (prereq, topic) pairs. Raises ValueError on a cycle.
    """
    adjacency = {n: [] for n in nodes}
    indegree = {n: 0 for n in nodes}
    for prereq, topic in edges:
        adjacency[prereq].append(topic)
        indegree[topic] += 1

    queue = deque(n for n in nodes if indegree[n] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in adjacency[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(nodes):
        raise ValueError("Cycle detected in topic prerequisites")
    return order
