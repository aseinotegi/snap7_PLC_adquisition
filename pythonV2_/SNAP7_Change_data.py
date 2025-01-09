# IMPORT LIBRARY
import snap7
from snap7.util import *
from datetime import datetime
import pika


class PLC_Instance():

    def __init__(self,DB,B_Bools,B_Bytes,B_Int16,B_Int32,B_Float):
        self.DB = DB
        self.B_Bools = B_Bools
        self.B_Bytes = B_Bytes
        self.B_Int16 = B_Int16
        self.B_Int32 = B_Int32
        self.B_Float = B_Float
        self._startBools = 0
        self._startBytes = B_Bools
        self._startInt16 = B_Bools + B_Bytes
        self._startInt32 = B_Bools + B_Bytes + B_Int16
        self._startFloat = B_Bools + B_Bytes + B_Int16 + B_Int32
        self.Lenght = B_Bools + B_Bytes + B_Int16 + B_Int32 + B_Float
        self.AllData = {}
        self.ChangeData = {}
        self.ChangeData_mem = {}
        self.client = snap7.client.Client()

    def Connect (self,IP,rack,slot):
        self.client.connect(IP,rack,slot)

    #GET TIMESTAMP
    def TimeStamp (self):
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return timestamp_str 

    #READ DATA FROM PLC (BYTEARRAY)
    def ReadFromPLC (self):    
        Bytedata = self.client.db_read(self.DB, self._startBools,self.Lenght)
        return Bytedata

    def GetAllDataPLC (self):
        StopBools = self._startBytes
        StopBytes = self._startInt16
        StopInt16 = self._startInt32
        StopInt32 = self._startFloat
        StopFloat = self.Lenght
        self.AllData = {}
        if self.client.get_connected:
            print("Connection to PLC succesfull")
            PLCData = self.ReadFromPLC()
            if self.B_Bools > 0 :
                for _byte in range(self._startBools,StopBools):
                    for _bit in range(8):
                        valor = get_bool(PLCData,_byte,_bit)
                        name = f'Bool_011_o_({_byte})_{_bit}'
                        self.AllData.update({name: valor})
            if self.B_Bytes > 0 :
                for _byte in range(self._startBytes,StopBytes):
                    valor = get_byte(PLCData,_byte)
                    name = f'Byte_011_o_({_byte})'
                    self.AllData.update({name: valor})
            if self.B_Int16 > 0 :
                for _byte in range(self._startInt16,StopInt16,2):
                    valor = get_int(PLCData,_byte)
                    name = f'Int16_011_o_({_byte})'
                    self.AllData.update({name: valor})   
            if self.B_Int32 > 0 :
                for _byte in range(self._startInt32,StopInt32,4):
                    valor = get_dint(PLCData,_byte)
                    name = f'Int32_011_o_({_byte})'
                    self.AllData.update({name: valor})   
            if self.B_Float > 0 :
                for _byte in range(self._startFloat,StopFloat,4):
                    valor = get_real(PLCData,_byte)
                    name = f'Float_011_o_({_byte})'
                    self.AllData.update({name: valor})
            TimeStamp_str = self.TimeStamp()
            self.AllData.update({"TimeStamp": TimeStamp_str})
            self.ChangeData_mem = self.AllData
            #print(AllData)
            return self.AllData 
    async def PublishRabbitMQ(self,PublishData,host,queue):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.basic_publish(exchange='', routing_key=queue, body=str(PublishData))

    async def GetChangeDataPLC (self):
        self.ChangeData = {}
        StopBools = self._startBytes
        StopBytes = self._startInt16
        StopInt16 = self._startInt32
        StopInt32 = self._startFloat
        StopFloat = self.Lenght
        if self.client.get_connected:
            ejecute = False 
            PLCData = self.ReadFromPLC()
            if self.B_Bools > 0 :
                for _byte in range(self._startBools,StopBools):
                    for _bit in range(8):
                        name = f'Bool_011_o_({_byte})_{_bit}'
                        valor = get_bool(PLCData, _byte, _bit)
                        if valor != self.ChangeData_mem[name]:
                            self.ChangeData.update({name: valor})
                            self.ChangeData_mem[name] = self.ChangeData[name]
                            ejecute = True
            if self.B_Bytes > 0 :
                for _byte in range(self._startBytes,StopBytes):
                    valor = get_byte(PLCData,_byte)
                    name = f'Byte_011_o_({_byte})'
                    if valor != self.ChangeData_mem[name]:
                            self.ChangeData.update({name: valor})
                            self.ChangeData_mem[name] = self.ChangeData[name]
                            ejecute = True
            if self.B_Int16 > 0 :
                for _byte in range(self._startInt16,StopInt16,2):
                    valor = get_int(PLCData,_byte)
                    name = f'Int16_011_o_({_byte})'
                    if valor != self.ChangeData_mem[name]:
                            self.ChangeData.update({name: valor})
                            self.ChangeData_mem[name] = self.ChangeData[name]
                            ejecute = True
            if self.B_Int32 > 0 :
                for _byte in range(self._startInt32,StopInt32,4):
                    valor = get_dint(PLCData,_byte)
                    name = f'Int32_011_o_({_byte})'
                    if valor != self.ChangeData_mem[name]:
                            self.ChangeData.update({name: valor})
                            self.ChangeData_mem[name] = self.ChangeData[name]
                            ejecute = True
            if self.B_Float > 0 :
                for _byte in range(self._startFloat,StopFloat,4):
                    valor = get_real(PLCData,_byte)
                    name = f'Float_011_o_({_byte})'
                    if valor != self.ChangeData_mem[name]:
                            self.ChangeData.update({name: valor})
                            self.ChangeData_mem[name] = self.ChangeData[name]
                            ejecute = True
            if ejecute :                
                TimeStamp_str = self.TimeStamp()
                self.ChangeData.update({"TimeStamp": TimeStamp_str})
            if self.ChangeData != {}:
                await self.PublishRabbitMQ(self.ChangeData,'localhost','datos_plc')
            #print(ChangeData)
            return self.ChangeData