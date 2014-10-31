import sys

def main():
    density = 20
    offset = 2.5e-06
    tree = MinSVTree(density)
    size = 0.1
    time = 0.0
    failures = 0
    successes = 0
    while time <= 1.0:
        for _ in xrange(10):
            start = time + offset
            end = start + (size / 1.0)
            print "t:", time
            print "b:", start
            print "e:", end
            channel = tree.channel_search(start, end)
            print "c:", channel
            if channel is not None:
                tree.update_tree(time, True)
                successes += 1
                print "s + 1"
            else:
                tree.update_tree(time)
                failures += 1
                print "f + 1"
            #print "tree:"
            #tree.print_in_order()
            print "links:", tree.busy_links(time)
            print "---------------------------------------------------"
            raw_input()
            time += 0.003
        time += 0.003
    print "s:", successes
    print "f:", failures
    

from math import log, floor, pow

class Node(object):
    def __init__(self, subtree_median_start = 0.0):
        self.subtree_median_start = subtree_median_start
        self.is_node = True # attribute for not invoking isinstance(obj, class) function
    
    def __str__(self):
        return str(self.subtree_median_start)

class Leaf(object):
    def __init__(self, channel, start, end):
        self.is_node = False # attribute for not invoking isinstance(obj, class) function
        self.channel = channel
        self.start = start
        self.end = end
    
    def __str__(self):
        return str(self.channel) + " : " + str(self.start) + "-" + str(self.end)


