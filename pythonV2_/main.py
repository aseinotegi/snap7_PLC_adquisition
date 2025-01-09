from SNAP7_Change_data import *
import asyncio

PLC1 = PLC_Instance(1000,400,20,596,396,0)
PLC1.Connect('121.11.244.12', 0, 1)

async def main ():

    FirstTime = False            
    while True:
        if not FirstTime:
            PLC1.GetAllDataPLC()
            FirstTime = True
        else:
            await PLC1.GetChangeDataPLC()

if __name__== '__main__':
    asyncio.run(main())

