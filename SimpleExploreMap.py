from random import shuffle

UNSEEN = 0
WATER = -2000

class SimpleExploreMap():

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        self.map = [[UNSEEN]*cols for row in range(rows)]

        self.land = set([(r,c) for r in range(rows) for c in range(cols)])
        self.water = set()
        self.ants = set()


    def update(self, ants):

        self.ants = set(ants.my_ants())

        new_water = ants.water()
        self.water.update(new_water)
        self.land.difference_update(new_water)
        non_visibles = self.land - self.ants

        for r,c in non_visibles:
            if self.map[r][c] < 0:
                self.map[r][c]=0
            else:
                self.map[r][c]+=1

        for r,c in self.ants:
            if self.map[r][c] > 0:
                self.map[r][c]=0
            else:
                self.map[r][c]-=1

        for r,c in new_water:
            self.map[r][c] = WATER

    def neighborhood(self, loc):
        row, col = loc
        neighborhood = set([((row)%self.rows, (col+1)%self.cols),
                            ((row)%self.rows, (col-1)%self.cols),
                            ((row-1)%self.rows, (col)%self.cols),
                            ((row+1)%self.rows, (col)%self.cols) ])
        return neighborhood - self.water

    def get_lower_locs(self,loc):
        neighborhood = list(self.neighborhood(loc))
        shuffle(neighborhood)
        val_loc = [ (self.map[row][col], (row, col)) for row, col in neighborhood]
        val_loc.sort()
        return val_loc

    def get_higher_locs(self,loc):
        lowers = self.get_lower_locs(loc)
        lowers.reverse()
        return lowers
