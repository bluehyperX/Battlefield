import random
from time import sleep
import grpc
import battle_pb2
import battle_pb2_grpc

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
        print(f"\nStarting Simulation! \n\nNew Commander's ID is {self.CommanderID}")

    def missile_approaching(self, pX, pY, N, t, type):
            
            # Display current iteration in the header information
            print("\n" + "-" * (2*N+3))
            print(f"Current Iteration: {t}".center(2*N+3))
            print("-" * (2*N+3))
            print(f"\nAlert!! Incoming Missile - \nLocation - ({pX},{pY}) \nType - {type}")

            # Function to alert soldiers of an incoming missile
            Commander.missile=[pX, pY]
            Missile = battle_pb2.IncomingMissile(pX=pX, pY=pY, type=type)
            Commander.stub.take_shelter(Missile)
            print("\nAlerting soldiers!")

    def status_all(self):

        # Function to get the status of all soldiers after the missile hit
        print(f"\nGetting status of all alive soldiers - \n")

        for i in list(Commander.alive_soldiers.keys()):
            req = battle_pb2.Request(id=i)
            DeadStatus = Commander.stub.was_hit(req)
            if DeadStatus.status is True:
                print(f"Soldier {i} got Hit!")
                Commander.alive_soldiers.pop(i)
            else:
                req1 = battle_pb2.Request(id=i)
                positionX = Commander.stub.GetPositionX(req1)
                req2= battle_pb2.Request(id=i)
                positionY = Commander.stub.GetPositionY(req2)

                # Checking if soldiers moved or stayed in the same position
                if (Commander.alive_soldiers[i][0]==positionX.position and Commander.alive_soldiers[i][1]==positionY.position):
                    print(f"Soldier {i} is still at ({Commander.alive_soldiers[i][0]},{Commander.alive_soldiers[i][1]})")
                else:
                    print(f"Soldier {i} has moved from ({Commander.alive_soldiers[i][0]},{Commander.alive_soldiers[i][1]}) to ({positionX.position},{positionY.position})")
                    Commander.alive_soldiers[i]=[positionX.position,positionY.position]

        # Checking if commander is dead
        if self.CommanderID not in Commander.alive_soldiers.keys():
            print("Commander is dead!")

            # Setting new commander by setting commander ID to any random soldier ID else setting ID to -1
            self.CommanderID=random.choice(list(Commander.alive_soldiers.keys())) if len(list(Commander.alive_soldiers.keys()))!=0 else -1  
            
            # If cannot set commander as everyone is dead then set the flag 
            if self.CommanderID==-1:
                flag=1
                print(f"Everyone is Dead!")
            print(f"\nNew Commander's ID is {self.CommanderID}")   

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

        print("\n")
          # Print column numbers
        header = ' ' * (CELL_WIDTH + 1)  # extra space for row numbers
        for i in range(N):
            header += str(i).center(CELL_WIDTH)
        print(header)

        print(" " + " " * CELL_WIDTH + "+" + "-" * (CELL_WIDTH * N) + "+")

         # Print the matrix with row numbers on both sides
        for idx, row in enumerate(reversed(matrix)):
            rowNum = str(N - idx - 1).rjust(CELL_WIDTH)
            leftrowNum = str(N - idx - 1).ljust(CELL_WIDTH)
            row_string = rowNum + "|"
            for cell in row:
                if cell.strip() == 'X':
                    # Colorize 'X' just before printing
                    row_string += RED_START + cell + COLOR_END
                else:
                    row_string += cell
            row_string += "|" + leftrowNum  # append row number to the end
            print(row_string)
        
        print(" " + " " * CELL_WIDTH + "+" + "-" * (CELL_WIDTH * N) + "+")
          # Print column numbers
        header = ' ' * (CELL_WIDTH + 1)  # extra space for row numbers
        for i in range(N):
            header += str(i).center(CELL_WIDTH)
        print(header)


        alive = len(Commander.alive_soldiers.keys())
        dead = M - alive

        print(f"\nTotal Number of Soldiers: {M}")
        print(f"Alive Soldiers: {alive}")
        print(f"Dead Soldiers: {dead}")
        print("-" * (CELL_WIDTH * N + CELL_WIDTH + 2))  # extended the line length to match the matrix width

def run():

    # Main function to simulate the battlefield
    with grpc.insecure_channel("localhost:50051") as channel:       #For running on local machines, uncomment this line
    # with grpc.insecure_channel("172.17.49.241:50051") as channel:       #For running on different machines, uncomment this line and update the IP address with the current ID address of the server
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
                    print(f"Game Over. Lost!")
                    return
                
                commander.printLayout(N,M)
                

        print("Won!") if len(Commander.alive_soldiers) > 0.5*M else print("Lost!")
        
if __name__ == "__main__":
    run()