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


def prerequisite_map(edges):
    """Turn (prereq, topic) pairs into {topic: [prerequisites]}."""
    mapping = {}
    for prereq, topic in edges:
        mapping.setdefault(topic, []).append(prereq)
    return mapping


def all_prerequisites(topic, prereqs):
    """DFS: every direct and indirect prerequisite of topic (topic excluded).

    Uses an explicit stack, so deep chains can't hit the recursion limit.
    O(V + E).
    """
    visited = {topic}
    order = []
    stack = list(reversed(prereqs.get(topic, [])))
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        stack.extend(reversed(prereqs.get(node, [])))
    return order


def unmet_prerequisites(topic, prereqs, mastered):
    """BFS: prerequisites of topic that are not mastered yet, nearest first.

    Returns (name, distance) pairs, where distance 1 is a direct prerequisite.
    The search does not continue past a mastered topic, since that topic's own
    prerequisites are assumed to be covered. O(V + E).
    """
    visited = {topic}
    queue = deque((p, 1) for p in prereqs.get(topic, []))
    result = []
    while queue:
        node, dist = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        if node in mastered:
            continue
        result.append((node, dist))
        for p in prereqs.get(node, []):
            queue.append((p, dist + 1))
    return result
