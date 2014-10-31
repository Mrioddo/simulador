#!/usr/bin/env python2.7

'''Profiling tool'''
# from time import time

from config import NUMBER_OF_REPETITIONS

'''LOGGING'''
# from config import NUMBER_OF_WAVELENGTHS, LINK_WAVELENGTH_CAPACITY, NUMBER_OF_FLUX_ARRIVALS
# from config import AVERAGE_PACKET_SIZE, FIXED_ASSEMBLY_PERIOD, MEAN_INTERVAL_OF_PACKET_ARRIVAL, MINIMUM_FLUX_SIZE, MAXIMUM_FLUX_SIZE

from model import Model


def main():
    #TODO: I could try and remove parts from the Simulation library to make it faster for my special case.
    #      I just have to remember to make backup copies.
    
    deliveries = []
    drops = []

    '''LOGGING'''
#     counter = 0
#     count = True
#     while count:
#         try:
#             f = open("log" + str(counter) + ".txt", 'r')
#             counter += 1  
#             f.close()
#         except:
#             count = False
#     log = open("log" + str(counter) + ".txt", 'a')
#     log.write("---------------TUNNABLE PARAMETERS---------------------\n")
#     log.write("NUMBER_OF_WAVELENGTHS = {!s}\n".format(NUMBER_OF_WAVELENGTHS))
#     log.write("LINK_WAVELENGTH_CAPACITY = {!s}\n".format(NUMBER_OF_FLUX_ARRIVALS))
#     log.write("NUMBER_OF_FLUX_ARRIVALS = {!s}\n".format(LINK_WAVELENGTH_CAPACITY))
#     log.write("\n-----------------OTHER PARAMETERS----------------------\n")
#     log.write("MINIMUM_FLUX_SIZE = {!s}\n".format(MINIMUM_FLUX_SIZE))
#     log.write("MAXIMUM_FLUX_SIZE = {!s}\n".format(MAXIMUM_FLUX_SIZE))
#     log.write("MEAN_FLUX_ARRIVAL_INTERVAL = {!s}\n".format(MEAN_FLUX_ARRIVAL_INTERVAL))
#     log.write("AVERAGE_PACKET_SIZE = {!s}\n".format(AVERAGE_PACKET_SIZE))
#     log.write("MEAN_INTERVAL_OF_PACKET_ARRIVAL = {!s}\n".format(MEAN_INTERVAL_OF_PACKET_ARRIVAL))
#     log.write("FIXED_ASSEMBLY_PERIOD = {!s}\n".format(FIXED_ASSEMBLY_PERIOD))
#     log.write("\n---------------STARTING SIMULATION---------------------\n")
    
    
    for _ in xrange(NUMBER_OF_REPETITIONS):
        
#         before = time()
        obs_energy, obs_deliveries, obs_drops, obs_total, ocs_energy, ocs_deliveries, ocs_drops, ocs_total, nodes, end = Model().run()
#         after = time()
#         runtime = after - before
        
        deliveries.append(obs_deliveries + ocs_deliveries)
        drops.append(obs_drops + ocs_drops)
        
        print "\tdelivered".ljust(10) + "\tdroped".ljust(10) + "\tenergy".ljust(10)
          
        print "burst\t{!s:10}\t{!s:10}\t{!s} W in {!s} seconds".format(obs_deliveries, obs_drops, obs_energy, end)
        print "circuit\t{!s:10}\t{!s:10}\t{!s} MW per hour for {!s} nodes".format(ocs_deliveries, ocs_drops, ocs_energy / 1000.0, nodes)
        print "total\t{!s:10}\t{!s:10}".format(obs_deliveries + ocs_deliveries, obs_drops + ocs_drops)
        
#         if runtime > 60.0:
#             print "time spent to simulate:", (after - before) / 60.0, "minutes"
#         else:
#             print "time spent to simulate:", after - before, "seconds"
 
        obs_percentage = (obs_total / float(ocs_total + obs_total)) * 100
        ocs_percentage = (ocs_total / float(ocs_total + obs_total)) * 100
        print "OBS flux counter: {!s}%\t-> {!s}".format(obs_percentage, obs_total)
        print "OCS flux counter: {!s}%\t-> {!s}\n".format(ocs_percentage, ocs_total)
        
        '''LOGGING'''
#         log.write('\tdelivered'.ljust(10) + '\tdroped'.ljust(10) + '\tenergy'.ljust(10) + "\n")
#         log.write("burst\t{!s:10}\t{!s:10}\t{!s} W in {!s} seconds\n".format(my_simulation.num_of_burst_deliveries, 
#                                                       my_simulation.num_of_burst_drops, my_simulation.obs_energy,
#                                                       my_simulation.end))
#         log.write("circuit\t{!s:10}\t{!s:10}\t{!s} MW per hour for {!s} nodes\n".format(my_simulation.num_of_circuit_deliveries, 
#                                                         my_simulation.num_of_circuit_drops, my_simulation.ocs_energy / 1000.0, my_simulation.num_of_nodes))
#         log.write("total\t{!s:10}\t{!s:10}\n".format(my_simulation.num_of_burst_deliveries + my_simulation.num_of_circuit_deliveries,
#                                                       my_simulation.num_of_burst_drops + my_simulation.num_of_circuit_drops))
#         log.write("OBS flux counter: {!s}%\t-> {!s}\n".format(obs_percentage, my_simulation.obs_flux_counter))
#         log.write("OCS flux counter: {!s}%\t-> {!s}\n\n".format(ocs_percentage, my_simulation.ocs_flux_counter))

    print "mean deliveries: {!s}".format(float(sum(deliveries)) / len(deliveries))
    print "mean drops: {!s}\n".format(float(sum(drops)) / len(drops))
    
    '''LOGGING'''
#     log.write("mean deliveries: {!s}\n".format(float(sum(deliveries)) / len(deliveries)))
#     log.write("mean drops: {!s}\n\n".format(float(sum(drops)) / len(drops)))
#     log.close()

'''LOGGING'''
# def logprint(file_handle, string):
#     print string
#     file_handle.write(string + "\n")

if __name__ == "__main__":
#     from sys import exit        # Standard run
#     sys.exit(main())            # Standard run
    from cProfile import run    # Profiling tool
    run("main()", sort=1)       # Profiling run