class MinSVTree(object):
    def __init__(self, number_of_channels):
        '''This is so that array indexes matches tree position respectively,
           but also len(self.array) returns the number of nodes plus one'''
        self.array = [0]
        '''Since there are count(leaves) - 1 internal nodes in a balanced binary tree like this one'''
        for _ in xrange(number_of_channels - 1):
            self.array.append(Node()) # appending internal nodes
        '''Used for tracking the end of internal nodes and beginning of leaf nodes (which is self.last_node + 1)'''
        self.internal_node_count = number_of_channels - 1
        for channel in xrange(number_of_channels): # now appending leaves
            self.array.append(Leaf(channel, 0.0, float("infinity"))) # initial void is from 0.0 to infinity (end of simulation = UNTIL)
        
    '''
    Use print_in_order() to print to the console a better visual representation of a MinSVTree stored in an array.
    Root is index = 1 (self.array[0] is not a node). Output should be like:
            7 : root.right.right
        3 : root.right
            6 : root.right.left
    1 : root
            5 : root.left.right
        2 : root.left
            4 : root.left.left
    '''
    def print_in_order(self, index = 1, number_of_tabs = 0):
        size = len(self.array)
        if index * 2 + 1 < size:
            self.print_in_order(index * 2 + 1, number_of_tabs + 1)
        for _ in xrange(number_of_tabs):
            print "\t",
        print index, ":", self.array[index]
        if index * 2 < size:
            self.print_in_order(index * 2, number_of_tabs + 1)
    
    '''
    Use channel_search(start, end) to search for a void to handle a burst ranging in time from start to end.
    It searches the tree and fills the solution space in O(log n) time, where n is the size of the tree.
    The solution space or set comprises every node to the left of the first leaf it reaches.
    Which side to go is decided using internal nodes medians, comparing them to the burst start,
    The median itself is assumed to be on the left.
    The internal nodes medians are computed by update_median_start_time().
    If the first leaf reached is a solution, it surely is a MinSV solution, so it can be returned without further processing.
    This function returns the channel on which the burst is to be scheduled or None if solution returns None.
    '''
    def channel_search(self, burst_start, burst_end):
        solution_space = []
        index = 1 # index = 1 is the root (self.array[0] is not a node)
        array_size = (self.internal_node_count + 1) * 2
        
        #self.print_in_order()
        
        while index < array_size:
            if self.array[index].is_node:
                
                #print index, "is node"
                
                if burst_start > self.array[index].subtree_median_start:
                    
                    #print "start is higher than", index, "median"
                    
                    if 2 * index < array_size:
                        
                        #print "appending", index, "down/left children"
                        
                        solution_space.append(2 * index)
                        
                    #print "going up/right"
                    
                    index = 2 * index + 1
                else:
                    
                    #print "start lower than", index, "median"
                    #print "going down/left"
                    
                    index = 2 * index
            else: # if self.array[index] is a leaf node
                
                #print index, "is leaf"
                
                '''
                The author of the algorithm (XU et al. 2003) is not plain and explicitly clear
                if a burst lasting a minimum amount of time (like 1e-14) should be scheduled
                if its arrival (and ending) is at the same time a void start or ends.
                Because of that start and end times always have to be between the void gap, excluding it's boundaries.
                '''
                if self.array[index].start < burst_start and burst_end < self.array[index].end:
                    
                    #print "found a suitable void in", index, "!"
                    
                    chosen_void = self.array.pop(index)
                    if burst_start > chosen_void.start:
                        
                        #print "creating a new void between the void start and the burst start"
                        
                        new_void_before = Leaf(chosen_void.channel, chosen_void.start, burst_start)
                        self.array.append(new_void_before)
                    if burst_end < chosen_void.end:
                        
                        #print "creating a new void between the burst end and the void end"
                        
                        new_void_after = Leaf(chosen_void.channel, burst_end, chosen_void.end)
                        self.array.append(new_void_after)
                    return chosen_void.channel
                
                #print "didn't found a suitable void in", index, "..."
                
                break # since the node is a leaf, this is the same as choosing a side and let index >= size                
        return self.solution(solution_space, burst_start, burst_end)
    
    '''
    Use solution(set, start, end) to test if set contains a void eligible for scheduling a burst from start to end.
    The set should be traversed in reversed order because the leaves are ordered by the voids start times,
    so if more than one solution is available the algorithm returns the solution most to the right,
    making sure it gives the minimum gap between voids start time and the burst start time (MinSV).
    When a possible solution (an item from the set) is not a leaf,
    all leaves that have a straight down heritage with this node are traversed by search_subtree(node_index, end).
    If it finds a solution in the set, it returns the corresponding channel on which the burst is to be scheduled.
    If it doesn't find a solution, it returns None.
    '''
    def solution(self, solution_space, burst_start, burst_end):
        
        #print "solution space:", solution_space
        
        for index in reversed(solution_space):
            if self.array[index].is_node:                
                tree_size = (self.internal_node_count + 1) * 2
                subtree_solution = self.search_subtree(index, tree_size, burst_end)
                if subtree_solution is not None:
                    
                    #print "found a suitable void in", subtree_solution, "!"
                    
                    chosen_void = self.array.pop(subtree_solution)
                    if burst_start > chosen_void.start:
                        
                        #print "creating a new void between the void start and the burst start"
                        
                        new_void_before = Leaf(chosen_void.channel, chosen_void.start, burst_start)
                        self.array.append(new_void_before)
                    if burst_end < chosen_void.end:
                        
                        #print "creating a new void between the burst end and the void end"
                        
                        new_void_after = Leaf(chosen_void.channel, burst_end, chosen_void.end)
                        self.array.append(new_void_after)
                    return chosen_void.channel
            else: # if self.array[index] is a leaf node
                
                #print index, "is leaf"
                
                if self.array[index].end > burst_end:
                    
                    #print "found a suitable void in", index, "!"
                    
                    chosen_void = self.array.pop(index)
                    if burst_start > chosen_void.start:
                        
                        #print "creating a new void between the void start and the burst start"
                        
                        new_void_before = Leaf(chosen_void.channel, chosen_void.start, burst_start)
                        self.array.append(new_void_before)
                    if burst_end < chosen_void.end:
                        
                        #print "creating a new void between the burst end and the void end"
                        
                        new_void_after = Leaf(chosen_void.channel, burst_end, chosen_void.end)
                        self.array.append(new_void_after)
                    return chosen_void.channel
        else:
            
            #print "no void found"
            
            return None
    
    '''
    Use search_subtree(node_index, size, end) to recursively traverse a subtree with root at node from right to left,
    seeking a void that finishes after the burst's end.
    The start of the burst doesn't need to be checked because every leaf here is in the solution space of the channel_search function.
    The recursion returns None when a branch or the subtree doesn't hold a solution, or returns the index of a solution if it exists.
    '''
    def search_subtree(self, index, tree_size, burst_end):
        if self.array[index].is_node:
            
            #print index, "is node"
            
            if 2 * index + 1 < tree_size:
                
                #print "going up/right of", index
                
                subtree_solution = self.search_subtree(2 * index + 1, tree_size, burst_end)
                if subtree_solution is not None:
                    return subtree_solution
            if 2 * index < tree_size:
                
                #print "going down/left of", index
                
                subtree_solution = self.search_subtree(2 * index, tree_size, burst_end)
                if subtree_solution is not None:
                    return subtree_solution
        else: # if self.array[index] is a leaf node
            
            #print index, "is leaf"
            
            if self.array[index].end > burst_end:
                return index
        return None
    
    '''
    Use update_tree(current_time, True or False) to manage all updates required to do at the tree,
    after a solution is (or isn't) found.
    Use True when channel_search returns a void and False otherwise.
    This method should do a couple of things:
    - clear expired leaves (those are any leaf nodes (or voids) with an end time expired,
      in other words, voids that ends before the current_time) in any case;
    - if a solution was found or if there were expired leaves:
      - remove expired leaves from the tree, if that's the case;
      - build the new tree;
      - update median values in internal nodes.
    '''
    def update_tree(self, expiration_time, tree_was_modified = False):
        leaves = self.array[self.internal_node_count + 1:] # this is done so the leaves are preserved during the reconstruction process
        removable_leaves = []
        number_of_voids = 0
        '''Removing each leaf in this loop doesn't work because it changes the leaves set, leading to flaws in the process'''
        for leaf in leaves:
            number_of_voids += 1
            if leaf.end <= expiration_time:
                removable_leaves.append(leaf)
                tree_was_modified = True
        if tree_was_modified:
            for leaf in removable_leaves:
                number_of_voids -= 1
                leaves.remove(leaf)
            '''Again, this is so that array indexes matches tree position respectively,
               but also len(self.array) returns the number of nodes plus one'''
            self.array = [0]
            for _ in xrange(number_of_voids - 1):
                self.array.append(Node())
            '''The number of internal nodes is always equal to the number of leaves minus one'''
            self.internal_node_count = number_of_voids - 1
            '''
            The next seven lines of code illustrate a technique (Nioi Pier Giuliano, 2010),
            to make it feasible to use arrays for a balanced binary tree.
            The aim is to find level i (and in some cases i + 1) where the first leaf appears.
            From that you should know how many leaves are at level i,
            and how many should be at level i + 1 as a consequence of level i being already filled with some internal nodes.
            The number of internal nodes at level i is in fact the number of elements to shift from beginning to end in the leaves set,
            so that appending the leaves to the tree maintains balance.
            Arrays are better because they benefit from more compact storage and better locality of reference.
            '''
            leaves = sorted(leaves, key=lambda void: void.start)
            first_leaf_level = int(floor(log(number_of_voids, 2)))
            elements_to_the_end = int(2 * (number_of_voids - pow(2, first_leaf_level)))
            while elements_to_the_end:
                leaves.append(leaves[0])
                leaves.pop(0)
                elements_to_the_end -= 1
            for leaf in leaves:
                self.array.append(leaf)
            '''2 * number_of_voids is equal to len(self.array) because of self.array[0]'''
                
            #print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            #print "beginning median start times update..."
            #print "time:", expiration_time
            #self.print_in_order()
            
            self.update_median_start_time(number_of_voids + number_of_voids)
            
            #self.print_in_order()            
    
    '''
    Use update_median_start_time(size) to recursively update median void start times in internal nodes,
    so that comparing works on the channel_search function.
    This is needed to maintain the property that says that all solutions are to the left of the first leaf reached.
    Improvements could be made if one could keep track of new and old voids,
    and update only the median of the parents of those nodes (although the root, at least,
    would always have to look at the entire set of leaves to compute its median value).
    Keeping track of all leaf nodes each internal node has in its subtree is not practical for high counts of leaves.
    This function returns a void start value in a set, if the node being visited is a leaf node.
    Otherwise it returns the concatenation of each of its subtrees returns and updates its own median value before returning.
    '''
    def update_median_start_time(self, tree_size, index = 1): # complexity = O(n)
        temporary_set = []
        
        if self.array[index].is_node:
            
            #print index, "is node with initial temporary set:", temporary_set
            
            if index * 2 < tree_size:
                temporary_set += self.update_median_start_time(tree_size, index * 2)
                
                #print "temporary left set for", index, "is:", temporary_set
                
            if index * 2 + 1 < tree_size:
                temporary_set += self.update_median_start_time(tree_size, index * 2 + 1)
                
                #print "temporary final set for", index, "is:", temporary_set
            
            #print "setting", index, "median start time"
            
            '''self.array[index].subtree_median_start = median(temporary_set)'''
            self.array[index].subtree_median_start = mean(temporary_set)
            
            return temporary_set
        else: # if self.array[index] is a leaf node
            
            #print index, "is leaf with start", self.array[index].start
            
            temporary_set.append(self.array[index].start)
            return temporary_set


'''
This function was created because, if the median is used, instead of the mean, the algorithm doesn't work.
It returns the mean of the values of the set.
'''
def mean(ordered_set):
    
    #print ordered_set
    #print sum(ordered_set) / len(ordered_set)
    
    return sum(ordered_set) / len(ordered_set)

'''
Use median(set) to calculate the median of any already in order set.
This function returns the median of the set.
'''
# def median(ordered_set):
#     set_size = len(ordered_set)
#     
#     #print "set should be in order..."
#     print ordered_set
#     
#     if set_size % 2 == 0:
#         return (ordered_set[set_size // 2] + ordered_set[set_size // 2 - 1]) / 2
#     else:
#         return ordered_set[set_size // 2]
    
if __name__ == "__main__":
    sys.exit(main())