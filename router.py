from config import NUMBER_OF_WAVELENGTHS as WAVELENGTH
from config import LINK_WAVELENGTH_CAPACITY as CAPACITY
from config import OPTICAL_ROUTER_CONSUMPTION as CONSUMPTION

from config import AVERAGE_PACKET_SIZE as PACKET_SIZE, FIXED_ASSEMBLY_PERIOD as ASSEMBLY_PERIOD, MEAN_INTERVAL_OF_PACKET_ARRIVAL as PACKET_INTERVAL

from min_sv_tree import MinSVTree

from math import log, sqrt
PART_A = 11.3088 / 9.0 # from Aleksic et al. (2011)
PART_B = 5.6544 / 9.0 # from Aleksic et al. (2011)

class Router(object):
    def __init__(self, router_id, topology):
        self.id = router_id
        self.energy_consumption = CONSUMPTION["SWITCH_CONTROL_UNIT"] + CONSUMPTION["MANAGEMENT_CARD"]
        self.obs_energy_consumption = 0
        self.ocs_energy_consumption = 0
        self.connecting_fibers = 0
        
        tree_density = WAVELENGTH // 2 # 50% of the fiber for each paradigm, set by me
        '''Used in MinSV for burst switching'''
        self.void_tree = {}
        '''Used in horizon for circuit switching'''
        self.fiber_links = {}
        '''Used in horizon for burst switching'''
        self.OBS_fiber_links = {}
        
        self.link_available = {}#True
        
        for adjacent_node in topology[router_id]:
            self.connecting_fibers += 1
            self.void_tree[adjacent_node] = MinSVTree(tree_density)
            self.fiber_links[adjacent_node] = [0] * (WAVELENGTH - tree_density)
            self.OBS_fiber_links[adjacent_node] = [0] * (tree_density)
            
            self.link_available[adjacent_node] = True
            
        n = sqrt(self.connecting_fibers * tree_density / 2.0) # n is the number of ports belonging to a single switching unit of the three-stage Clos network
        k = 2 * n # k is one parameter (the other is p) used to ensure that the Clos network is non-blocking
        self.fast_switch_port_consumption = PART_A * log(k - 1, 2) + PART_B * log(k) + 12 * k - 4
        self.fast_switch_port_consumption /= 3600.0 # Transforming in W per second
        
        self.ocs_energy_consumption += 3600.0 * (CONSUMPTION["SLOW_SWITCH"] + CONSUMPTION["TRANSCEIVER"] + CONSUMPTION["CIE/R"] + CONSUMPTION["WAVELENGTH_CONVERTER"]) * self.connecting_fibers * (WAVELENGTH - tree_density)
        self.energy_consumption += self.connecting_fibers * CONSUMPTION["OPTICAL_AMPLIFIER"]
        # The optical amplifier consumption is being counted as overall energy because although the slow switch,
        # used to forward circuits, is always on, the fast switch is not always off because it is turned on when it's going to be used,
        # so it should be counted into both techniques
        self.energy_consumption *= 3600.0
    
    '''Functions for data coming from the router's upper layers'''
    def schedule_local_burst(self, next_route_node, burst_size, offset, now):
        tree = self.void_tree[next_route_node]
        burst_start = now + offset
        burst_end = burst_start + (float(burst_size) / CAPACITY)
        scheduled_channel = tree.channel_search(burst_start, burst_end)
        if scheduled_channel is not None:
            tree.update_tree(now, True)
            self.obs_energy_consumption += (burst_end - burst_start) * (CONSUMPTION["TRANSCEIVER"] + (CONSUMPTION["CIE/R"] / 2.0))
            # I'm assuming that the CIE/R energy consumption corresponds to both the CIE and CIR, and only the CIR is used here
            return True
        else:
            tree.update_tree(now)
            return False
        
    def LAUC_schedule_local_burst(self, next_route_node, burst_size, offset, now):
        sub_waves = self.OBS_fiber_links[next_route_node]
        burst_start = now + offset
        lauc_horizon = 0
        lauc = None # LAUC stands for Latest Available Unscheduled Channel
        for index, horizon in enumerate(sub_waves):
            if (horizon < burst_start) and (lauc_horizon < horizon):
                lauc_horizon = horizon
                lauc = index
        if lauc is not None:
            burst_end = burst_start + (burst_size / CAPACITY)
            sub_waves[lauc] = burst_end
            self.obs_energy_consumption += (burst_end - burst_start) * (CONSUMPTION["TRANSCEIVER"] + (CONSUMPTION["CIE/R"] / 2.0))
            # I'm assuming that the CIE/R energy consumption corresponds to both the CIE and CIR, and only the CIR is used here
            return True
        else:
            return False
    
    def ocs_has_link_available(self, adjacent_node):
        return self.link_available[adjacent_node]
    
    def schedule_local_circuit(self, next_route_node, data_arrival, data_size):
        sub_waves = self.fiber_links[next_route_node]
        minimum_horizon = data_arrival
        wavelength = None
        for index, horizon in enumerate(sub_waves):
            if (horizon < data_arrival) and (horizon < minimum_horizon):
                minimum_horizon = horizon
                wavelength = index
        if wavelength is not None:
            sub_waves[wavelength] = data_arrival + (data_size / CAPACITY)
            return True
        else:
            self.link_available[next_route_node] = False            
            return False
        
    def select_paradigm(self, ocs_drops, ocs_deliveries, rate, flux_size, route_size):
        """
        1 - UTILIZACAO DA REDE
        2 - GANHO EM MULTIPLEXACAO ESTATISTICA (OBS)
        3 - CUSTOS DE: SINALIZACAO E RESERVA DE RECURSOS
        4 - *CONSUMO DE ENERGIA        
        """
        
        #TODO: update this table.
        #        x = 10,00 %          |        y = 5,00 %
        #    OCS blocking rate < x    |    OBS energy rate < y   |    Choice
        #            True             |           True           |     OCS
        #            True             |           False          |     OCS
        #            False            |           True           |     OBS
        #            False            |           False          |     OCS
        
        if ocs_drops > 0:
            blocking_rate = float(ocs_drops) / float(ocs_deliveries + ocs_drops)
        else:
            blocking_rate = 0
        
        if blocking_rate * 100.0 < 1.0:#5.0:
            return "OCS"
        
        PACKET_RATE = 1.0 / PACKET_INTERVAL        
        MEAN_BURST_DURATION = PACKET_RATE * ASSEMBLY_PERIOD * PACKET_SIZE # also its size
        NUMBER_OF_MEAN_BURSTS = flux_size / MEAN_BURST_DURATION
        
        local_obs_energy_consumption = (CONSUMPTION["TRANSCEIVER"] + (CONSUMPTION["CIE/R"] / 2.0))
        # this should be zero because the self.ocs_energu_consumption only counts local energy consumption
        obs_energy_consumption = 0#(CONSUMPTION["TRANSCEIVER"] + CONSUMPTION["CIE/R"] + CONSUMPTION["WAVELENGTH_CONVERTER"] + self.fast_switch_port_consumption)
        obs_energy = (2 / 2 * local_obs_energy_consumption + (route_size - 2) * obs_energy_consumption) * MEAN_BURST_DURATION
        
