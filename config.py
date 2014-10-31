'''All data in bits and seconds'''
'''Where applicable, the symbol for the kibibyte (KiB) is used to denote 1024 bytes'''


# Router configuration
# This value is obtained from Qiao et al. (1999), using the MINIMUM_BURST_LENGTH and LINK_WAVELENGTH_CAPACITY to find "L",
# and using "L" and the ratio "c" from the paper to find lambda (the processing speed).
PROCESSING_TIME = 5.24288e-06 # (0.00000524288) seconds OR 5.24288 microseconds
# This is the value used in Ethernet networks
MAXIMUM_TRANSMISSION_UNIT = 12000.0 # bits OR 1500 B (CASTRO, 2011)


# Physical medium configuration
# The next two variable values were taken from Melo et al. (2013)
NUMBER_OF_WAVELENGTHS = 32 # Put only even numbers here, because of the 50% rate of channels to each switching technique
LINK_WAVELENGTH_CAPACITY = 1000000000.0 # 1 Gigabit (1e+9 bits)
REFRACTION_INDEX = 1.5
LIGHT_SPEED = 299792.458 # kilometers per second OR 299792458 m/s


# Data configuration
# This is the average size of packets in the byte range 1426-1492, which were the most frequent packet range (more than 50% of the time, according to Castro (2011))
AVERAGE_PACKET_SIZE = 1459.0 * 8 # bits OR 1459 B OR 11672 bits
## Burst configuration
# The minimum burst length is chosen based on the size of the largest IP packet possible, 65536 B (ABID et al., 2007)
MINIMUM_BURST_LENGTH = 64.0 * 1024 * 8 # bits OR 524288 B OR 64 KiB
FIXED_ASSEMBLY_PERIOD = 0.02 # seconds(CAO et al., 2002)
## Circuit configuration
# This could be something like infinity, but is set as 2 hours to make it more feasible
CIRCUIT_EXPIRATION_SECONDS = 2.0 * 60 * 60 # seconds or 2 hours OR 120 minutes OR 7200 seconds


# Simulation configuration

'''CODE'''
TOPOLOGY = "nfsnet.gml" # (CAO et al., 2002)

'''TEST'''
# TOPOLOGY = "burst_drop_testnet.gml"

#TODO: Finish reading Abid et al. (2007) to see if the author mentions something about arrival rates
# This variable value was taken from Melo et al. (2013)
MEAN_FLUX_ARRIVAL_INTERVAL = 0.000222 # seconds
#TODO: The simulation could accept a distribution function that returns a value as a rate between some limit
#      or accept a mean interval and a distribution function
# Obtained as the mean of a pareto distributed interarrival time between packets from Avallone (2004).
MEAN_INTERVAL_OF_PACKET_ARRIVAL = 0.015 # seconds
# Both packet counts, 100 and 800, obtained from CAO et al. (2002). 
MINIMUM_FLUX_SIZE = 100 * AVERAGE_PACKET_SIZE # 1167200 bits OR 145900 B OR 142,48046875 KiB
MAXIMUM_FLUX_SIZE = 800 * AVERAGE_PACKET_SIZE # 9337600 bits OR 1167200 B OR 1139,84375 KiB OR 1,113128662109375 MiB
#TODO: Obtain the mean flux size from: sum([random.Random().uniform(MINIMUM_FLUX_SIZE, MAXIMUM_FLUX_SIZE) for _ in xrange(1000000)]) / 1000000
NUMBER_OF_REPETITIONS = 1#5

'''LEGACY'''
#UNTIL = 3600.000 # seconds CURRENTLY NOT IN USE

NUMBER_OF_FLUX_ARRIVALS = 100#0000


# Energy consumption configuration (ALEKSIC et al., 2012)
#TODO: Can I assume that the measure of Watts means Watts per hour?
OPTICAL_ROUTER_CONSUMPTION = {
                # W PER NODE
                "MANAGEMENT_CARD" : 300.0,
                "SWITCH_CONTROL_UNIT" : 300.0,
                # SWITCHES
                # The fast switch consumption is dependent on the number of fibers coming and going from its router
                "SLOW_SWITCH" : 0.1, # W per active port (always active)
                # W PER ACTIVE FIBER
                "OPTICAL_AMPLIFIER" : 14.0, # coming and going fiber (2 stages per node)
                #"AHOS_CONTROL_PLANE" : 560.0, # W per fiber NOT BEING USED
                # W PER ACTIVE PORT/CHANNEL
                "WAVELENGTH_CONVERTER" : 1.69, # W per port
                "CIE/R" : 17.0, # W per port
                "TRANSCEIVER" : 1.25 # W per channel
                }
# Transforming the values from W/h to W/s
''' This is done because the simulation length is variable, and given in seconds, so it's easier to deal with the calculations if the values are given in W per second'''
for key in OPTICAL_ROUTER_CONSUMPTION:
    OPTICAL_ROUTER_CONSUMPTION[key] /= 3600.0