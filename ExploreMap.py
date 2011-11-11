from random import shuffle
from math import sqrt

class ExploreMap():

    def __init__(self, rows, cols, rad, view_radius2):
        self.rows = rows
        self.cols = cols
        self.map = [[100]*cols for row in range(rows)]
        self.land = set([(r,c) for r in range(rows) for c in range(cols)])
        self.water = set()

        def get_pre_radius(rad):
            offsets = []
            mx = rad
            rad2 = rad**2
            for d_row in range(-mx,mx+1):
                for d_col in range(-mx,mx+1):
                    d = d_row**2 + d_col**2
                    if d <= rad2:
                        offsets.append((
                            d_row%self.rows-self.rows,
                            d_col%self.cols-self.cols
                        ))
            return offsets

        def get_pre_ring(rada,radb):
            offsets = []
            mx = radb
            radb2 = radb**2
            rada2 = rada**2
            for d_row in range(-mx,mx+1):
                for d_col in range(-mx,mx+1):
                    d = d_row**2 + d_col**2
                    if rada2 <= d <= radb2:
                        offsets.append((
                            d_row%self.rows-self.rows,
                            d_col%self.cols-self.cols
                        ))
            return offsets

        #rad = 3
        self.clear_area = get_pre_radius(rad)
        radXrad = [(d_row%self.rows-self.rows, d_col%self.cols-self.cols)
                                for d_row in range(-(rad+1), rad+1)
                                for d_col in range(-(rad+1), rad+1)]
        self.border_area = set(radXrad) - set(self.clear_area)
        self.ring = get_pre_ring(6,8)

        self.visible_area = get_pre_radius(int(sqrt(view_radius2)+1))



    def get_radius(self, loc, area):
        a_row, a_col = loc
        return set([ ((a_row+v_row)%self.rows, (a_col+v_col)%self.cols) for v_row, v_col in area])


    def update(self, ants):
        visibles = set()
        rad = self.get_radius
        va = self.clear_area

        for loc in ants.my_ants():
            visibles.update(rad(loc, va))

        new_water = ants.water()
        self.water.update(new_water)
        self.land.difference_update(new_water)
        non_visibles = self.land - visibles


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

        for r,c in new_water:
            self.map[r][c] = -2000



    def high_direction(self, loc):
        r,c = loc
        #possibles = [((r+1)%self.rows, (c-1)%self.cols), ((r+1)%self.rows, (c+1)%self.cols),
        #             ((r-1)%self.rows, (c+1)%self.cols), ((r-1)%self.rows, (c-1)%self.cols)]

        possibles = self.get_radius(loc, self.border_area)

        high = None
        high_val = -1000
        for row,col in possibles:
            if self.map[row][col] > high_val:
                high = (row,col)
                high_val = self.map[row][col]
        return high

    def all_val_locs(self, loc):
        possibles_spaces = self.get_radius(loc, set(self.visible_area)-self.water-set([loc]))
        val_vs_spaces =[ (self.map[r][c], (r,c)) for r,c in possibles_spaces ]

        values = set([ val for val, loc in val_vs_spaces ])

        ordered_spaces = []
        for value in values:
            locs = [loc for val,loc in val_vs_spaces if val == value]
            shuffle(locs)
            ordered_spaces.append((value, locs))

        ordered_spaces.sort(reverse=True)
        return ordered_spaces
        # [ (dist1, [loc1, loc2, loc3]), (dist2, [loc1, loc2, loc3]), (dist3, [loc1, loc2, loc3]),]

    def max_val_locs(self, loc):
        possibles_spaces = self.get_radius(loc, self.ring)
        val_vs_loc =[ (self.map[r][c], (r,c)) for r,c in possibles_spaces ]

        values = set([ val for val, loc in val_vs_loc ])
        max_val = max(values)
        locs = [loc for val,loc in val_vs_loc if val == max_val]

        return locs


    def print_map(self, center):
        c_row, c_col = center
        for row in range(c_row-10, c_row+10):
            print self.map[row%self.rows][(c_col-10)%self.cols:(c_col+10)%self.cols]

    def fill_area(self, area, num):
        for r,c in area:
            self.map[r][c] = num