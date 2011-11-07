

class ExploreMap():

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.map = [[0]*cols for row in range(rows)]
        self.spaces = set([(r,c) for r in rows for c in cols])
        
    def update(self, visibles):
        non_visibles = self.spaces - visibles
        
        for r,c in non_visibles:
            if self.map[r][c] < 0:
                self.map[r][c]=0
            else:
                self.map[r][c]+=1
        
        for r,c in visibles:
            if self.map[r][c] > 0:
                self.map[r][c]=0
            else:
                self.map[r][c]-=1
    
    
    def high_direction(self, loc):
        r,c = loc
        possibles = [((r+1)%self.rows, (c-1)%self.cols), ((r+1)%self.rows, (c+1)%self.cols),
                     ((r-1)%self.rows, (c+1)%self.cols), ((r-1)%self.rows, (c-1)%self.cols)]
        high = None
        high_val = -1000
        for row,col in possibles:
            if self.map[row][col] >= high_val:
                high = (row,col)
                high_val = self.map[row][col]
        return high
    
    def print_map(self, center):
        c_row, c_col = center
        for row in range(c_row-10, c_row+10):
            print self.map[row%self.rows][(c_col-10)%self.cols:(c_col+10)%self.cols]
            
            # ver cuadros al rededor de vision con mayor puntaje, usar bfs para llegar
