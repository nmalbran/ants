#!/usr/bin/env python
from ants import *
from PathFinder import PathFinder
from random import shuffle
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
        # ants working in food orders
        self.working_ants = []
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
        
        self.rows = 0
        self.cols = 0
        self.turns = 0
        self.va = []
        self.neighbourhood = {}
        self.protect = {}
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
        self.turns = ants.turns
        #self.vr = ants.viewradius2
        #self.fr = ants.spawnradius2
        
        # visible area for an ant
        ants.visible((1,1))
        va = []
        if hasattr(ants, 'vision_offsets_2'):
            va = ants.vision_offsets_2
        self.va = va
        
        #rows = range(ants.rows)
        #cols = range(ants.cols)
        #self.unseen = [ (r,c) for r in rows for c in cols ]
    
    def possible_moves(self, loc):
        d = self.ants.destination
        moves = [ loc for loc in [ d(loc, direction) for direction in self.rose ] if loc not in self.water ]
        return moves
    
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
        self.water.update(set(ants.water_list))
        
        #shuffle(self.rose)
        
        # define or update neighbourhood
        if self.first:
            for hill in ants.my_hills():
                h_row, h_col = hill
                self.neighbourhood[hill] = set([ (h_row+v_row, h_col+v_col) for v_row, v_col in self.va])
                self.protect[hill] = set([(h_row+1,h_col+1), (h_row-1,h_col-1), (h_row-1,h_col+1), (h_row+1,h_col-1)])
        else:
            old_neighbourhood = self.neighbourhood
            self.neighbourhood = {}
            for hill in ants.my_hills():
                if hill in old_neighbourhood:
                    self.neighbourhood[hill] = old_neighbourhood[hill]
        
        # ants that have'nt moved yet
        free_ants = ants.my_ants()[:]
        
        # remove water from unseen spaces
        #self.unseen.difference_update(set(ants.water_list))
        #self.unseen = [ i for i in self.unseen if i not in set(ants.water_list)]

        
        # find ant attack enemy ants near my hills
        enemys = set(ants.enemy_ants())
        for hill in ants.my_hills():
            enemys_near_hill = enemys & self.neighbourhood[hill]
            if len(enemys_near_hill) > 0:
                print("enemy close")
                for enemy_ant in enemys_near_hill:
                    paths = self.path_finder.BFS(enemy_ant, free_ants, self.possible_moves, False, 10, True)
                    if len(paths) > 0:
                        print("num atk: "+len(paths))
                        for path in paths:
                            self.do_move_location(path[2], path[1][path[2]])
        
        new_orders = {}
        # work in food_orders (food_loc, path)
        for ant_loc in self.working_ants[:]:
            # if ant is still alive and if food still exist, go for it
            if ant_loc in free_ants and self.food_orders[ant_loc][0] in ants.food():
                new_loc = self.food_orders[ant_loc][1][ant_loc]
                if self.do_move_location(ant_loc, new_loc, free_ants) and new_loc == self.food_orders[ant_loc][0]:
                    self.food_targets.remove(new_loc) # discard collected food
                new_orders[new_loc] = self.food_orders[ant_loc]
                # if food disappear or ant is dead, cancel order

        self.food_orders = new_orders
        self.working_ants = self.food_orders.keys()

        # estimate timing start
        if self.fifth == 0:
            ini = time.time()

        if t()-self.times['bfs'] > 20:
            # find close food, ~1ms/ant
            for ant_loc in free_ants[:]:
                path = self.path_finder.BFS(ant_loc, set(ants.food())-self.food_targets, self.possible_moves)
                if len(path) > 0:
                    if self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                        self.food_targets.add(path[0][2])
                        self.food_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])
                        self.working_ants.append(path[0][1][ant_loc])
        
        # estimate timing stop
        if self.fifth == 0:
            self.times['bfs'] = int(1000*(time.time()-ini))+2


        # hills and neighbourhood
        hills_neighbourhood = set(ants.my_hills()) | set([ l for h in ants.my_hills() for l in self.possible_moves(h) ])
        # unblock own hill
        for hill_loc in hills_neighbourhood:
            if hill_loc in free_ants:
                for direction in self.rose:
                    if self.do_move_direction(hill_loc, direction, free_ants):
                        break

        # defend hills, mantain 3 ants close to hill
        for hill in ants.my_hills():
            if ants.my_ants() > 8:
                ants_in_hills = self.neighbourhood[hill] & set(free_ants)
                if len(ants_in_hills) <= 3:
                    for ant_loc in ants_in_hills:
                        free_ants.remove(ant_loc)
                else:
                    i = 0
                    for ant_loc in ants_in_hills:
                        if i>3:
                            break
                        free_ants.remove(ant_loc)
                        i+=1

        # check if we still have time left to calculate more orders
        if t() < 10:
            return

        # detect enemy hills
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)
        
        # check if we still have time left to calculate more orders
        if t() < 10:
            return
        
        # check for razed hills
        for enemy_hill in self.hills[:]:
            if enemy_hill in ants.my_ants():
                self.hills.remove(enemy_hill)

        # check if we still have time left to calculate more orders
        if t() < 10:
            return

        # estimate timing start
        if self.fifth == 1:
            ini = time.time()

        if t()-self.times['enemy_hill'] > 30:
            # calculate distance from every free ant to the enemy hill
            ant_dist = [ (d(ant_loc, hill_loc), ant_loc) for hill_loc in self.hills for ant_loc in free_ants ]
        
        # estimate timing stop
        if self.fifth == 1:
            self.times['enemy_hill'] = int(1000*(time.time()-ini))+3
            #print("enemy-hill: "+str(self.times['enemy_hill']))

        ant_dist.sort()
        # check if we still have time left to calculate more orders
        if t() < 10:
            return

        # attack hills
        for dist, ant_loc in ant_dist:
            self.do_move_location(ant_loc, hill_loc, free_ants)
        
        # check if we still have time left to calculate more orders
        if t() < 10:
            return

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
            path = self.path_finder.BFSexplore(ant_loc, self.possible_moves, 10)
            if len(path) > 0 and self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                self.explore_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])

        # estimate timing stop
        if self.fifth == 4:
            self.times['unseen'] = int(1000*(time.time()-ini))/num +2
            #print("unseen: "+str(self.times['unseen']))
        
        print("time left: "+str(t()))
            
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
