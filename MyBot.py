#!/usr/bin/env python
from ants import *
from PathFinder import PathFinder
from ExploreMap import ExploreMap
import random
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
        self.times = {'food':2, 'unseen':5, 'enemy_hill':5, 'attack_hill':10}
        self.fifth = -1

        # view area 
        self.va = []
        # visibles spaces around hills
        self.neighbourhood = {}
        # spaces with permanent ants, around hills
        self.protect = {}
        # exits from hills
        self.exitway = {}
        # defensive wall
        self.shield = {}
        self.first = True
        
        self.rose = ['n','e','s','w']
        #self.turn = 0
        
        self.not_spawned_ants = 0
    
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
        #fr2 = ants.spawnradius2
        random.seed(ants.player_seed)
        #self.unseen = [ (r,c) for r in range(ants.rows) for c in range(ants.cols) ]
        
        self.explore_map = ExploreMap(self.rows, self,cols)
        
        # precalculate squares around an ant, of radius sqrt(rad2)
        def get_pre_radius(rad2):
            offsets = []
            mx = int(sqrt(rad2))
            for d_row in range(-mx,mx+1):
                for d_col in range(-mx,mx+1):
                    d = d_row**2 + d_col**2
                    if d <= rad2:
                        offsets.append((
                            d_row%self.rows-self.rows,
                            d_col%self.cols-self.cols
                        ))
            return offsets
            
        extra_rad = 0
        ar2 = int(4*ants.attackradius2+(extra_rad**2)+4*extra_rad*sqrt(ants.attackradius2))
        extra_rad = 1
        dr2 = int(ants.attackradius2+(extra_rad**2)+2*extra_rad*sqrt(ants.attackradius2))

        self.va = get_pre_radius(ants.viewradius2) # visible area for an ant
        self.ar = get_pre_radius(ar2)              # attack area => attack rad*2 +2
        self.dr = get_pre_radius(dr2)              # defend area => attack rad +1
        self.food_rad = get_pre_radius(ants.spawnradius2)
        
    
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
            if loc in self.ants.my_hills():
                self.not_spawned_ants-=1
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
    
    def get_radius(self, loc, area):
        a_row, a_col = loc
        return set([ ((a_row+v_row)%self.rows, (a_col+v_col)%self.cols) for v_row, v_col in area])
        
    def get_shield(self, hill):
        h_row, h_col = hill
        shield = set([ (row%self.rows, col%self.cols) for row in range(h_row-2, h_row+2) for col in range(h_col-2, h_col+2) ])
        shield.remove(hill)
        shield.difference_update(self.water)
        shield.difference_update(set([((row+2)%self.rows, (col+2)%self.cols), ((row+2)%self.rows, (col-2)%self.cols),
                                      ((row-2)%self.rows, (col-2)%self.cols), ((row-2)%self.rows, (col+2)%self.cols)]))
        d = self.ants.euclidian_distance
        dist = [ (d(loc,hill), loc) for loc in shield ]
        dist.sort()
        return dist
        
    
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
        # numbers of ants, used to count not spawned ants
        n_ants = len(free_ants)
        
        # define or update neighbourhood (no need to remove razed hills)
        if self.first:
            self.not_spawned_ants = n_ants
            for hill in ants.my_hills():
                h_row, h_col = hill
                self.neighbourhood[hill] = self.get_radius(hill, self.va) - self.water
                self.protect[hill] = set([(h_row+1,h_col+1), (h_row-1,h_col-1), (h_row-1,h_col+1), (h_row+1,h_col-1)]) - self.water
                self.exitway[hill] = [((h_row+1,h_col), ['s']), ((h_row-1,h_col), ['n']), ((h_row,h_col+1), ['e']), ((h_row,h_col-1), ['w'])]
                self.shield[hill] = self.get_shield(hill)
        
        # remove water from unseen spaces
        #self.unseen.difference_update(ants.water())
        #self.unseen = [ i for i in self.unseen if i not in set(ants.water())]
        
        # detect enemy hills
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)
                
        # check for razed hills
        for enemy_hill in self.hills[:]:
            if enemy_hill in free_ants:
                self.hills.remove(enemy_hill)
        
        # find and attack enemy ants near my hills or make a shield around hill
        for hill in ants.my_hills():
            enemys_near_hill = set(ants.enemy_ants_nn()) & self.neighbourhood[hill]
            if len(enemys_near_hill) > 1:
                shield = self.shield[hill][:]
                if self.not_spawned_ants > 10: # if hidden ants, expand shield to let them out
                    shield.reverse()
                
                for dist, loc in shield:
                    if loc in free_ants: # if there is an ant, stay there
                        free_ants.remove(loc)
                        self.prox_dest.add(loc)
                    else: # search close ants and move it there
                        path = self.path_finder.BFS(loc, free_ants, self.possible_moves(self.water | set(ants.my_hills())), 1, 20, True)
                        if len(path) > 0:
                            self.do_move_location(path[0][2], path[0][1][path[0][2]], free_ants)
                
            else:
                for enemy_ant in enemys_near_hill:
                    paths = self.path_finder.BFS(enemy_ant, free_ants, self.possible_moves(self.water), 1, 10, True)
                    if len(paths) > 0:
                        self.do_move_location(path[0][2], path[0][1][path[0][2]], free_ants)
        
        # check time left
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
                    closest = self.path_finder.BFS(defend_loc, free_ants, self.possible_moves(self.water), 1, 10, True)
                    if len(closest) > 0:
                        self.do_move_location(closest[0][2], closest[0][1][closest[0][2]], free_ants)
                        
        # check time left
        if t() < 10:
            return
        
        # prevent fighting
        # safe dist: dont run if to close to a hill
        safe_dist = 9
        for ant_loc in free_ants[:]:
            around_enemys = self.get_radius(ant_loc, self.ar).intersection(ants.enemy_ants_nn())
            if len(around_enemys) == 1:
                enemy = around_enemys.pop()
                friends_around = self.get_radius(ant_loc, self.dr).intersection(free_ants)
               
                if len(friends_around) > 1: # if there is more friends, attack!
                    for ant in friends_around:
                        if ant in free_ants:
                            path = self.path_finder.BFS(ant, [enemy], self.possible_moves(self.water), 1, 6, False)
                            if len(path) >0:
                                self.do_move_location(ant, path[0][1][ant], free_ants)
                else:
                    dist = [ d(ant_loc, hill) for hill in ants.my_hills() ]
                    dist.append(100)
                    if min(dist) > safe_dist and ant_loc in free_ants:
                        # run
                        directions = set(self.rose).difference(ants.direction(ant_loc, enemy))
                        for direction in directions:
                            if self.do_move_direction(ant_loc, direction, free_ants):
                                break
                        # and call for help
                        #close_ants = self.path_finder.BFS(ant_loc, set(free_ants)-set([ant_loc]), self.possible_moves(self.water), 3, 10, True)
                        #for ant_path in close_ants:
                        #    self.do_move_location(ant_path[2], ant_path[1][ant_path[2]], free_ants)
                        
            elif len(around_enemys) > 1:
                friends_around = self.get_radius(ant_loc, self.dr).intersection(free_ants) # included ant_loc
                if len(friends_around) == 1: # if alone, run
                    dist = [ d(ant_loc, hill) for hill in ants.my_hills() ]
                    dist.append(100)
                    if min(dist) > safe_dist and ant_loc in free_ants:
                        directions = set(self.rose)
                        for enemy in around_enemys:
                            directions.difference_update(ants.direction(ant_loc, enemy))
                        for direction in directions:
                            if self.do_move_direction(ant_loc, direction, free_ants):
                                break
        # check time left
        if t() < 20:
            return

        # unblock own hill
        if n_ants > (15*len(ants.my_hills())):
            ideal_def = int(n_ants * 0.10)
        else:
            ideal_def = 0
        for hill in ants.my_hills():
            for loc, directions in self.exitway[hill]:
                if loc in free_ants:
                    for direction in directions:
                        if self.do_move_direction(loc, direction, free_ants):
                            break

            if hill in free_ants:
                if self.not_spawned_ants >= ideal_def:
                    for direction in self.rose:
                        if self.do_move_direction(hill, direction, free_ants):
                            break
                else:
                    free_ants.remove(hill)
        
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

        # check if we still have time left to calculate more orders
        if t() < 10:
            return


        # estimate timing start
        if self.fifth == 0:
            ini = time.time()
            
        # find close food, ~1ms/ant
        if t()-self.times['food'] > 20:
            for ant_loc in free_ants[:]:
                path = self.path_finder.BFS(ant_loc, set(ants.food())-self.food_targets, self.possible_moves(self.water))
                if len(path) > 0:
                    if self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                        self.food_targets.add(path[0][2])
                        self.food_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])
                        self.food_gathering_ants.append(path[0][1][ant_loc])
        
        # estimate timing stop
        if self.fifth == 0:
            self.times['food'] = int(1000*(time.time()-ini))+2


        # estimate timing start
