import random
from time import sleep
import grpc
import battle_pb2
import battle_pb2_grpc
import sys

flag=0

class Commander:
    alive_soldiers = {}
    missile = []
    stub = None
    def __init__(self, stub,M):
        Commander.stub = stub
        for i in range(M):
            req1 = battle_pb2.Request(id=i)
            positionX = stub.GetPositionX(req1)
            req2= battle_pb2.Request(id=i)
            positionY = stub.GetPositionY(req2)
            Commander.alive_soldiers[i]=[positionX.position,positionY.position]
            # print(Commander.alive_soldiers) 
        self.CommanderID = random.choice(list(Commander.alive_soldiers.keys()))
        print(f"\nStarting Simulation! \n\nNew Commander's ID is {self.CommanderID}")

    def missile_approaching(self, pX, pY, N, t, type):
            Commander.missile=[pX, pY]
            # Display header information
            print("\n" + "-" * (2*N+3))
            print(f"Current Iteration: {t}".center(2*N+3))
            print("-" * (2*N+3))
            print(f"\nAlert!! Incoming Missile - \nLocation - ({pX},{pY}) \nType - {type}")
            Missile = battle_pb2.IncomingMissile(pX=pX, pY=pY, type=type)
            Commander.stub.take_shelter(Missile)
            print("\nAlerting soldiers!")

    def status_all(self):
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
                if (Commander.alive_soldiers[i][0]==positionX.position and Commander.alive_soldiers[i][1]==positionY.position):
                    print(f"Soldier {i} is still at ({Commander.alive_soldiers[i][0]},{Commander.alive_soldiers[i][1]})")
                else:
                    print(f"Soldier {i} has moved from ({Commander.alive_soldiers[i][0]},{Commander.alive_soldiers[i][1]}) to ({positionX.position},{positionY.position})")
                    Commander.alive_soldiers[i]=[positionX.position,positionY.position]
        if self.CommanderID not in Commander.alive_soldiers.keys():
            print("Commander is dead!")
            self.CommanderID=random.choice(list(Commander.alive_soldiers.keys())) if len(list(Commander.alive_soldiers.keys()))!=0 else -1  
            if self.CommanderID==-1:
                flag=1
                print(f"Everyone is Dead!")
            print(f"\nNew Commander's ID is {self.CommanderID}")   

    # def printLayout(self, N, M):
    #     CELL_WIDTH = 4
    #     RED_START = "\033[91m"
    #     COLOR_END = "\033[0m"
    #     matrix = [[' ' * CELL_WIDTH for _ in range(N)] for _ in range(N)]
        
    #     for key, value in Commander.alive_soldiers.items():
    #         x, y = value
    #         matrix[y][x] = str(key).center(CELL_WIDTH)
        
    #     # Store 'X' without color codes in the matrix
    #     matrix[Commander.missile[1]][Commander.missile[0]] = 'X'.center(CELL_WIDTH)

    #     # Print the matrix
    #     print("+" + "-" * (CELL_WIDTH * N) + "+")
    #     for row in reversed(matrix):
    #         row_string = "|"
    #         for cell in row:
    #             if cell.strip() == 'X':
    #                 # Colorize 'X' just before printing
    #                 row_string += RED_START + cell + COLOR_END
    #             else:
    #                 row_string += cell
    #         print(row_string + "|")
    #     print("+" + "-" * (CELL_WIDTH * N) + "+")

    #     alive = len(Commander.alive_soldiers.keys())
    #     dead = M - alive

    #     print(f"\nTotal Number of Soldiers: {M}")
    #     print(f"Alive Soldiers: {alive}")
    #     print(f"Dead Soldiers: {dead}")
    #     print("-" * (CELL_WIDTH * N))

    def printLayout(self, N, M):
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
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = battle_pb2_grpc.SoldierStub(channel)
        N = int(input("Enter the size of Battlefield - "))
        M = int(input("Enter the number of Soldiers - "))
        t = int(input("Enter the missile launch interval - "))
        T = int(input("Enter the simulation time - "))

        req = battle_pb2.Request(id=M)
        stub.SetSoldierNum(req)

        req = battle_pb2.Request(id=N)
        stub.SetBattleFieldSize(req)
    
        commander = Commander(stub,M)

        for i in range(T):
            if i%t==0:
                commander.missile_approaching(random.randint(0,N-1), random.randint(0,N-1), N, int(i/t), random.randint(1,4))
                sleep(3)
                commander.status_all()
                if flag==1:
                    print(f"Game Over. Lost!")
                    return
                sleep(3)
                commander.printLayout(N,M)
                sleep(3)

        print("Won!") if len(Commander.alive_soldiers) > 0.5*M else print("Lost!")
        
if __name__ == "__main__":
    run()