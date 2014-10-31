from SimPy.Simulation import Simulation, infinity
from networkx import read_gml, all_pairs_dijkstra_path

from config import TOPOLOGY, REFRACTION_INDEX, LIGHT_SPEED
from router import Router
from edge_node import LegacyNetwork

class Model(Simulation):
    def __init__(self):
        Simulation.initialize(self)
        # for topology documentation and methods look at the graph.py class at the networkx library
        self.topology = read_gml(TOPOLOGY)
        self.num_of_nodes = self.topology.number_of_nodes()
        for edge in self.topology.edges_iter():
            self.topology[edge[0]][edge[1]]['delay'] = self.propagation_delay(self.topology[edge[0]][edge[1]]['weight'])
        routes = all_pairs_dijkstra_path(self.topology)
        self.nodes = []        
        legacy_networks = []
        for router in self.topology:
            self.nodes.append(Router(router, self.topology))
            
            '''CODE'''
            legacy_networks.append(LegacyNetwork(self, router))
            self.activate(legacy_networks[router], legacy_networks[router].traffic_assembler(routes))

        '''TEST'''
#         legacy_networks.append(LegacyNetwork(self, 0))
#         self.activate(legacy_networks[0], legacy_networks[0].traffic_assembler(routes))
#         legacy_networks.append(LegacyNetwork(self, 1))
#         self.activate(legacy_networks[1], legacy_networks[1].traffic_assembler(routes))
#         legacy_networks.append(LegacyNetwork(self, 2))
#         self.activate(legacy_networks[2], legacy_networks[2].traffic_assembler(routes))
            
            
    def propagation_delay(self, distance): # distance should be in Km
        # (300e+3 / 1.5 = 200e+3 Km/s)
        # (300e+3 / 1.1 = 272e+3 Km/s)
        return distance / (LIGHT_SPEED / REFRACTION_INDEX) # this return how many seconds for a bit to traverse "distance" at 200e+3 Km/s
    
    def initialize(self):
        self.num_of_burst_deliveries = self.num_of_burst_drops = 0
        self.num_of_circuit_deliveries = self.num_of_circuit_drops = 0
        self.overall_flux_counter = self.obs_flux_counter = self.ocs_flux_counter = 0
        
    def run(self):
        self.initialize()
        
        '''LEGACY'''
#         self.end = UNTIL

        print self.simulate(infinity)
        self.end = self.now()
        
        constant_energy = ocs_energy = obs_energy = 0.0
        for router in self.nodes:
            '''Multiplying by the simulation duration is required because the power consumption unit being used is watts per seconds,
            and the simulation may have different durations than 1 second. The OBS energy is only accounted for the time it activates
            the router it's passing through, so it is already multiplied by the duration of its consumption.'''
            constant_energy += router.energy_consumption
            ocs_energy += router.ocs_energy_consumption
            obs_energy += router.obs_energy_consumption
        
        return (obs_energy, self.num_of_burst_deliveries, self.num_of_burst_drops, self.obs_flux_counter, ocs_energy, self.num_of_circuit_deliveries, 
                self.num_of_circuit_drops, self.ocs_flux_counter, self.num_of_nodes, self.end)
