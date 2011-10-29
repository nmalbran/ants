from collections import deque

class PathFinder():


    def __init__(self):
        pass
        
    
    def BFS(self, source, goals, childs, first=True, max_cost=10, backward=False):
        """ Find paths from source to goals using BFS,
            with a max lenght path of max_cost,
            if first is set, return the shortest path
            if backward is set, return the paths from goals to source"""
        tree = Node(source, None, 0)
        visited = set()
        cost = 0
        founds = []
        
        q = deque()
        q.append(tree)
        visited.add(source)

        while(len(q)>0 and cost <= max_cost):
            v = q.popleft()
            if v.loc in goals:
                founds.append(v)
                if first:
                    break

            children = childs(v.loc)
            for child in children:
                if child not in visited:
                    visited.add(child)
                    nc = v.cost+1
                    q.append(Node(child, v, nc))
                    if cost < nc:
                        cost = nc
        
        paths = []
        for f in founds:
            path = {}
            i = f
            while i.cost != 0:
                path[i.father.loc] = i.loc
                i = i.father
            if backward:
                path = dict(zip(path.values(),path.keys()))
                paths.append((f.cost, path, f.loc))
            else:
                paths.append((f.cost, path, f.loc))

        if not first:
            paths.sort()
        return paths


class Node():
    def __init__(self, loc, father, cost):
        self.loc = loc
        self.father = father
        self.cost = cost
