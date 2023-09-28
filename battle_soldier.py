from concurrent import futures
import random
import battle_pb2_grpc
import battle_pb2
import grpc
from google.protobuf import empty_pb2

class Soldier(battle_pb2_grpc.SoldierServicer):
    id = 0
    all = []
    N = 0
    M = 0

    def __init__(self):
        self.soldierID=Soldier.id
        Soldier.id=Soldier.id+1
        self.positionX=0
        self.positionY=0
        self.speed=random.randint(0,4)
        self.isAlive=True
        Soldier.all.append(self)

    def SetBattleFieldSize(self, request, context):
        print(f"Received Battlefield size - {request.id}")
        Soldier.N = request.id
        for soldier in Soldier.all:
            soldier.positionX=random.randint(0,Soldier.N-1)
            soldier.positionY=random.randint(0,Soldier.N-1)
            print(f"Created a new soldier id - {soldier.soldierID} with position {soldier.positionX},{soldier.positionY} and with speed {soldier.speed}.")
        print(f"Total number of soldiers is {len(Soldier.all)}")
        return empty_pb2.Empty()

    def SetSoldierNum(self, request, context):
        print(f"Received Soldier Number - {request.id}")
        Soldier.M = request.id
        for i in range(Soldier.M-1):
            Soldier()
        return empty_pb2.Empty()

    def take_shelter(self, request, context):
        missile_minX = 0 if request.pX-request.type<0 else request.pX-request.type
        missile_minY = 0 if request.pY-request.type<0 else request.pY-request.type
        missile_maxX = Soldier.N-1 if request.pX+request.type>Soldier.N-1 else request.pX+request.type
        missile_maxY = Soldier.N-1 if request.pY+request.type>Soldier.N-1 else request.pY+request.type
        top_left = [missile_minX, missile_minY]
        bottom_right = [missile_maxX, missile_maxY]
        for soldier in Soldier.all:
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
            
            safe_moves = {move for move in moves if move[0] < top_left[0] or move[0] > bottom_right[0] or move[1] < top_left[1] or move[1] > bottom_right[1]}

            # print(safe_moves)

            if len(safe_moves)==0:
                soldier.isAlive = False
            elif (soldier.positionX, soldier.positionY) in safe_moves:
                continue
            else:
                A = random.choice(list(safe_moves))
                soldier.positionX=A[0]
                soldier.positionY=A[1]
        return empty_pb2.Empty()

    def was_hit(self, request, context):
        soldier = Soldier.getSoldier(request.id)
        reply = battle_pb2.StatusReply()
        if soldier is not None:
            if soldier.isAlive == True:
                reply.status=False
                return reply
            else:
                Soldier.all.remove(soldier)
                del soldier
                reply.status=True
                return reply
        reply.status=False
        return reply
  
    def GetPositionX(self, request, context):
        soldier = Soldier.getSoldier(request.id)
        reply = battle_pb2.PositionReply()
        if soldier is not None:
            reply.position=soldier.positionX
            return reply
        reply.position=-1
        return reply

    def GetPositionY(self, request, context):
        soldier = Soldier.getSoldier(request.id)
        reply = battle_pb2.PositionReply()
        if soldier is not None:
            reply.position=soldier.positionY
            return reply
        reply.position=-1
        return reply

    def getSoldier(id):
        for soldier in Soldier.all:
            if soldier.soldierID==id:
                return soldier
            else:
                None

    def __repr__(self) -> str:
        if self.isAlive == True:
            return f"Soldier {self.soldierID} is Alive and his position is {self.positionX}, {self.positionY}"
        else:
            return f"Soldier {self.soldierID} is Dead and his last position was {self.positionX}, {self.positionY}"

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    battle_pb2_grpc.add_SoldierServicer_to_server(Soldier(), server)
    server.add_insecure_port("localhost:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
