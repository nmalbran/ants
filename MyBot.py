#!/usr/bin/env python
from ants import *
from PathFinder import PathFinder
from random import shuffle
from math import sqrt
import time

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
    def __init__(self):
        # define class level variables, will be remembered between turns
        self.path_finder = PathFinder()
        # orders already asigned
        self.food_orders = {}
        self.explore_orders = {}
        self.attaking_orders = {}
        # ants working
        self.food_gathering_ants = []
        #self.attaking_ants = []
        # food spaces being hunted
        self.food_targets = set()
        # enemy's hills
        self.hills = []
        # unseen spaces
        #self.unseen = set()
        # water spaces
        self.water = set()
        # spaces where ants will go
        self.prox_dest = set()
        
        # stats for timeout prevent
        self.times = {'bfs':2, 'unseen':5, 'enemy_hill':5}
        self.fifth = -1
        
        #self.rows = 0
        #self.cols = 0
        #self.turns = 0
        # view area 
        self.va = []
        # visibles spaces around hills
        self.neighbourhood = {}
        # spaces with permanent ants, around hills
        self.protect = {}
        # exits from hills
        self.exitway = {}
        self.first = True
        
        self.rose = ['n','e','s','w']
        #self.turn = 0
    
    # do_setup is run once at the start of the game
    # after the bot has received the game settings
    # the ants class is created and setup by the Ants.run method
    def do_setup(self, ants):
        #self.loadtime = ants.loadtime
        #self.turntime = ants.turntime
        self.rows = ants.rows
        self.cols = ants.cols
        #self.turns = ants.turns
        #self.vr = ants.viewradius2
        #self.fr = ants.spawnradius2
        extra_rad = 2
        ar2 = int(4*ants.attackradius2+(extra_rad**2)+4*extra_rad*sqrt(ants.attackradius2))

        # visible area for an ant
        ants.visible((1,1))
        self.va = ants.vision_offsets_2
        
        #self.unseen = [ (r,c) for r in range(ants.rows) for c in range(ants.cols) ]
        
        # precalculate squares around an ant to set as visible
        vision_offsets = []
        mx = int(sqrt(ar2))
        for d_row in range(-mx,mx+1):
            for d_col in range(-mx,mx+1):
                d = d_row**2 + d_col**2
                if d <= ar2:
                    vision_offsets.append((
                        d_row%self.rows-self.rows,
                        d_col%self.cols-self.cols
                    ))
        self.ar = vision_offsets
        
    
    # receive set of obstacles
    # return function giving possible moves using these obstacles
    def possible_moves(self, obstacles):
        def temp(loc):
            d = self.ants.destination
            rose = self.rose
            moves = [ loc for loc in [ d(loc, direction) for direction in rose ] if loc not in obstacles ]
            return moves
        return temp
        
    
    def do_move_direction(self, loc, direction, free_ants):
        new_loc = self.ants.destination(loc, direction)
        if(self.ants.unoccupied(new_loc) and new_loc not in self.prox_dest):
            self.ants.issue_order((loc, direction))
            self.prox_dest.add(new_loc)
            free_ants.remove(loc)
            return True
        else:
            return False
    
    def do_move_location(self, loc, dest, free_ants):
        directions = self.ants.direction(loc, dest)
        #shuffle(directions)
        for direction in directions:
            if self.do_move_direction(loc, direction, free_ants):
                return True
        return False
    
    def attack_radius(self, loc):
        a_row, a_col = loc
        return set([ ((a_row+v_row)%self.rows, (a_col+v_col)%self.cols) for v_row, v_col in self.ar])
    
    # do turn is run once per turn
    # the ants class has the game state and is updated by the Ants.run method
    # it also has several helper methods to use
    def do_turn(self, ants):
        self.ants = ants
        self.fifth = (self.fifth +1)%5
        #self.turn+=1
        
        d = ants.distance
        t = ants.time_remaining
        
        # track all moves, prevent collisions and prevent stepping on own hill
        self.prox_dest = set(ants.my_hills())
        
        # update new water space found
        self.water.update(ants.water())
        
        # ants that have'nt moved yet
        free_ants = ants.my_ants()[:]
        
        # detect enemy hills
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)
                
        # check for razed hills
        for enemy_hill in self.hills[:]:
            if enemy_hill in free_ants:
                self.hills.remove(enemy_hill)
        
        # define or update neighbourhood (no need to remove razed hills)
        if self.first:
            for hill in ants.my_hills():
                h_row, h_col = hill
                self.neighbourhood[hill] = set([ ((h_row+v_row)%self.rows, (h_col+v_col)%self.cols) for v_row, v_col in self.va])
                self.protect[hill] = set([(h_row+1,h_col+1), (h_row-1,h_col-1), (h_row-1,h_col+1), (h_row+1,h_col-1)]) - self.water
                self.exitway[hill] = [(hill, self.rose), ((h_row+1,h_col), ['s']), ((h_row-1,h_col), ['n']),
                                                         ((h_row,h_col+1), ['e']), ((h_row,h_col-1), ['w'])]
        #else:
        #    old_neighbourhood = self.neighbourhood
        #    old_protect = self.protect
        #    self.neighbourhood = {}
        #    self.protect = {}
        #    for hill in ants.my_hills():
        #        if hill in old_neighbourhood:
        #            self.neighbourhood[hill] = old_neighbourhood[hill]
        #            self.protect[hill] = old_protect[hill]
        
        # remove water from unseen spaces
        #self.unseen.difference_update(ants.water())
        #self.unseen = [ i for i in self.unseen if i not in set(ants.water())]

        
        # find and attack enemy ants near my hills
        for hill in ants.my_hills():
            enemys_near_hill = set(ants.enemy_ants_nn()) & self.neighbourhood[hill]
            if len(enemys_near_hill) > 0:
                for enemy_ant in enemys_near_hill:
                    paths = self.path_finder.BFS(enemy_ant, free_ants, self.possible_moves(self.water), False, 10, True)
                    if len(paths) > 0:
                        for path in paths:
                            self.do_move_location(path[2], path[1][path[2]], free_ants)
        
        # check if we still have time left to calculate more orders
        if t() < 10:
            return
        
        num = len(ants.my_ants())/(len(ants.my_hills())+1)
        if num > 6:
            protecting_ants = 4
        elif num > 3:
            protecting_ants = 2
        elif num > 1:
            protecting_ants = 1
        else:
            protecting_ants = 0

        # protect hills, maintain x ants around each hill
        for hill in ants.my_hills():
            i = 0
            for defend_loc in self.protect[hill]:
                if i >= protecting_ants:
                    break
                i+=1
                if defend_loc in free_ants: # if there is an ant, stay there
                    free_ants.remove(defend_loc)
                    self.prox_dest.add(defend_loc)
                else:
                    closest = self.path_finder.BFS(defend_loc, free_ants, self.possible_moves(self.water), True, 10, True)
                    if len(closest) > 0:
                        self.do_move_location(closest[0][2], closest[0][1][closest[0][2]], free_ants)
        
        # prevent fighting
