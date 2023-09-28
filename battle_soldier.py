# Importing necessary libraries and modules
from concurrent import futures
import random
import battle_pb2_grpc
import battle_pb2
import grpc
from google.protobuf import empty_pb2

class Soldier(battle_pb2_grpc.SoldierServicer):
    
    # Class attributes to keep track of global soldier details
    id = 0      # Unique ID for each soldier
    all = []    # List to store all soldier instances
    N = 0       # Battlefield width/height
    M = 0       # Number of soldiers

    # Initializing soldier properties
    def __init__(self):
        
        # Initialize soldier with unique ID and default position
        self.soldierID=Soldier.id
        Soldier.id=Soldier.id+1
        self.positionX=0
        self.positionY=0
        self.speed=random.randint(0,4)
        self.isAlive=True
        Soldier.all.append(self)  # Add soldier instance to the global list

    def SetBattleFieldSize(self, request, context):

        # Set the size of the battlefield and initialize positions for all soldiers
        print(f"Received Battlefield size - {request.id}")
        Soldier.N = request.id
        for soldier in Soldier.all:
            soldier.positionX=random.randint(0,Soldier.N-1)
            soldier.positionY=random.randint(0,Soldier.N-1)
            print(f"Created a new soldier id - {soldier.soldierID} with position {soldier.positionX},{soldier.positionY} and with speed {soldier.speed}.")
        print(f"Total number of soldiers is {len(Soldier.all)}")
        return empty_pb2.Empty()

    def SetSoldierNum(self, request, context):

        # Set the number of soldiers and create instances accordingly
        print(f"Received Soldier Number - {request.id}")
        Soldier.M = request.id
        for i in range(Soldier.M-1):
            Soldier()
        return empty_pb2.Empty()

    def take_shelter(self, request, context):

        # Determine the blast zone of a missile and move soldiers to safety
        # Get the boundaries of the blast zone
        missile_minX = 0 if request.pX-request.type<0 else request.pX-request.type
        missile_minY = 0 if request.pY-request.type<0 else request.pY-request.type
        missile_maxX = Soldier.N-1 if request.pX+request.type>Soldier.N-1 else request.pX+request.type
        missile_maxY = Soldier.N-1 if request.pY+request.type>Soldier.N-1 else request.pY+request.type
        top_left = [missile_minX, missile_minY]
        bottom_right = [missile_maxX, missile_maxY]

        # Loop through each soldier and find safe moves outside the blast zone
        for soldier in Soldier.all:
            
            # Possible moves the soldier can make based on its speed
            # Includes current position and 8 directions
            moves = [
                    (soldier.positionX, soldier.positionY), # Current
                    (soldier.positionX, Soldier.N-1 if soldier.positionY + soldier.speed>Soldier.N-1 else soldier.positionY + soldier.speed),       # Up
                    (Soldier.N-1 if soldier.positionX + soldier.speed>Soldier.N-1 else soldier.positionX + soldier.speed, soldier.positionY),       # Right
                    (soldier.positionX, 0 if soldier.positionY - soldier.speed<0 else soldier.positionY - soldier.speed),       # Down
                    (0 if soldier.positionX - soldier.speed<0 else soldier.positionX - soldier.speed, soldier.positionY),       # Left
                    (Soldier.N-1 if soldier.positionX + soldier.speed>Soldier.N-1 else soldier.positionX + soldier.speed, Soldier.N-1 if soldier.positionY + soldier.speed>Soldier.N-1 else soldier.positionY + soldier.speed), # Up-Right
                    (0 if soldier.positionX - soldier.speed<0 else soldier.positionX - soldier.speed, 0 if soldier.positionY - soldier.speed<0 else soldier.positionY - soldier.speed), # Down-Left
                    (Soldier.N-1 if soldier.positionX + soldier.speed>Soldier.N-1 else soldier.positionX + soldier.speed, 0 if soldier.positionY - soldier.speed<0 else soldier.positionY - soldier.speed), # Down-Right
                    (0 if soldier.positionX - soldier.speed<0 else soldier.positionX - soldier.speed, Soldier.N-1 if soldier.positionY + soldier.speed>Soldier.N-1 else soldier.positionY + soldier.speed)  # Up-Left
                    ] 
            
            # Filter out the moves which are out of blast zon
            safe_moves = {move for move in moves if move[0] < top_left[0] or move[0] > bottom_right[0] or move[1] < top_left[1] or move[1] > bottom_right[1]}

            # If no safe moves are found, mark the soldier as dead
            if len(safe_moves)==0:      
                soldier.isAlive = False

            # If current position is safe, no need to move            
            elif (soldier.positionX, soldier.positionY) in safe_moves:
                continue

            # Otherwise, randomly choose a safe move
            else:
                A = random.choice(list(safe_moves))
                soldier.positionX=A[0]
                soldier.positionY=A[1]
        return empty_pb2.Empty()

    def was_hit(self, request, context):

        # Check if a soldier was hit by the missile
        soldier = Soldier.getSoldier(request.id)
        reply = battle_pb2.StatusReply()
        if soldier is not None:
            if soldier.isAlive == True: 
                
                # If the soldier is alive then return was_hit as false
                reply.status=False
                return reply
            else:                       
                
                # Otherwise remove the soldier from the array, delete the soldier instance and return true
                Soldier.all.remove(soldier)
                del soldier
                reply.status=True
                return reply
        reply.status=False
        return reply
  
    def GetPositionX(self, request, context):

        # Get X position of a soldier
        soldier = Soldier.getSoldier(request.id)
        reply = battle_pb2.PositionReply()
        if soldier is not None:
            reply.position=soldier.positionX
            return reply
        reply.position=-1
        return reply

    def GetPositionY(self, request, context):

        # Get Y position of a soldier
        soldier = Soldier.getSoldier(request.id)
        reply = battle_pb2.PositionReply()
        if soldier is not None:
            reply.position=soldier.positionY
            return reply
        reply.position=-1
        return reply

    @staticmethod
    def getSoldier(id):

        # Fetch soldier instance by ID     
        for soldier in Soldier.all:
            if soldier.soldierID==id:
                return soldier
            else:
                None

    def __repr__(self) -> str:

        # String representation of soldier object
        if self.isAlive == True:
            return f"Soldier {self.soldierID} is Alive and his position is {self.positionX}, {self.positionY}"
        else:
            return f"Soldier {self.soldierID} is Dead and his last position was {self.positionX}, {self.positionY}"

def serve():

    # Start the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    battle_pb2_grpc.add_SoldierServicer_to_server(Soldier(), server)
    # server.add_insecure_port("localhost:50051")     #For running on local machines, uncomment this line
    server.add_insecure_port("172.17.49.241:50051")     #For running on different machines, uncomment this line and update the IP address with the current ID address of the server
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":

    # Run the gRPC server when script is executed
    serve()
