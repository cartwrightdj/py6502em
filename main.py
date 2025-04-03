    
from py6502em import *
import sys

cpu = CPU(ver='65C02') 

ram = AddressSpace(0x0000,0x8000-1,name='RAM')
rom = AddressSpace(0x8000,0xFFFF,ro=True,name='ROM')

cpu.symbols = rom._load_from_bf('rom.bin',0x8000)
#cpu.symbols = rom._load_from_bf('./bin/a1basic.bin',0xE000)
print(cpu.symbols)

rom._dump()

cpu.memory.add(ram)
cpu.memory.add(rom)

sys.stdout.write('\x1b[2J')
#cpu.memory._dump()

#ACIA =ACIADevice(0xD010,0xD013,'rw','ACIA')
ACIA =ACIA_Terminal(0xD010,0xD013,'rw','ACIA')
cpu.memory.add(ACIA)

rom.ro = False
#cpu.write(0xFFFC,0x00)
#cpu.write(0xFFFD,0xE0)

cpu.reset()
cpu.timer_on = True
while True:
    cpu.step()
