from random import Random

from SimPy.Simulation import Process, hold, waituntil
from config import MINIMUM_FLUX_SIZE, MAXIMUM_FLUX_SIZE, MEAN_INTERVAL_OF_PACKET_ARRIVAL as SECONDS_PER_PACKET, AVERAGE_PACKET_SIZE as PACKET_SIZE
from config import NUMBER_OF_FLUX_ARRIVALS, PROCESSING_TIME, MEAN_FLUX_ARRIVAL_INTERVAL
from config import FIXED_ASSEMBLY_PERIOD as FAP
from control_packet import BurstHeader, CircuitControlPacket


class LegacyNetwork(Process):
    
    def __init__(self, simulation, edge_router_id):
        Process.__init__(self, sim=simulation)
        self.edge_node_id = edge_router_id
        self.ocs_senders = [None] * simulation.num_of_nodes
    
    def traffic_assembler(self, routes):
        rate = 1 / MEAN_FLUX_ARRIVAL_INTERVAL
        node_numbers = range(self.sim.num_of_nodes)
        node_numbers.remove(self.edge_node_id)
        generator = Random()
        obs_assemblers = {}
        
        select_mode = self.sim.nodes[self.edge_node_id].select_paradigm
        
        while self.sim.overall_flux_counter < NUMBER_OF_FLUX_ARRIVALS:
            self.sim.overall_flux_counter += 1
            seconds_to_next_flux_arrival = generator.expovariate(rate)
            yield hold, self, seconds_to_next_flux_arrival
            
            '''CODE'''
            destination_node = generator.choice(node_numbers)
            
            '''TEST'''
#             destination_node = 4
            
            route = routes[self.edge_node_id][destination_node]
            flux_size = generator.uniform(MINIMUM_FLUX_SIZE, MAXIMUM_FLUX_SIZE)
            
            if self.ocs_senders[destination_node] != None:
                self.sim.ocs_flux_counter += 1
                self.ocs_senders[destination_node].buffer_data(flux_size)
                self.sim.num_of_circuit_deliveries += 1
            else:
                route_size = len(route)
            
                mode = select_mode(self.sim.num_of_circuit_drops, self.sim.num_of_circuit_deliveries, rate, flux_size, route_size)            
                
                '''TEST'''
                mode = "OBS"
#                 mode = "OCS"
                
                if mode == "OBS":
                    self.sim.obs_flux_counter += 1
                    if not obs_assemblers.has_key(destination_node):
                        obs_assemblers[destination_node] = BurstAssembler(self.sim, self.edge_node_id)
                        self.sim.activate(obs_assemblers[destination_node], obs_assemblers[destination_node].run(route, route_size))
                    obs_sender = BurstAggregator(self.sim, self.edge_node_id)
                    self.sim.activate(obs_sender, obs_sender.run(flux_size, obs_assemblers[destination_node]))
                elif mode == "OCS":
                    self.sim.ocs_flux_counter += 1
                    circuit_sender = CircuitSender(self.sim, self.edge_node_id)
                    self.sim.activate(circuit_sender, circuit_sender.run(self, route, flux_size, route_size))


