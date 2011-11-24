from math import sqrt
from random import shuffle

MAX_FOOD = 100000
MAX_EXPLORE = 10000
ANTS_COLLABORATION = -100

FOOD = 1
EXPLORE = 2

class DiffusionMap():
    def __init__(self, rows, cols, view_radius2):

        self.rows = rows
        self.cols = cols

        self.map = [[{FOOD:0, EXPLORE:0, 'last_seen':0}]*cols for row in range(rows)]
        self.water = set()
        self.food = set()
        self.visible = set()
        self.current_ants = set()
        self.all_locs = set([(r,c) for r in range(rows) for c in range(cols)])

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

    def get_radius(self, loc, area):
        a_row, a_col = loc
        return set([ ((a_row+v_row)%self.rows, (a_col+v_col)%self.cols) for v_row, v_col in area])

    def neighborhood(self, loc):
        row, col = loc
        neighborhood = set([((row)%self.rows, (col+1)%self.cols),
                            ((row)%self.rows, (col-1)%self.cols),
                            ((row-1)%self.rows, (col)%self.cols),
                            ((row+1)%self.rows, (col)%self.cols) ])
        return neighborhood - self.water

    def update(self, ants):
        rad = self.get_radius
        va = self.visible_area

        self.visible = set()

        for loc in ants.my_ants():
            self.visible.update(rad(loc, va))

        self.water.update(ants.water())
        self.update_last_seen()

        self.current_ants = set(ants.my_ants())

        for row in range(self.rows):
            for col in range(self.cols):
                self.diffuse(row, col)

    def update_last_seen(self):
        non_visible = self.all_locs - self.visible
        for row, col in non_visible:
            self.map[row][col]['last_seen'] += 1

        for row, col in self.visible:
            self.map[row][col]['last_seen'] = 0

    def diffuse(self, row, col):
        loc = (row, col)
        if loc in self.water:
            self.map[row][col][FOOD] = 0
            self.map[row][col][EXPLORE] = 0
            return

        if loc in self.current_ants:
            self.map[row][col][FOOD] = ANTS_COLLABORATION
            self.map[row][col][EXPLORE] = ANTS_COLLABORATION
            return


        goalsToDiffuse = []

        if loc in self.food:
            self.map[row][col][FOOD] = MAX_FOOD
        else:
            goalsToDiffuse.append(FOOD)


        if loc not in self.visible:
            self.map[row][col][EXPLORE] = MAX_EXPLORE - ((200 - self.map[row][col]['last_seen']) * 300)
        else:
            goalsToDiffuse.append(EXPLORE)


        for goal in goalsToDiffuse:
            up    = self.map[(row-1)%self.rows][col][goal]
            down  = self.map[(row+1)%self.rows][col][goal]
            left  = self.map[row][(col-1)%self.cols][goal]
            right = self.map[row][(col+1)%self.cols][goal]

            self.map[row][col][goal] = 0.25 * (up + down + left + right)


    def get_loc_highest_goal(self, loc, goal):
        neighborhood = list(self.neighborhood(loc))
        val_loc = [ (self.map[row][col][goal], (row, col)) for row, col in neighborhood]
        return max(val_loc)[1]


    def get_lower_locs(self,loc, goal):
        neighborhood = list(self.neighborhood(loc))
        shuffle(neighborhood)
        val_loc = [ (self.map[row][col][goal], (row, col)) for row, col in neighborhood]
        val_loc.sort()
        return val_loc

    def get_higher_locs(self,loc, goal):
        lowers = self.get_lower_locs(loc, goal)
        lowers.reverse()
        return lowers