#        if self.fifth == 1:
#            ini = time.time()
            
        # calculate distance from every free ant to the enemy hill
#        if t()-self.times['enemy_hill'] > 30:
#            ant_dist = [ (d(ant_loc, hill_loc), ant_loc, hill_loc) for hill_loc in self.hills for ant_loc in free_ants ]
#            ant_dist.sort()
        
        # estimate timing stop
#        if self.fifth == 1:
#            self.times['enemy_hill'] = int(1000*(time.time()-ini))+3
            #print("enemy-hill: "+str(self.times['enemy_hill']))

        # estimate timing start
        if self.fifth == 2:
            #num = len(free_ants)+1
            ini = time.time()

        # attack hills
        if t()-self.times['attack_hill'] > 20:
            for hill_loc in self.hills:
                paths = self.path_finder.BFS(hill_loc, set(free_ants), self.possible_moves(self.water), 30, 40, True)
                for path in paths:
                    if path[2] in free_ants and self.do_move_location(path[2], path[1][path[2]], free_ants):
                        self.attaking_orders[path[1][path[2]]] = (hill_loc, path[1])


        # attack hills
#        for dist, ant_loc, hill_loc in ant_dist:
#            if t()-self.times['attack_hill'] < 20:
#                break
#            if ant_loc in free_ants:
#                if dist < 60:
#                    path = self.path_finder.BFS(ant_loc, set([hill_loc]), self.possible_moves(self.water), 1, 30)
#                    if len(path) > 0 and self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
#                        self.attaking_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])
                #else:
                #    self.do_move_location(ant_loc, hill_loc, free_ants)
        
        # estimate timing stop
        if self.fifth == 2:
            self.times['attack_hill'] = int(1000*(time.time()-ini))+2#/num +2
        
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
            random.shuffle(self.rose)
            path = self.path_finder.BFSexplore(ant_loc, self.possible_moves(self.water.union(self.prox_dest)), 15)
            if len(path) > 0 and self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                self.explore_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])

        # estimate timing stop
        if self.fifth == 4:
            self.times['unseen'] = int(1000*(time.time()-ini))/num +2
            #print("unseen: "+str(self.times['unseen']))

        # check for collected food, aprox
        for food in ants.food():
            close_ants = self.get_radius(food, self.food_rad) & self.prox_dest
            if len(close_ants) > 0:
                self.not_spawned_ants+=1


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
# evitar peleas

# continuar con las ordenes de ataque
# continuar con las ordenes de comida

# despejar hormigueros

# buscar comida

# atacar hormigueros

# continuar con las ordenes de exploracion
# explorar

