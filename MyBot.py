#!/usr/bin/env python
from ants import *

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
    def __init__(self):
        # define class level variables, will be remembered between turns
        pass
    
    # do_setup is run once at the start of the game
    # after the bot has received the game settings
    # the ants class is created and setup by the Ants.run method
    def do_setup(self, ants):
#        self.loadtime = ants.loadtime
        self.rows = ants.rows
        self.cols = ants.cols
        self.turns = ants.turns
        self.vr = ants.viewradius2
        self.fr = ants.spawnradius2
        #self.ps = ants.player_seed

        self.hills = []
        self.unseen = []
        self.water = set()
        for row in range(ants.rows):
            for col in range(ants.cols):
                self.unseen.append((row, col))
    
    def possible_moves(self, loc):
        directions = list(AIM.keys())
        moves = []
        for direction in directions:
            moves.append(self.ants.destination(loc, direction))
        for loc in moves[:]:
            if loc in self.water:
                moves.remove(loc)
        return moves
    
    # do turn is run once per turn
    # the ants class has the game state and is updated by the Ants.run method
    # it also has several helper methods to use
    def do_turn(self, ants):
        self.ants = ants
        # ants that have'nt moved yet
        free_ants = ants.my_ants()[:]
        
        # update new water space found
        self.water.update(set(ants.water_list))
        
        # food spaces chosen by ant to hunt by
        food_targets = set()
        
        # remove water from unseen spaces
        for water in ants.water_list:
            if water in self.unseen:
                self.unseen.remove(water)        
        
        # track all moves, prevent collisions and prevent stepping on own hill
        prox_dest = set(ants.my_hills())
        
        def do_move_direction(loc, direction):
            new_loc = ants.destination(loc, direction)
            if(ants.unoccupied(new_loc) and new_loc not in prox_dest):
                ants.issue_order((loc, direction))
                prox_dest.add(new_loc)
                free_ants.remove(loc)
                return True
            else:
                return False
        
        def do_move_location(loc, dest):
            directions = ants.direction(loc, dest)
            for direction in directions:
                if do_move_direction(loc, direction):
                    return True
            return False
        
        # find close food
        ant_dist = []
        for food_loc in ants.food():
            for ant_loc in free_ants:
                dist = ants.distance(ant_loc, food_loc)
                ant_dist.append((dist, ant_loc, food_loc))
        ant_dist.sort()
        for dist, ant_loc, food_loc in ant_dist:
            if food_loc not in food_targets and ant_loc in free_ants:
                if do_move_location(ant_loc, food_loc):
                    food_targets.add(food_loc)
                
        
        # check if we still have time left to calculate more orders
#        if ants.time_remaining() < 10:
#            return

        # unblock own hill
        for hill_loc in ants.my_hills():
            if hill_loc in free_ants:
                for direction in ('s','e','w','n'):
                    if do_move_direction(hill_loc, direction):
                        break
        
        # check if we still have time left to calculate more orders
        if ants.time_remaining() < 10:
            return

        # attack hills
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)        
        ant_dist = []
        for hill_loc in self.hills:
            for ant_loc in free_ants:
                dist = ants.distance(ant_loc, hill_loc)
                ant_dist.append((dist, ant_loc))
        ant_dist.sort()
        for dist, ant_loc in ant_dist:
            do_move_location(ant_loc, hill_loc)

        # check if we still have time left to calculate more orders
#        if ants.time_remaining() < 10:
#            return

        # explore unseen areas
        for loc in self.unseen[:]:
            if ants.visible(loc):
                self.unseen.remove(loc)
        for ant_loc in free_ants:
            unseen_dist = []
            for unseen_loc in self.unseen:
                dist = ants.distance(ant_loc, unseen_loc)
                unseen_dist.append((dist, unseen_loc))
            unseen_dist.sort()
            for dist, unseen_loc in unseen_dist:
                if do_move_location(ant_loc, unseen_loc):
                    break
            
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
