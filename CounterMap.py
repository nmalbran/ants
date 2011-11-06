from collections import deque

class CounterMap():

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.map = [[100]*cols for row in range(rows)]
        
    def update(self, ants, childs, water, foods):
        for r in range(self.rows):
            for c in range(self.cols):
                self.map[r][c]+=1
        
        for r,c in water:
            self.map[r][c]=-99
        
        for ant in ants:
            self.update_ant(ant, childs, ants)
        
        for food in foods:
            self.update_food(food, childs, ants)

    
    def update_ant(self, ant, childs, ants):
        visited = set()
        cost = 3
        q = deque()
        q.append(ant)
        visited.add(ant)
        
        while(cost >=0):
            v = q.popleft()
            r,c = v
            self.map[r][c]-=cost
            children = childs(v)
            for child in children:
                if child not in visited:
                    visited.add(child)
                    q.append(child)
            cost-=1

    def update_food(self, food, childs, ants):
        visited = set()
        cost = 20
        q = deque()
        q.append(food)
        visited.add(food)
        
        while(cost >=0):
            v = q.popleft()
            if v not in ants:
                r,c = v
                self.map[r][c]+=cost
                children = childs(v)
                for child in children:
                    if child not in visited:
                        visited.add(child)
                        q.append(child)
            cost-=1

    def high_direction(self, loc):
        r,c = loc
        possibles = [((r+1)%self.rows, (c-1)%self.cols), ((r+1)%self.rows, (c+1)%self.cols),
                     ((r-1)%self.rows, (c+1)%self.cols), ((r-1)%self.rows, (c-1)%self.cols)]
        high = None
        high_val = -100
        for row,col in possibles:
            if self.map[row][col] > high_val:
                high = (row,col)
                high_val = self.map[row][col]
        return high
        
    def print_map(self, center):
        c_row, c_col = center
        for row in range(c_row-10, c_row+10):
            print self.map[row%self.rows][(c_col-10)%self.cols:(c_col+10)%self.cols]
                
            
            
