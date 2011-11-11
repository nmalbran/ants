#!/usr/bin/env python
from ants import *
from PathFinder import PathFinder
from ExploreMap import ExploreMap
#import random
from math import sqrt
import time

class MyBot:
    def __init__(self):
        self.path_finder = PathFinder()

        self.food_orders = {}
        self.food_targets = set()
        self.explore_orders = {}
        self.attaking_orders = {}
        self.food_gathering_ants = []

        self.enemy_hills = []
        self.water = set()
        self.prox_dest = set()

        self.times_stats = {'food':2, 'unseen':5, 'enemy_hill':5, 'attack_hill':10}
        self.fifth_turn = -1
        self.first_turn = True

        self.rose = ['n','e','s','w']
        self.not_spawned_ants = 0

        # visibles spaces around hills
        self.neighbourhood = {}
        # spaces with permanent ants, around hills
        self.hill_defending_locations = {}
        self.hill_exitway = {}
        self.hill_shield = {}


    def do_setup(self, ants):
        self.rows = ants.rows
        self.cols = ants.cols
        #random.seed(ants.player_seed)

        self.explore_map = ExploreMap(self.rows, self.cols, 3, ants.viewradius2)

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
        # rad*2 + extra_rad
        attack_rad2 = int(4*ants.attackradius2+(extra_rad**2)+4*extra_rad*sqrt(ants.attackradius2))

        extra_rad = 1
        # rad + extra_rad
        defend_rad2 = int(ants.attackradius2+(extra_rad**2)+2*extra_rad*sqrt(ants.attackradius2))

        self.ant_view_area = get_pre_radius(ants.viewradius2)
        self.ant_attack_area = get_pre_radius(attack_rad2)
        self.ant_defend_area = get_pre_radius(defend_rad2)
        self.food_rad = get_pre_radius(ants.spawnradius2)


    def do_turn(self, ants):
        self.ants = ants
        self.fifth_turn = (self.fifth_turn +1)%5

        time_left = ants.time_remaining

        # track all moves, prevent collisions and prevent stepping on my own hills
        self.prox_dest = set(ants.my_hills())
        self.water.update(ants.water())

        free_ants = ants.my_ants()[:]
        initial_n_ants = len(free_ants)

        self.explore_map.update(ants)

        if self.first_turn:
            self.not_spawned_ants = initial_n_ants
            self.set_hills_areas()
            self.first_turn = False

        self.detect_enemy_hills()
        self.check_razed_hills(free_ants)
        self.defend_my_hills(free_ants)

        if time_left() < 10:
            return

        self.maintain_ants_at_defending_location(initial_n_ants, free_ants)

        if time_left() < 10:
            return

        self.fight(free_ants)

        if time_left() < 20:
            return

        self.unblock_own_hill(initial_n_ants, free_ants)
        self.continue_with_attaking_orders(free_ants)
        self.continue_with_food_orders(free_ants)

        if time_left() < 10:
            return

        self.find_close_food(free_ants, time_left, 1)
        self.attack_enemy_hills(free_ants, time_left, 2)

        if time_left() < 25:
            return

        self.continue_with_explore_orders(free_ants)
        self.explore(free_ants, time_left, 3)

        if time_left() < 20:
            return

        self.check_collected_food()

        if self.fifth_turn == 4:
            print("time left: "+str(time_left()))




###############################################################################################
############### Helper Functions ##############################################################
###############################################################################################


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
        for direction in directions:
            if self.do_move_direction(loc, direction, free_ants):
                return True
        return False

    def get_radius(self, loc, area):
        a_row, a_col = loc
        return set([ ((a_row+v_row)%self.rows, (a_col+v_col)%self.cols) for v_row, v_col in area])

    def get_shield(self, hill):
        # .sss.
        # sssss
        # ssHss
        # sssss
        # .sss.

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




