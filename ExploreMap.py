class ExploreMap():

    def __init__(self, rows, cols, rad):
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
        self.visible_area = get_pre_radius(rad)
        radXrad = [(d_row%self.rows-self.rows, d_col%self.cols-self.cols)
                                for d_row in range(-(rad+1), rad+1)
                                for d_col in range(-(rad+1), rad+1)]
        self.border_area = set(radXrad) - set(self.visible_area)
        self.ring = get_pre_ring(6,7)



    def get_radius(self, loc, area):
        a_row, a_col = loc
        return set([ ((a_row+v_row)%self.rows, (a_col+v_col)%self.cols) for v_row, v_col in area])


    def update(self, ants):
        visibles = set()
        rad = self.get_radius
        va = self.visible_area

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
            self.map[r][c] = -1000



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

    def high_list(self, loc):
        possibles = self.get_radius(loc, self.ring)
        order =[ (self.map[r][c], (r,c)) for r,c in possibles ]
        order.sort()
        return order



    def print_map(self, center):
        c_row, c_col = center
        for row in range(c_row-10, c_row+10):
            print self.map[row%self.rows][(c_col-10)%self.cols:(c_col+10)%self.cols]

            # ver cuadros al rededor de vision con mayor puntaje, usar bfs para llegar

    def fill_area(self, area, num):
        for r,c in area:
            self.map[r][c] = num