#        for ant_loc in free_ants[:]:
#            around_enemys = self.attack_radius(ant_loc).intersection(ants.enemy_ants_nn())
#            if len(around_enemys) > 0:
#                around_friends = self.attack_radius(ant_loc).intersection(ants.enemy_ants_nn())
#                directions = set(self.rose)
#                for enemy in around_enemys:
#                    directions.difference_update(ants.direction(ant_loc, enemy))
#                for direction in directions:
#                    if self.do_move_direction(ant_loc, direction, free_ants):
#                        break
        
        
        # continue with attaking_orders
        new_orders = {}
        for ant_loc in free_ants[:]:
            if ant_loc in self.attaking_orders and self.attaking_orders[ant_loc][0] in self.hills:
                new_loc = self.attaking_orders[ant_loc][1][ant_loc]
                self.do_move_location(ant_loc, new_loc, free_ants)
                new_orders[new_loc] = self.attaking_orders[ant_loc]
        self.attaking_orders = new_orders
        
        # continue with food_orders (food_loc, path)
        new_orders = {}
        for ant_loc in self.food_gathering_ants[:]:
            # if ant is still alive and if food still exist, go for it
            if ant_loc in free_ants and self.food_orders[ant_loc][0] in ants.food():
                new_loc = self.food_orders[ant_loc][1][ant_loc]
                if self.do_move_location(ant_loc, new_loc, free_ants) and new_loc == self.food_orders[ant_loc][0]:
                    self.food_targets.remove(new_loc) # discard collected food
                new_orders[new_loc] = self.food_orders[ant_loc]
                # if food disappear or ant is dead, cancel order
        self.food_orders = new_orders
        self.food_gathering_ants = self.food_orders.keys()

        # estimate timing start
        if self.fifth == 0:
            ini = time.time()
            
        # find close food, ~1ms/ant
        if t()-self.times['bfs'] > 20:
            for ant_loc in free_ants[:]:
                path = self.path_finder.BFS(ant_loc, set(ants.food())-self.food_targets, self.possible_moves(self.water))
                if len(path) > 0:
                    if self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                        self.food_targets.add(path[0][2])
                        self.food_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])
                        self.food_gathering_ants.append(path[0][1][ant_loc])
        
        # estimate timing stop
        if self.fifth == 0:
            self.times['bfs'] = int(1000*(time.time()-ini))+2

        # unblock own hill
        for hill in ants.my_hills():
            for loc, directions in self.exitway[hill]:
                if loc in free_ants:
                    for direction in directions:
                        if self.do_move_direction(loc, direction, free_ants):
                            break

        # check if we still have time left to calculate more orders
        if t() < 10:
            return

        # estimate timing start
        if self.fifth == 1:
            ini = time.time()
            
        # calculate distance from every free ant to the enemy hill
        if t()-self.times['enemy_hill'] > 30:
            ant_dist = [ (d(ant_loc, hill_loc), ant_loc, hill_loc) for hill_loc in self.hills for ant_loc in free_ants ]
            ant_dist.sort()
        
        # estimate timing stop
        if self.fifth == 1:
            self.times['enemy_hill'] = int(1000*(time.time()-ini))+3
            #print("enemy-hill: "+str(self.times['enemy_hill']))

        # attack hills
        for dist, ant_loc, hill_loc in ant_dist:
            if ant_loc in free_ants:
                if dist < 30:
                    path = self.path_finder.BFS(ant_loc, set([hill_loc]), self.possible_moves(self.water), True, 30)
                    if len(path) > 0 and self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                        self.attaking_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])
                else:
                    self.do_move_location(ant_loc, hill_loc, free_ants)
        
        # update unseen spaces, ~5-7ms
        #v = ants.visible
        #unseen = [ loc for loc in self.unseen if not v(loc) ]
        #self.unseen = unseen
        
        # check if we still have time left to calculate more orders
        if t() < 25:
            return

        # continue with explore orders (dest, path)
        new_orders = {}
        for ant_loc in free_ants[:]:
            if ant_loc in self.explore_orders and ant_loc != self.explore_orders[ant_loc][0]:
                new_loc = self.explore_orders[ant_loc][1][ant_loc]
                self.do_move_location(ant_loc, new_loc, free_ants)
                new_orders[new_loc] = self.explore_orders[ant_loc]
        self.explore_orders = new_orders


        # estimate timing start
        if self.fifth == 4:
            num = len(free_ants)+1
            ini = time.time()

        # BFS explore
        for ant_loc in free_ants[:]:
            if t()-self.times['unseen'] < 20:
                break
            shuffle(self.rose)
            path = self.path_finder.BFSexplore(ant_loc, self.possible_moves(self.water.union(self.prox_dest)), 15)
            if len(path) > 0 and self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                self.explore_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])

        # estimate timing stop
        if self.fifth == 4:
            self.times['unseen'] = int(1000*(time.time()-ini))/num +2
            #print("unseen: "+str(self.times['unseen']))

        #if self.fifth == 4:
        #    print("time left: "+str(t()))
            
if __name__ == '__main__':
    # psyco will speed up python a little, but is not needed
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        Ants.run(MyBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')


# ORDEN DE ACCION:

# actualizar variables
# atacar enemigos cerca de los hormigueros
# dejar hormigas cerca

# continuar con las ordenes de ataque

# continuar con las ordenes de comida
# buscar comida

# despejar hormigueros

# atacar hormigueros

# continuar con las ordenes de exploracion
# explorar

