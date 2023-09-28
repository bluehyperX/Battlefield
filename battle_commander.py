import random
import grpc
import battle_pb2
import battle_pb2_grpc
import logging

# Setting up logging to write to an 'output_log.txt' file
logging.basicConfig(filename='output_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Flag to set when all the soldiers and commanders are dead
flag=0

class Commander:

    # Class-level variables to keep track of alive soldiers and incoming missile details
    alive_soldiers = {}
    missile = []
    stub = None

    def __init__(self, stub,M):

        # Constructor initializes the Soldier service stub and gets the positions of all soldiers
        Commander.stub = stub
        for i in range(M):
            req1 = battle_pb2.Request(id=i)
            positionX = stub.GetPositionX(req1)
            req2= battle_pb2.Request(id=i)
            positionY = stub.GetPositionY(req2)
            Commander.alive_soldiers[i]=[positionX.position,positionY.position]
            
        # Randomly choosing a Commander from the soldiers   
        self.CommanderID = random.choice(list(Commander.alive_soldiers.keys()))
        logging.info("Starting Simulation!")
        logging.info(f"New Commander's ID is {self.CommanderID}\n")

    def missile_approaching(self, pX, pY, N, t, type):
        
        # Display current iteration in the header information
        logging.info("-" * (2*N+3))
        logging.info(f"Current Iteration: {t}".center(2*N+3))
        logging.info("-" * (2*N+3))
        logging.info(f"Alert!! Incoming Missile. Location - ({pX},{pY}), Type - {type}\n")

        # Function to alert soldiers of an incoming missile
        Commander.missile=[pX, pY]
        Missile = battle_pb2.IncomingMissile(pX=pX, pY=pY, type=type)
        Commander.stub.take_shelter(Missile)
        logging.info("Alerting soldiers!\n")

    def status_all(self):

        # Function to get the status of all soldiers after the missile hit
        logging.info(f"Getting status of all alive soldiers - \n")

        for i in list(Commander.alive_soldiers.keys()):
            req = battle_pb2.Request(id=i)
            DeadStatus = Commander.stub.was_hit(req)
            if DeadStatus.status is True:
                logging.info(f"Soldier {i} got Hit!")
                Commander.alive_soldiers.pop(i)
            else:
                req1 = battle_pb2.Request(id=i)
                positionX = Commander.stub.GetPositionX(req1)
                req2= battle_pb2.Request(id=i)
                positionY = Commander.stub.GetPositionY(req2)

                # Checking if soldiers moved or stayed in the same position
                if (Commander.alive_soldiers[i][0]==positionX.position and Commander.alive_soldiers[i][1]==positionY.position):
                    logging.info(f"Soldier {i} is still at ({Commander.alive_soldiers[i][0]},{Commander.alive_soldiers[i][1]})")
                else:
                    logging.info(f"Soldier {i} has moved from ({Commander.alive_soldiers[i][0]},{Commander.alive_soldiers[i][1]}) to ({positionX.position},{positionY.position})")
                    Commander.alive_soldiers[i]=[positionX.position,positionY.position]

        # Checking if commander is dead
        if self.CommanderID not in Commander.alive_soldiers.keys():
            logging.info("Commander is dead!\n")
            
            # Setting new commander by setting commander ID to any random soldier ID else setting ID to -1
            self.CommanderID=random.choice(list(Commander.alive_soldiers.keys())) if len(list(Commander.alive_soldiers.keys()))!=0 else -1  
            
            # If cannot set commander as everyone is dead then set the flag 
            if self.CommanderID==-1:
                flag=1
                logging.info(f"Everyone is Dead!\n")
            logging.info(f"New Commander's ID is {self.CommanderID}\n")   

    def printLayout(self, N, M):

        # Function to print the current battlefield layout with soldiers' positions
        CELL_WIDTH = 4
        RED_START = "\033[91m"
        COLOR_END = "\033[0m"
        matrix = [[' ' * CELL_WIDTH for _ in range(N)] for _ in range(N)]
        
        for key, value in Commander.alive_soldiers.items():
            x, y = value
            matrix[y][x] = str(key).center(CELL_WIDTH)
        
        # Store 'X' without color codes in the matrix
        matrix[Commander.missile[1]][Commander.missile[0]] = 'X'.center(CELL_WIDTH)

        
          # Print column numbers
        header = ' ' * (CELL_WIDTH + 1)  # extra space for row numbers
        for i in range(N):
            header += str(i).center(CELL_WIDTH)
        logging.info(header)

        # Print the matrix
        logging.info(" " + " " * CELL_WIDTH + "+" + "-" * (CELL_WIDTH * N) + "+")
        for idx, row in enumerate(reversed(matrix)):
            rowNum = str(N - idx - 1).rjust(CELL_WIDTH)
            leftrowNum = str(N - idx - 1).ljust(CELL_WIDTH)
            row_string = rowNum + "|"
            for cell in row:
                row_string += cell
            row_string += "|" + leftrowNum  # append row number to the end
            logging.info(row_string)
        logging.info(" " + " " * CELL_WIDTH + "+" + "-" * (CELL_WIDTH * N) + "+")
        
        # Print column numbers
        header = ' ' * (CELL_WIDTH + 1)  # extra space for row numbers
        for i in range(N):
            header += str(i).center(CELL_WIDTH)
        logging.info(header)

        alive = len(Commander.alive_soldiers.keys())
        dead = M - alive

        # Printing Total, Alive and Dead soldier counts
        logging.info(f"Total Number of Soldiers: {M}")
        logging.info(f"Alive Soldiers: {alive}")
        logging.info(f"Dead Soldiers: {dead}")
        logging.info("-" * (CELL_WIDTH * N)+"\n")

def run():

    # Main function to simulate the battlefield
    # with grpc.insecure_channel("localhost:50051") as channel:       #For running on local machines, uncomment this line
    with grpc.insecure_channel("172.17.49.241:50051") as channel:       #For running on different machines, uncomment this line and update the IP address with the current ID address of the server
        stub = battle_pb2_grpc.SoldierStub(channel)

        #Taking inputs from user
        N = int(input("Enter the size of Battlefield - "))
        M = int(input("Enter the number of Soldiers - "))
        t = int(input("Enter the missile launch interval - "))
        T = int(input("Enter the simulation time - "))

        # Sending number of soldier to server
        req = battle_pb2.Request(id=M)
        stub.SetSoldierNum(req)

        # Sending battlefield size to server
        req = battle_pb2.Request(id=N)
        stub.SetBattleFieldSize(req)
    
        # Creating a commander instance
        commander = Commander(stub,M)

        # Starting simulation and sending missile at every t turns 
        for i in range(T):
            if i%t==0:
                commander.missile_approaching(random.randint(0,N-1), random.randint(0,N-1), N, int(i/t), random.randint(1,4))
                commander.status_all()
                if flag==1:
                    logging.info(f"Game Over. Lost!")
                    logging.info("_____________________________________________________________________________________________\n")
                    return
                commander.printLayout(N,M)

        logging.info("Won!") if len(Commander.alive_soldiers) > 0.5*M else logging.info("Lost!")
        logging.info("_____________________________________________________________________________________________\n")

if __name__ == "__main__":
    run()