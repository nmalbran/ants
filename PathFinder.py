from collections import deque

class PathFinder():


    def __init__(self):
        pass
        
    
    def BFS(self, source, objectives, childs, first=True, max_cost=10):
        tree = Node(source, None, 0)
        visited = set()
        cost = 0
        founds = []
        goals = objectives
        
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
                    w = Node(child, v, v.cost+1)
                    q.append(w)
                    if cost < v.cost+1:
                        cost = v.cost+1
        
        paths = []
        for f in founds:
            path = {}
            i = f
            while i.cost != 0:
                path[i.father.loc] = i.loc
                i = i.father
            paths.append((f.cost, path, f.loc))

        paths.sort()
        return paths




class Node():
    def __init__(self, loc, father, cost):
        self.loc = loc
        self.father = father
        self.cost = cost
