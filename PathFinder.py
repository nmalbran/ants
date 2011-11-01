from collections import deque
import heapq

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
        return paths # (cost, path, location)

    def BFSexplore(self, source, childs, max_cost=7, num=1):
        tree = Node(source, None, 0)
        visited = set()
        cost = 0
        founds = []
        
        q = deque()
        q.append(tree)
        visited.add(source)

        while(len(q)>0):
            v = q.popleft()
            if v.cost == max_cost:
                founds.append(v)
                if len(founds)>=num:
                    break
            elif v.cost > max_cost:
                visited.add(v.loc)
            else:
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
            paths.append((f.cost, path, f.loc))

        if num > 1:
            paths.sort()
        return paths

#    def AStar(self, source, dest, childs):
#        #openlist = PriorityQueueSet([(0, source)])
#        openlist = [(0, source)]
#        closelist = []
#        
#        while 1:
#            openlist.sort()
#            n = openlist[0]
#            if n[1] == dest:
#                break
#            closelist.append(n[1])
#            children = childs(n[1])
#            for child in children:
#                cost = g(n[1]) + 1
#                if child in openlist and cost < g(child):
#                    openlist.remove(child)
#                if child in closelist and cost < g(child):
#                    closelist.remove(child)
#                if child not in openlist and child not in closelist:
                    
        
        

class Node():
    def __init__(self, loc, father, cost):
        self.loc = loc
        self.father = father
        self.cost = cost
        

class PriorityQueueSet(object):
    """ Combined priority queue and set data structure. Acts like
        a priority queue, except that its items are guaranteed to
        be unique.

        Provides O(1) membership test, O(log N) insertion and 
        O(log N) removal of the smallest item.

        Important: the items of this data structure must be both
        comparable and hashable (i.e. must implement __cmp__ and
        __hash__). This is true of Python's built-in objects, but
        you should implement those methods if you want to use
        the data structure for custom objects.
    """
    def __init__(self, items=[]):
        """ Create a new PriorityQueueSet.

            items:
                An initial item list - it can be unsorted and 
                non-unique. The data structure will be created in
                O(N).
        """
        self.set = dict((item, True) for item in items)
        self.heap = self.set.keys()
        heapq.heapify(self.heap)

    def has_item(self, item):
        """ Check if *item* exists in the queue
        """
        return item in self.set

    def pop_smallest(self):
        """ Remove and return the smallest item from the queue
        """
        smallest = heapq.heappop(self.heap)
        del self.set[smallest]
        return smallest

    def add(self, item):
        """ Add *item* to the queue. The item will be added only
            if it doesn't already exist in the queue.
        """
        if not (item in self.set):
            self.set[item] = True
            heapq.heappush(self.heap, item)
    
    def empty(self):
        return len(self.set) == 0
