from SimPy.Simulation import Process, hold

from config import PROCESSING_TIME, CIRCUIT_EXPIRATION_SECONDS

class CircuitControlPacket(Process):
    def __init__(self, sender, simulation, circuit_id, flux_size, control_packet_offset):
        Process.__init__(self, sim=simulation)
        self.id = circuit_id
        self.sender = sender
        self.total_propagation_time = 0
        self.circuit_expiration = self.sim.now() + CIRCUIT_EXPIRATION_SECONDS
        self.offset = control_packet_offset
        self.dropped = False
    
    def run(self, route, route_size):
        '''The propagation and processing delay are simulated in one hold only, reducing simulation time.
           To make that possible, the instant of the flux arrival is calculated after the simulation of the processing time,
           and so the processing time should be subtracted before calculating the flux arrival time'''
        
        now = self.sim.now
        
        for current_route_node in xrange(route_size-2):
            propagation = self.sim.topology[route[current_route_node]][route[current_route_node+1]]['delay']
            self.total_propagation_time += propagation
            yield hold, self, propagation + PROCESSING_TIME
            new_current_route_node = current_route_node + 1
            self.next_route_node = route[new_current_route_node+1]
            self.offset -= PROCESSING_TIME # propagation time doesn't count because the burst also propagates, but it isn't processed
            self.data_arrival = now() + self.offset
            if not self.sim.nodes[route[new_current_route_node]].schedule_circuit(self): 
                while new_current_route_node >= 1: # clean circuit from the last scheduled node (first current_node) to the first node
                    self.sim.nodes[route[new_current_route_node-1]].clean_circuit(now(), route[new_current_route_node], self.circuit_expiration)
                    new_current_route_node -= 1
                self.dropped = True
                self.interrupt(self.sender)
                yield hold, self
                break
        else:
            propagation = self.sim.topology[route[route_size-2]][route[route_size-1]]['delay']
            self.total_propagation_time += propagation
            yield hold, self, propagation + PROCESSING_TIME
            
            yield hold, self, self.total_propagation_time # this is to simulate the sending of a successful agreement notice packet
            self.interrupt(self.sender)
            
            yield hold, self, self.circuit_expiration - now()
            if not self.interrupted():
                self.interrupt(self.sender)
            
            #TODO: I think that all routers in the route from source to destiny should be updated to have a circuit to destiny.
            #      And at every node, the control packet should be able to access if a circuit already exists to the destination
            #      from that intermediate node.

    def has_dropped(self):
        return self.dropped


class BurstHeader(Process):
    def __init__(self, simulation, burst_id, burst_size, burst_header_offset):
        Process.__init__(self, sim=simulation)
        self.id = burst_id
        self.burst_size = burst_size
        self.offset = burst_header_offset

    def run(self, route, route_size):
        '''The propagation and processing delay are simulated in one hold only, reducing simulation time.
           To make that possible, the instant of the burst arrival is calculated after the simulation of the processing time,
           and so the processing time should be subtracted before calculating the burst arrival time'''
        for current_route_node in xrange(route_size-2):
            propagation = self.sim.topology[route[current_route_node]][route[current_route_node+1]]['delay']
            yield hold, self, propagation + PROCESSING_TIME
            self.next_route_node = route[current_route_node+2]
            self.offset -= PROCESSING_TIME # propagation time doesn't count because the burst also propagates, but it isn't processed
            self.burst_arrival = self.sim.now() + self.offset # offset units of time after control packet arrives and is processed
            if not self.sim.nodes[route[current_route_node+1]].schedule_burst(self, self.sim.now()):
                self.sim.num_of_burst_drops += 1
                break
        else:
            propagation = self.sim.topology[route[route_size-2]][route[route_size-1]]['delay']
            yield hold, self, propagation + PROCESSING_TIME
            self.sim.num_of_burst_deliveries += 1
