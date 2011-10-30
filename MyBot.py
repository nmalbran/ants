#!/usr/bin/env python
from ants import *
from PathFinder import PathFinder
#from random import shuffle
import time

ROSE = ('n','e','s','w')

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
    def __init__(self):
        # define class level variables, will be remembered between turns
        self.path_finder = PathFinder()
        # orders already asigned
        self.orders = {}
        # ants working in orders
        self.working_ants = []
        # food spaces being hunted
        self.food_targets = set()
        # enemy's hills
        self.hills = []
        # unseen spaces
        self.unseen = set()
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
        
        rows = range(ants.rows)
        cols = range(ants.cols)
        self.unseen = [ (r,c) for r in rows for c in cols ]
    
    def possible_moves(self, loc):
        d = self.ants.destination
        moves = [ loc for loc in [ d(loc, direction) for direction in ROSE ] if loc not in self.water ]
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
        d = ants.distance
        self.fifth = (self.fifth +1)%5
        
        t = ants.time_remaining
        
        # ants that have'nt moved yet
        free_ants = ants.my_ants()[:]
        
        # update new water space found
        self.water.update(set(ants.water_list))
        
        # remove water from unseen spaces
        #self.unseen.difference_update(set(ants.water_list))
        #self.unseen = [ i for i in self.unseen if i not in set(ants.water_list)]
        
        # track all moves, prevent collisions and prevent stepping on own hill
        self.prox_dest = set(ants.my_hills())
        
        new_orders = {}
        # work in orders
        for ant_loc in self.working_ants[:]:
            # if ant is still alive
            if ant_loc in free_ants:
                # if food still exist, go for it
                if self.orders[ant_loc][0] in ants.food():
                    new_loc = self.orders[ant_loc][1][ant_loc]
                    if self.do_move_location(ant_loc, new_loc, free_ants):
                        new_orders[new_loc] = self.orders[ant_loc]
                    else:
                        new_orders[ant_loc] = self.orders[ant_loc]
                # if food disappear or ant is dead, cancel order
        self.orders = new_orders
        self.working_ants = self.orders.keys()
        

        # estimate timing start
        if self.fifth == 0:
            ini = time.time()

        if t()-self.times['bfs'] > 20:
            # find close food, ~1ms/ant
            for ant_loc in free_ants:
                path = self.path_finder.BFS(ant_loc, set(ants.food())-self.food_targets, self.possible_moves)
                if len(path) > 0:
                    if self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                        self.food_targets.add(path[0][2])
                        self.orders[path[0][1][ant_loc]] = (path[0][2],path[0][1])
                        self.working_ants.append(path[0][1][ant_loc])
        
        # estimate timing stop
        if self.fifth == 0:
            self.times['bfs'] = int(1000*(time.time()-ini))+2

        # unblock own hill
        for hill_loc in ants.my_hills():
            if hill_loc in free_ants:
                for direction in ROSE:
                    if self.do_move_direction(hill_loc, direction, free_ants):
                        break

        # check if we still have time left to calculate more orders
        if t() < 10:
            return

        # attack hills
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)
        
        # check if we still have time left to calculate more orders
        if t() < 10:
            return
        
        # check for razed hills

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

        for dist, ant_loc in ant_dist:
            self.do_move_location(ant_loc, hill_loc, free_ants)
        
        # check if we still have time left to calculate more orders
        if t() < 10:
            return

        # update unseen spaces, ~5-7ms
        v = ants.visible
        unseen = [ loc for loc in self.unseen if not v(loc) ]
        self.unseen = unseen
        
        # check if we still have time left to calculate more orders
        if t() < 20:
            return

        # estimate timing start
        if self.fifth == 4:
            num = len(free_ants)+1
            ini = time.time()
        
        # explore unseen areas
        for ant_loc in free_ants:
            if t()-self.times['unseen'] < 20:
                break
            unseen_dist = [ (d(ant_loc, unseen_loc), unseen_loc) for unseen_loc in self.unseen ]
            unseen_dist.sort()
            for dist, unseen_loc in unseen_dist:
                if self.do_move_location(ant_loc, unseen_loc, free_ants):
                    break

        # estimate timing stop
        if self.fifth == 4:
            self.times['unseen'] = int(1000*(time.time()-ini))/num +4
            #print("unseen: "+str(self.times['unseen']))
            
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