class CircuitSender(Process):    
    def __init__(self, simulation, edge_node_id):
        Process.__init__(self, sim=simulation)
        self.edge_node_id = edge_node_id
    
    def run(self, router, route, flux_size, route_size):
        self.data_size = flux_size

        router.ocs_senders[route[route_size-1]] = self
        
        circuit_control_packet_offset = 2 * (PROCESSING_TIME * (route_size-1))
        if not self.sim.nodes[route[0]].schedule_local_circuit(route[1], self.sim.now() + circuit_control_packet_offset, self.data_size):
            self.sim.num_of_circuit_drops += 1
        else:
            circuit_control_packet = CircuitControlPacket(self, self.sim, self.sim.overall_flux_counter, self.data_size, circuit_control_packet_offset)
            self.sim.activate(circuit_control_packet, circuit_control_packet.run(route, route_size))
            # This time was chosen because if it were longer than the simulation duration, the simulation wouldn't end as it should
            # It would output "SimPy: Normal exit at time 'UNTIL'", when it should output "SimPy: No more events at time 'X'"
            # And I couldn't come up with a rule for a smaller value than the end of the simulation for a hold made to be interrupted

            yield hold, self, circuit_control_packet.circuit_expiration#float("infinity")# - self.sim.now()#self.sim.end - self.sim.now() # waiting to be interrupted by the control packet
            #TODO: count the amounted waited and translate that into packets arrived
            if self.interrupted():
                self.interruptReset()
                if circuit_control_packet.has_dropped():
                    self.sim.num_of_circuit_drops += 1
                else:
                    buffered = 0.0
                    while buffered < (self.data_size - PACKET_SIZE) and not self.interrupted():
                        yield hold, self, SECONDS_PER_PACKET
                        buffered += PACKET_SIZE
                    if self.interrupted():
                        self.sim.num_of_circuit_drops += 1
                    else:
                        yield hold, self, SECONDS_PER_PACKET * ((self.data_size - buffered) / (PACKET_SIZE))
                        buffered += self.data_size - buffered
                        self.sim.num_of_circuit_deliveries += 1
                        self.interrupt(circuit_control_packet)
                    for route_node in xrange(route_size-2): # clean circuit in all nodes excluding the source and destination
                        self.sim.nodes[route[route_node+1]].clean_circuit(self.sim.now(), route[route_node+2], circuit_control_packet.circuit_expiration)

        router.ocs_senders[route[route_size-1]] = self             
    
    def buffer_data(self, data):
        self.data_size += data


class BurstAggregator(Process):
    def __init__(self, simulation, edge_node_id):
        Process.__init__(self, sim=simulation)
        self.edge_node_id = edge_node_id
    
    def run(self, flux_size, burst_assembler):
        buffered = 0.0
        while buffered < (flux_size - PACKET_SIZE):
            # I should remember that a process is only active if it is in its "hold" mode, the "waituntil" mode and others doesn't trigger the active() function.
            if burst_assembler.active():
                yield hold, self, SECONDS_PER_PACKET
                buffered += PACKET_SIZE
                burst_assembler.buffer_data(PACKET_SIZE)
            else:
                burst_assembler.start_buffer()
                yield hold, self
                #TODO: Use the "assembly_period" based code here, because I can assume the assembler will still start after this and it will have to
                #      wait this period before sending the burst, therefore this would speed things up without compromising the simulation.
                #      I just have to check about multiples aggregators.
        if buffered < flux_size:
            yield hold, self, SECONDS_PER_PACKET * ((flux_size - buffered) / (PACKET_SIZE))
            burst_assembler.buffer_data(flux_size - buffered)


class BurstAssembler(Process):
    def __init__(self, simulation, edge_node_id):
        Process.__init__(self, sim=simulation)
        self.edge_node_id = edge_node_id
        self.buffered_data = 0.0
        self.assembly_period = FAP
    
    def run(self, route, route_size):
        next_node = route[1]
        burst_id = self.edge_node_id
        burst_header_offset = PROCESSING_TIME * (route_size-1)
        
        activate = self.sim.activate
        schedule_burst = self.sim.nodes[self.edge_node_id].schedule_local_burst
        
        #TODO: Try to make the assembler be reactivated instead of using an endless loop, for trying to use the hold clause "self.sim.end - self.sim.now()"
        #      without making the simulation exiting with the "Normal exit" end.

        while True:
            self.start_buffering = False
            yield waituntil, self, self.needs_action
                
            yield hold, self, self.assembly_period
            
            if self.buffered_data:
                burst_size = self.buffered_data
                self.buffered_data = 0.0
                burst_header = BurstHeader(self.sim, burst_id, burst_size, burst_header_offset)
                if schedule_burst(next_node, burst_size, burst_header_offset, self.sim.now()):
                    activate(burst_header, burst_header.run(route, route_size))
                else:                
                    self.sim.num_of_burst_drops += 1
    
    def buffer_data(self, data_size):
        self.buffered_data += data_size
    
    def needs_action(self):
        return self.start_buffering
     
    def start_buffer(self):
        self.start_buffering = True