#         print "1:", obs_energy
        
        obs_energy *= NUMBER_OF_MEAN_BURSTS
        
#         print "2:", obs_energy
        
        # this calculates how much bigger is the energy to send the whole flux through OBS compared to OCS from this node to the next
        obs_to_ocs_rate = obs_energy / self.ocs_energy_consumption
        
#         print "ocs:", self.ocs_energy_consumption
#         print "rate:", obs_to_ocs_rate
#          
#         raw_input()
        
        if obs_to_ocs_rate < 100.0:#20.0:
            return "OBS"
        else:
            return "OCS"
        
#         LAMBDA = rate
#         MEAN_PACKET_SIZE = AVERAGE_PACKET_SIZE
#         V = CAPACITY
#         MEAN_SERVICE_TIME = MEAN_PACKET_SIZE / V
#         p = LAMBDA * MEAN_SERVICE_TIME
#         ocs_utilization = p
#         
#         T = ASSEMBLY_PERIOD
#         MEAN_BURST_SIZE = LAMBDA * T * MEAN_PACKET_SIZE
#         
#         #COSTS CALCULATIONS
#         
#         H = route_size
#         pj = PROCESSING_TIME
#         S = flux_size
#         MEAN_NUMBER_OF_BURSTS = S / MEAN_BURST_SIZE
#         obs_cost = MEAN_NUMBER_OF_BURSTS * (V * H * pj) / ((V * H * pj) + MEAN_BURST_SIZE)
#         obs_cost *= 1.0 / MEAN_NUMBER_OF_BURSTS
#         
#         a = MEAN_PACKET_SIZE
#         b = 1.0 - MEAN_PACKET_SIZE
#         PACKET_SIZE_VARIANCE = (a * b) / (((a + b)**2) * (a + b + 1.0))
#         PACKET_SIZE_STANDARD_DEVIATION = abs(PACKET_SIZE_VARIANCE)**0.5
#         COEFFICIENT_OF_VARIATION = PACKET_SIZE_STANDARD_DEVIATION / MEAN_PACKET_SIZE
#         r = (MEAN_SERVICE_TIME + p * MEAN_SERVICE_TIME * (1.0 + COEFFICIENT_OF_VARIATION**2)) / (2.0 * (1.0 - p))
#         MEAN_NUMBER_OF_PACKETS = S / MEAN_PACKET_SIZE
#         ocs_cost = (2.0 * H * pj) / (2.0 * H * pj + MEAN_NUMBER_OF_PACKETS * r)
#         ocs_cost *= 1.0 / MEAN_NUMBER_OF_BURSTS

    '''Functions for data passing through the router''' 
    def schedule_burst(self, burst_header, now):
        tree = self.void_tree[burst_header.next_route_node]
        burst_end = burst_header.burst_arrival + (float(burst_header.burst_size) / CAPACITY)
        scheduled_channel = tree.channel_search(burst_header.burst_arrival, burst_end)
        if scheduled_channel is not None:
            tree.update_tree(now, True)
            self.obs_energy_consumption += (burst_end - burst_header.burst_arrival) * (CONSUMPTION["TRANSCEIVER"] + CONSUMPTION["CIE/R"] + CONSUMPTION["WAVELENGTH_CONVERTER"] + self.fast_switch_port_consumption)
            return True
        else:
            tree.update_tree(now)
            return False
        #TODO: integrate burst scheduler with circuit scheduler by also updating fiber_links when scheduling a burst
        
    def LAUC_schedule_burst(self, burst_header):
        sub_waves = self.OBS_fiber_links[burst_header.next_route_node]
        burst_start = burst_header.burst_arrival
        lauc_horizon = 0
        lauc = None # LAUC stands for Latest Available Unscheduled Channel
        for index, horizon in enumerate(sub_waves):
            if (horizon < burst_start) and (lauc_horizon < horizon):
                lauc_horizon = horizon
                lauc = index
        if lauc is not None:
            burst_end = burst_start + (burst_header.burst_size / CAPACITY)
            sub_waves[lauc] = burst_end
            self.obs_energy_consumption += (burst_end - burst_start) * (CONSUMPTION["TRANSCEIVER"] + CONSUMPTION["CIE/R"] + CONSUMPTION["WAVELENGTH_CONVERTER"] + self.fast_switch_port_consumption)
            # I'm assuming that the CIE/R energy consumption corresponds to both the CIE and CIR, and only the CIR is used here
            return True
        else:
            return False

    def schedule_circuit(self, circuit_header):
        sub_waves = self.fiber_links[circuit_header.next_route_node]
        minimum_horizon = circuit_header.circuit_expiration
        wavelength = None
        for index, horizon in enumerate(sub_waves):
            if (horizon < circuit_header.data_arrival) and (horizon < minimum_horizon):
                minimum_horizon = horizon
                wavelength = index
        if wavelength is not None:
            sub_waves[wavelength] = circuit_header.circuit_expiration
            return True
        else:            
            return False
        #TODO: integrate circuit scheduler with burst scheduler by also updating void_tree when scheduling a circuit
    
    def clean_circuit(self, now, next_route_node, expiration_time):
        sub_waves = self.fiber_links[next_route_node]
        for index in xrange(len(sub_waves)-1):
            if sub_waves[index] == expiration_time:
                sub_waves[index] = now
                break
        self.link_available[next_route_node] = True
