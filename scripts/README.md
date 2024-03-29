### New options in Cooja to generate data traces

Multi-Trace Cooja has a new option to generate data traces when running simulations, and this option is found in the
`Settings` menu. The data traces will be saved together with the simulation, and each simulation run will generate a
new data trace.

The Cooja Simulation scripts have a new API to access and provide information to the data traces. Example script
logging an event to the data traces when the simulation network reached a steady state.

```
sim.getEventCentral().logEvent("network", "steady-state");
```

### Scripts to parse and generate Cooja simulation files,

Example generating a new simulation with randomized topology that is spread around
a sink node:
```
./generate-topology.py -i ../../../applications/blackhole-attack/simulations/rpl-udp-base-15-attack-blackhole-random.csc -o ../../../applications/blackhole-attack/generated/test.csc --topology spread
```

Example generating a new simulation with randomized topology that is
somewhat biased for more multihop:
```
./generate-topology.py -i ../../../applications/blackhole-attack/simulations/rpl-udp-base-15-attack-blackhole-random.csc -o ../../../applications/blackhole-attack/generated/test.csc
```

Example generating 20 new simulations with randomized topology with extra
constraint that nodes should be at least 40 meters from each other.
```
./generate-topology.py -c 20 -i ../../../applications/blackhole-attack/simulations/rpl-udp-base-15-attack-blackhole-random.csc -o ../../../applications/blackhole-attack/generated/test.csc --min-distance 40
```

Example generating simulations with different random seed policy
```
./generate-topology.py -c 20 -i ../../../applications/blackhole-attack/simulations/rpl-udp-base-15-attack-blackhole-random.csc -o ../../../applications/blackhole-attack/generated/test.csc --seed f
```

Example generating simulations of fixed topology while different transmission/receive ratios
```
./generate-topology.py -i ../../../applications/blackhole-attack/simulations/rpl-udp-base-15-attack-blackhole-random.csc -o ../../../applications/blackhole-attack/generated/test.csc --tx-ratio 0.9 --rx-ratio 0.85 0.95
```

### Scripts to batch run Cooja without GUI

Example running Cooja on all simulations in a folder to generate data traces. The simulations must contain a control
script that ensures the simulation finishes after some time and does not run forever. Otherwise, Cooja will refuse to
run the simulation.

```
./run-cooja.py ../../../applications/blackhole-attack/generated/*.csc
```

### Python library to parse Cooja data traces

Example reading a data trace and show a summary.

```
./coojatrace.py -s ../../../applications/blackhole-attack/generated/test-*-dt-*
```

Example script extracting some RPL statistics from a data trace. The features will be saved as a CSV file inside
the data trace folder.

```
./extract-rpl-features-blackhole.py ../../../applications/blackhole-attack/generated/test-00001-dt-*
```
