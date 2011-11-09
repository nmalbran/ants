#!/usr/bin/env python
from ants import *
from ExploreMap import ExploreMap
from PathFinder import PathFinder

class TestBot:
    def __init__(self):
        self.rose = ['n','e','s','w']
        self.water = set()
        self.path_finder = PathFinder()
        
    def do_setup(self, ants):
        self.map = ExploreMap(ants.rows, ants.cols)
        
        
    def possible_moves(self, obstacles):
        def temp(loc):
            d = self.ants.destination
            rose = self.rose
            moves = [ loc for loc in [ d(loc, direction) for direction in rose ] if loc not in obstacles ]
            return moves
        return temp  
        
    def do_move_direction(self, loc, direction):
        new_loc = self.ants.destination(loc, direction)
        if(self.ants.unoccupied(new_loc) and new_loc not in self.prox_dest):
            self.ants.issue_order((loc, direction))
            self.prox_dest.add(new_loc)
            return True
        else:
            return False
    
    def do_move_location(self, loc, dest):
        directions = self.ants.direction(loc, dest)
        for direction in directions:
            if self.do_move_direction(loc, direction):
                return True
        return False
  
        
    def do_turn(self, ants):
        self.ants = ants
        self.water.update(ants.water())
        self.prox_dest = set(ants.my_hills())
        
        #self.map.update(ants.my_ants(), self.possible_moves(self.water), ants.water(), ants.food())
        self.map.update(ants)
    
        #self.map.print_map(ants.my_hills()[0])
        
        for ant in ants.my_ants():
            new_loc = self.map.high_direction(ant)
            self.do_move_location(ant, new_loc)
            
        
        #print("time left: "+str(ants.time_remaining()))
            
            
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
        Ants.run(TestBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
