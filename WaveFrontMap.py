from collections import deque
from math import sqrt
from random import shuffle

UNSEEN = 100
WATER = -100

class WaveFrontMap(object):

    def __init__(self, rows, cols, origin, view_radius2):
        self.rows = rows
        self.cols = cols
        self.origin = origin

        self.map = [[UNSEEN]*cols for row in range(rows)]
        self.water = set()
        self.visited = set()
        self.known_locs = set()
        self.known_land = set()

        self.next_loc = deque()
        self.next_loc.append((origin, 0))

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

        self.visible_area = get_pre_radius(int(sqrt(view_radius2)))

    def neighborhood(self, loc):
        row, col = loc
        neighborhood = set([((row)%self.rows, (col+1)%self.cols),
                            ((row)%self.rows, (col-1)%self.cols),
                            ((row-1)%self.rows, (col)%self.cols),
                            ((row+1)%self.rows, (col)%self.cols) ])
        return neighborhood - self.water

    def get_radius(self, loc, area):
        a_row, a_col = loc
        return set([ ((a_row+v_row)%self.rows, (a_col+v_col)%self.cols) for v_row, v_col in area])


    def update(self, ants):
        rad = self.get_radius
        va = self.visible_area

        for loc in ants.my_ants():
            self.known_locs.update(rad(loc, va))

        self.water.update(ants.water())
        self.known_land = self.known_locs - self.water

        self.wave_expand()


    def wave_expand(self):
        pending_locs = deque()

        while len(self.next_loc) > 0:
            loc, val = self.next_loc.popleft()
            if loc in self.known_locs:

                childs = list(self.neighborhood(loc))
                shuffle(childs)
                for child in childs:
                    if child not in self.visited:
                        self.visited.add(child)
                        c_row, c_col = child
                        self.map[c_row][c_col] = val + 1
                        self.next_loc.append((child, val+1))

            else:
                pending_locs.append((loc, val))

        self.next_loc = pending_locs

    def clear_dead_locs(self):
        for loc in self.known_land:
            neighborhood = self.neighborhood(loc)
            if len(neighborhood) == 1:
                row, col = loc
                self.map[row][col] *= -1


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
