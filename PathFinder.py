from collections import deque

class PathFinder():


    def __init__():
        pass
        
    
    def BFS(self, source, objectives, childs, max_cost=10):
        tree = Node(source, None, 0)
        visited = set()
        cost = 0
        founds = []
        
        q = deque()
        q.append(tree)
        visited.add(source)

        while (len(q)>0 and cost <= max_cost):
            cost+=1
            v = q.popleft()
            if v.loc in objectives:
                founds.append(v)

            children = childs(v.loc)
            for child in children:
                if child not in visited:
                    visited.append(child)
                    w = Node(child, v, cost)
                    q.append(w)
        
        paths = []
        for f in founds:
            path = []
            i = f
            while i.cost != 0:
                path.insert(0,i.loc)
                i=i.father
            paths.appends((f.cost, path, f.loc))

        return paths




class Node():
    def __init__(self, loc, father, cost):
        self.loc = loc
        self.father = father
        self.cost = cost