###############################################################################################
############### Action Functions ##############################################################
###############################################################################################


    def check_razed_hills(self, free_ants):
        for enemy_hill in self.enemy_hills[:]:
            if enemy_hill in free_ants:
                self.enemy_hills.remove(enemy_hill)

    def detect_enemy_hills(self):
        for hill_loc, hill_owner in self.ants.enemy_hills():
            if hill_loc not in self.enemy_hills:
                self.enemy_hills.append(hill_loc)

    def set_hills_areas(self):
        for hill in self.ants.my_hills():
            h_row, h_col = hill
            self.neighbourhood[hill] = self.get_radius(hill, self.ant_view_area) - self.water
            self.hill_defending_locations[hill] = set([(h_row+1,h_col+1), (h_row-1,h_col-1), (h_row-1,h_col+1), (h_row+1,h_col-1)]) - self.water
            self.hill_exitway[hill] = [((h_row+1,h_col), ['s']), ((h_row-1,h_col), ['n']), ((h_row,h_col+1), ['e']), ((h_row,h_col-1), ['w'])]
            self.hill_shield[hill] = self.get_shield(hill)

    def maintain_ants_at_defending_location(self, initial_n_ants, free_ants):
        my_hills = self.ants.my_hills()
        ants_per_hill = initial_n_ants/(len(my_hills)+1)
        if ants_per_hill > 6:
            n_expected_ants = 4
        elif ants_per_hill > 3:
            n_expected_ants = 2
        elif ants_per_hill > 1:
            n_expected_ants = 1
        else:
            n_expected_ants = 0

        for hill in my_hills:
            n_defending_ants = 0
            for defend_loc in self.hill_defending_locations[hill]:
                if n_defending_ants >= n_expected_ants:
                    break
                n_defending_ants+=1
                if defend_loc in free_ants: # if there is an ant, stay there
                    free_ants.remove(defend_loc)
                    self.prox_dest.add(defend_loc)
                else:
                    closest = self.path_finder.BFS(defend_loc, free_ants, self.possible_moves(self.water), backward=True)
                    if len(closest) > 0:
                        self.do_move_location(closest[0][2], closest[0][1][closest[0][2]], free_ants)

    def unblock_own_hill(self, initial_n_ants, free_ants):
        my_hills = self.ants.my_hills()
        if initial_n_ants > (15 * len(my_hills)):
            ideal_def = int(initial_n_ants * 0.10)
        else:
            ideal_def = 0
        for hill in my_hills:
            for loc, directions in self.hill_exitway[hill]:
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

    def check_collected_food(self):
        for food in self.ants.food():
            close_ants = self.get_radius(food, self.food_rad) & self.prox_dest
            if len(close_ants) > 0:
                self.not_spawned_ants+=1

    def continue_with_attaking_orders(self, free_ants):
        # orders_format: (hill_loc, path)
        new_orders = {}
        for ant_loc in free_ants[:]:
            if ant_loc in self.attaking_orders and self.attaking_orders[ant_loc][0] in self.enemy_hills:
                new_loc = self.attaking_orders[ant_loc][1][ant_loc]
                self.do_move_location(ant_loc, new_loc, free_ants)
                new_orders[new_loc] = self.attaking_orders[ant_loc]
        self.attaking_orders = new_orders

    def continue_with_food_orders(self, free_ants):
        # orders_format: (food_loc, path)
        foods = self.ants.food()
        new_orders = {}
        for ant_loc in self.food_gathering_ants[:]:
            # if ant is still alive and if food still exist, go for it
            if ant_loc in free_ants and self.food_orders[ant_loc][0] in foods:
                new_loc = self.food_orders[ant_loc][1][ant_loc]
                if self.do_move_location(ant_loc, new_loc, free_ants) and new_loc == self.food_orders[ant_loc][0]:
                    self.food_targets.remove(new_loc) # discard collected food
                new_orders[new_loc] = self.food_orders[ant_loc]
        self.food_orders = new_orders
        self.food_gathering_ants = self.food_orders.keys()

    def continue_with_explore_orders(self, free_ants):
        # orders_format: (dest_loc, path)
        new_orders = {}
        for ant_loc in free_ants[:]:
            if ant_loc in self.explore_orders and ant_loc != self.explore_orders[ant_loc][0]:
                new_loc = self.explore_orders[ant_loc][1][ant_loc]
                if self.do_move_location(ant_loc, new_loc, free_ants):
                    new_orders[new_loc] = self.explore_orders[ant_loc]
        self.explore_orders = new_orders


    def find_close_food(self, free_ants, time_left, stat_update_turn):
        if self.fifth_turn == stat_update_turn:
            ini = time.time()

        # ~1ms/ant
        foods = set(self.ants.food())
        possible_moves = self.possible_moves(self.water)

        if time_left()-self.times_stats['food'] > 20:
            for ant_loc in free_ants[:]:
                path = self.path_finder.BFS(ant_loc, foods-self.food_targets, possible_moves)
                if len(path) > 0:
                    if self.do_move_location(ant_loc, path[0][1][ant_loc], free_ants):
                        self.food_targets.add(path[0][2])
                        self.food_orders[path[0][1][ant_loc]] = (path[0][2], path[0][1])
                        self.food_gathering_ants.append(path[0][1][ant_loc])

        if self.fifth_turn == stat_update_turn:
            self.times_stats['food'] = int(1000*(time.time()-ini))+2

    def attack_enemy_hills(self, free_ants, time_left, stat_update_turn):
        if self.fifth_turn == stat_update_turn:
            #num = len(free_ants)+1
            ini = time.time()

        possible_moves = self.possible_moves(self.water)

        if time_left()-self.times_stats['attack_hill'] > 20:
            for hill_loc in self.enemy_hills:
                paths = self.path_finder.BFS(hill_loc, set(free_ants), possible_moves, num=30, max_cost=40, backward=True)
                for path in paths:
                    if path[2] in free_ants and self.do_move_location(path[2], path[1][path[2]], free_ants):
                        self.attaking_orders[path[1][path[2]]] = (hill_loc, path[1])

        if self.fifth_turn == stat_update_turn:
            self.times_stats['attack_hill'] = int(1000*(time.time()-ini))+2#/num +2

    def explore(self, free_ants, time_left, stat_update_turn):
        if self.fifth_turn == stat_update_turn:
            num = len(free_ants)+1
            ini = time.time()

        possible_moves = self.possible_moves(self.water)

        for ant_loc in free_ants[:]:
            if time_left()-self.times_stats['unseen'] < 20:
                break

            new_locs = self.explore_map.all_val_locs(ant_loc)
            for val, locs in new_locs:
                break2 = False
                paths = self.path_finder.BFS(ant_loc, set(locs), possible_moves, num=15, max_cost=15)
                for path in paths:
                    if self.do_move_location(ant_loc, path[1][ant_loc], free_ants):
                        self.explore_orders[path[1][ant_loc]] = (path[2], path[1])
                        break2 = True
                        break
                if break2:
                    break

        if self.fifth_turn == stat_update_turn:
            self.times_stats['unseen'] = int(1000*(time.time()-ini))/num +2
            #print("unseen: "+str(self.times_stats['unseen']))

    def defend_my_hills(self, free_ants):
        for hill in self.ants.my_hills():
            enemys_near_hill = set(self.ants.enemy_ants_nn()) & self.neighbourhood[hill]
            if len(enemys_near_hill) > 1:
                shield = self.hill_shield[hill][:]
                #if self.not_spawned_ants > 10: # if hidden ants, expand shield to let them out
                #    shield.reverse()

                possible_moves = self.possible_moves(self.water | set(self.ants.my_hills()))
                for dist, loc in shield:
                    if loc in free_ants: # if there is an ant, stay there
                        free_ants.remove(loc)
                        self.prox_dest.add(loc)
                    else: # search close ants and move it there
                        path = self.path_finder.BFS(loc, free_ants, possible_moves, max_cost=20, backward=True)
                        if len(path) > 0:
                            self.do_move_location(path[0][2], path[0][1][path[0][2]], free_ants)

            else:
                for enemy_ant in enemys_near_hill:
                    paths = self.path_finder.BFS(enemy_ant, free_ants, self.possible_moves(self.water), backward=True)
                    if len(paths) > 0:
                        self.do_move_location(paths[0][2], paths[0][1][paths[0][2]], free_ants)

    def fight(self, free_ants):
        # prevent fighting
        # safe dist: dont run if to close to a hill
        d = self.ants.distance
        safe_dist = 9
        for ant_loc in free_ants[:]:
            around_enemys = self.get_radius(ant_loc, self.ant_attack_area).intersection(self.ants.enemy_ants_nn())
            if len(around_enemys) == 1:
                enemy = around_enemys.pop()
                friends_around = self.get_radius(ant_loc, self.ant_defend_area).intersection(free_ants)

                if len(friends_around) > 1: # if there is more friends, attack!
                    possible_moves = self.possible_moves(self.water)
                    for ant in friends_around:
                        if ant in free_ants:
                            path = self.path_finder.BFS(ant, [enemy], possible_moves, max_cost=6)
                            if len(path) >0:
                                self.do_move_location(ant, path[0][1][ant], free_ants)
                else:
                    dist = [ d(ant_loc, hill) for hill in self.ants.my_hills() ]
                    dist.append(100)
                    if min(dist) > safe_dist and ant_loc in free_ants:
                        # run
                        directions = set(self.rose).difference(self.ants.direction(ant_loc, enemy))
                        for direction in directions:
                            if self.do_move_direction(ant_loc, direction, free_ants):
                                break
                        # and call for help
                        #close_ants = self.path_finder.BFS(ant_loc, set(free_ants)-set([ant_loc]), self.possible_moves(self.water), 3, 10, True)
                        #for ant_path in close_ants:
                        #    self.do_move_location(ant_path[2], ant_path[1][ant_path[2]], free_ants)

            elif len(around_enemys) > 1:
                friends_around = self.get_radius(ant_loc, self.ant_defend_area).intersection(free_ants) # included ant_loc
                if len(friends_around) == 1: # if alone, run
                    dist = [ d(ant_loc, hill) for hill in self.ants.my_hills() ]
                    dist.append(100)
                    if min(dist) > safe_dist and ant_loc in free_ants:
                        directions = set(self.rose)
                        for enemy in around_enemys:
                            directions.difference_update(self.ants.direction(ant_loc, enemy))
                        for direction in directions:
                            if self.do_move_direction(ant_loc, direction, free_ants):
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