This is a Python assignment for simulating a battlefield using gRPC.

#### Team Members:
1. Sparsh Kumar
2. Shubham Shrivastav

#### Files:
1. battle_commander.py - Contains the logic for the battlefield commander.
2. battle_soldier.py - Contains the logic for each soldier in the battlefield.

#### Installation Instructions:
1. Ensure you have Python3.x installed on two machines.
2. Install the required dependencies on both the machines using: pip install -r requirements.txt

#### Running Instructions:
1. Start the gRPC server by executing: python battle_soldier.py on one machine.
2. Start the battlefield simulation by executing: python battle_commander.py on another machine

This simulation will continue for the time you've specified and you can view the output in the output_log.txt file.

#### Notes:

1. Ensure the gRPC server (from battle_soldier.py) is running before you execute the battle_commander.py to see the battlefield simulation.
2. Before starting another simulation, restart the existing gRPC server.