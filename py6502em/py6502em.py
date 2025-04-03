import uuid
import socket
import threading
import time
import os
import re
import sys


SLEEP = 0.0

class Ansi:
    """
    A collection of ANSI escape sequences for text formatting and color.
    """

    # Reset all attributes (color, style)
    RESET = "\033[0m"

    # Text styles
    BOLD       = "\033[1m"
    FAINT      = "\033[2m"
    ITALIC     = "\033[3m"
    UNDERLINE  = "\033[4m"
    BLINK_SLOW = "\033[5m"
    BLINK_RAPID= "\033[6m"
    REVERSE    = "\033[7m"
    HIDDEN     = "\033[8m"
    STRIKE     = "\033[9m"

    # Foreground (text) colors
    FG_BLACK   = "\033[30m"
    FG_RED     = "\033[31m"
    FG_GREEN   = "\033[32m"
    FG_YELLOW  = "\033[33m"
    FG_BLUE    = "\033[34m"
    FG_MAGENTA = "\033[35m"
    FG_CYAN    = "\033[36m"
    FG_WHITE   = "\033[37m"
    # Bright (high-intensity) foreground colors
    FG_BRIGHT_BLACK   = "\033[90m"
    FG_BRIGHT_RED     = "\033[91m"
    FG_BRIGHT_GREEN   = "\033[92m"
    FG_BRIGHT_YELLOW  = "\033[93m"
    FG_BRIGHT_BLUE    = "\033[94m"
    FG_BRIGHT_MAGENTA = "\033[95m"
    FG_BRIGHT_CYAN    = "\033[96m"
    FG_BRIGHT_WHITE   = "\033[97m"

    # Background colors
    BG_BLACK   = "\033[40m"
    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"
    BG_WHITE   = "\033[47m"
    # Bright (high-intensity) background colors
    BG_BRIGHT_BLACK   = "\033[100m"
    BG_BRIGHT_RED     = "\033[101m"
    BG_BRIGHT_GREEN   = "\033[102m"
    BG_BRIGHT_YELLOW  = "\033[103m"
    BG_BRIGHT_BLUE    = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN    = "\033[106m"
    BG_BRIGHT_WHITE   = "\033[107m"

class ACIA_Terminal:
    def __init__(self,start,end,mode,name='Device_'):
        self.start = start
        self.end = end
        self.mode = mode
        self.name = name
        self.input_buffer = []
        self.output_buffer = []
        self.status = 0x02 
        self.getch = None
        self.cursor_loc = (3,0)
        self.data = {address: 0 for address in range(start,end+1)}
       

        try:
            # Unix-based systems
            import termios, tty, sys

            def getch():
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    return sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            self.getch = getch
        except ImportError:
            # Windows
            import msvcrt

            def getch():
                return msvcrt.getch().decode()
            
            self.getch = getch

        self.read_key_thread = threading.Thread(target=self.read_key, daemon=True)
        self.read_key_thread.start()
        
        
    def read_key(self):
        while True:
            key = self.getch()
            sys.stdout.write(key)
            self.input_buffer.append(ord(key))
            time.sleep(.01)

            
       
    def peek(self,address):
        if len(self.input_buffer) > 0:
            char = self.input_buffer[0]
            return char        
            
    def write(self,address, data):
        #print(f'[{self.name}] --> {str(hex(address))[2:].zfill(4).upper()}:{str(hex(data))[2:].zfill(2).upper()}') 
        if address == self.start + 1:
            pass
            #print('writing to d011')
        elif address == self.start +2:
            if data != 0x00:
                cd = data #if data < 128 else data-0x80
                
                if cd < 0: cd = 0
                #if cd > 0x80: cd = cd-0x80
                if cd == 0xD:
                    #sys.stdout.write('\n')
                    #if self.cursor_loc[0] > 10:
                    #    self.cursor_loc = (1,0)
                    #else:
                    self.cursor_loc = (self.cursor_loc[0]+1,0)
                else:
                    #self.cursor_loc = (self.cursor_loc[0],self.cursor_loc[1]+1)
                    #move_cursor = f"\x1b[{self.cursor_loc[0]};{self.cursor_loc[1]}H" 
                    #sys.stdout.write(move_cursor)  
                    pass
                sys.stdout.write(chr(cd))
                
        elif address == self.start +3:
            pass
            #print(f'writing to d013 {data}')
        else:
            assert False
          
    def read(self,address,peek=False):
        if address == self.start: 
            # Reading data register clears the receive full bit
            if len(self.input_buffer) > 0:
                if peek:
                    return self.input_buffer[0]
                char = self.input_buffer.pop(0)        
                if len(self.input_buffer) == 0:
                    self.status &= ~0x01
                return char 
            else:
                return 0x00         
          
        elif address == self.start + 1:
            if len(self.input_buffer) > 0:
                cr_value = 0x80
            else:
                cr_value = 0x00
            #print(f'[{self.name}] <-- {str(hex(address))[2:].zfill(4).upper()}:{str(hex(cr_value))[2:].zfill(2).upper()}')
            return cr_value

        #DSP
        elif address == self.start + 2:
            # Always ready to recive data to send to reminal
            dsp = 0X00
            return dsp
        return 0x00

class ACIA_Server:
    def __init__(self, acia, host='0.0.0.0', port=6502):
        self.acia = acia
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.input_thread = None
        self.output_thread = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"ACIA server listening on {self.host}:{self.port}")
        self.running = True
        self.accept_thread = threading.Thread(target=self.accept_client, daemon=True)
        self.accept_thread.start()

    def accept_client(self):
        while self.running:
            client, addr = self.server_socket.accept()
            print(f"Client connected from {addr}")
            
            self.client_socket = client
            # Start IO threads
            self.input_thread = threading.Thread(target=self.input_loop, daemon=True)
            self.output_thread = threading.Thread(target=self.output_loop, daemon=True)
            self.input_thread.start()
            self.output_thread.start()

    def input_loop(self):
        # Read from client and inject into ACIA input
        try:
            while self.running and self.client_socket:
                data = self.client_socket.recv(1024)
                if not data:
                    # Client disconnected
                    print("Client disconnected")
                    self.client_socket.close()
                    self.client_socket = None
                    break
                for b in data:
                    
                    self.acia.key_press(b)
        except Exception as e:
            print("Input loop error:", e)
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

    def output_loop(self):
        # Periodically check ACIA output and send to client
        try:
            while self.running and self.client_socket:
                out = self.acia.get_output()
                if out and self.client_socket:
                    self.client_socket.sendall(bytes([out]))

                time.sleep(0.01)
        except Exception as e:
            print("Output loop error:", e)
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        print("ACIA server stopped")

class ACIADevice:
    def __init__(self,start,end,mode,name='Device_'):
        self.start = start
        self.end = end
        self.mode = mode
        self.name = name
        self.input_buffer = []
        self.output_buffer = []
        self.status = 0x02 
        self.server = ACIA_Server(self)
        self.server.start()
        self.data = {address: 0 for address in range(start,end+1)}
        
    def key_press(self,char):
        if char != 10:
            self.input_buffer.append(char)
            
       
    def get_output(self):
        if len(self.output_buffer) > 0:
            data = self.output_buffer.pop(0)
            if isinstance(data,str):
                return ord(data)
            return data

    def peek(self,address):
        if len(self.input_buffer) > 0:
            char = self.input_buffer[0]
            return char        
            
    def write(self,address, data):
        #print(f'[{self.name}] --> {str(hex(address))[2:].zfill(4).upper()}:{str(hex(data))[2:].zfill(2).upper()}') 
        if address == self.start + 1:
            pass
            #print('writing to d011')
        elif address == self.start +2:
            if data != 0x00:
                cd = data #if data < 128 else data-0x80
                
                if cd < 0: cd = 0

                self.output_buffer.append(cd)
              
                if cd == 13: 
                    self.output_buffer.append(10)
                
        elif address == self.start +3:
            pass
            #print(f'writing to d013 {data}')
        else:
            assert False
          
    def read(self,address,peek=False):
        if address == self.start: 
            # Reading data register clears the receive full bit
            if len(self.input_buffer) > 0:
                if peek:
                    return self.input_buffer[0]
                char = self.input_buffer.pop(0)        
                if len(self.input_buffer) == 0:
                    self.status &= ~0x01
                return char 
            else:
                return 0x00         
          
        elif address == self.start + 1:
            if len(self.input_buffer) > 0:
                cr_value = 0x80
            else:
                cr_value = 0x00
            #print(f'[{self.name}] <-- {str(hex(address))[2:].zfill(4).upper()}:{str(hex(cr_value))[2:].zfill(2).upper()}')
            return cr_value

        #DSP
        elif address == self.start + 2:
            # Always ready to recive data to send to reminal
            dsp = 0X00
            return dsp
        return 0x00

class AddressSpace:
    def __init__(self,start:int,end:int,maxvalue=0xFF,ro=False,default_value=0x00,name='AddressSpace'):
        self.start = start
        self.end = end
        self.maxvalue = maxvalue
        self.ro = ro
        self.name = name
        self.data = {int(address): default_value for address in range(start,end+1)}
        self.uuid = str(uuid.uuid4()).replace("-", "")[:8]

        self.f = open(f'./mem/{name}_.mem', 'wb')
        self.f.truncate(self.end - self.start + 1)
        print(f"Created file '{name}_.mem' of size {self.end - self.start + 1} bytes.")

    def ownes(self,key):
        return key in self.data.keys()

    def __setitem__(self, key, value):
        if not self.ro:
            if key in self.data.keys():
                if (self.maxvalue >= value >= 0):
                    self.data[key] = value
                    self.f.seek(key-self.start)
                    self.f.write(value.to_bytes(1, 'little'))
                    self.f.flush()
                else:
                    assert False
                    raise ValueError(f'Value: {value} is out of bounds.')
            else:
                raise IndexError(f'Address {key} does not exist in AddressSpace {self.uuid}')
        else:
            raise IndexError(f'{Ansi.BG_BRIGHT_RED}Address {key:04X} in AddressSpace {self.uuid} is Read Only{Ansi.RESET}')
    
    def write(self,address,value):
        self.__setitem__(address,value)
                
    def __getitem__(self,key):
        if key in self.data.keys():
            return self.data[key]

    def read(self,key,peek=False):
        return self.__getitem__(key)

    def __call__(self):
        return iter(self.data.items())

    def _load_from_kb(self,start=0):
        while True:
            value = input(f"{start:04X} ({self.__getitem__(start):02X}): ")
            if value == '': break
            self.__setitem__(start,int(value,16))
            start +=1
                          
    def _load_from_bf(self,filename,start) -> dict:
        startx = start
        start = start
        symbols = {}
        self.ro = False
        with open(filename, 'rb') as f:
            #lines = f.readlines()
            sbytes = f.read()
        for byte in sbytes:
                self.__setitem__(start,int(byte))
                start += 1
        self.ro = True

       # assert False
        if os.path.exists('mapfile.map'):
            symbols = {}
            pattern = re.compile(r'(?:([_A-Za-z0-9]+)\s+([0-9A-Fa-f]{6})\s[A-Za-z]{3}\s?)+')
            print(f"Loading symbols from file")
            with open('mapfile.map', 'r') as f:
                for line in f:
                    matches = pattern.findall(line)
                    for text, hex_val in matches:
                        hex_val = int(hex_val,16)
                        if hex_val in symbols.keys():
                            if not symbols[hex_val] == text:
                                symbols[hex_val] = symbols[hex_val] + ', ' + text
                        else:
                            symbols[hex_val] = text  

        print(f"Loaded {filename} from {hex(startx)} to {hex(start-1)}")
        return symbols

    def _dump(self):
        rowsum = 0
        con_zero = 0
        hex_row = []
        asc_row = []
        dump = []
        dump_str = []

        for r, key in enumerate(self.data.keys()):
            #if r == 160:
                #break
            #print(r)
            if r % 16 == 0 and r >= 16:
                if rowsum == 0:
                    con_zero += 1
                else:
                    con_zero = 0
                dump.append([key-16,hex_row,asc_row,con_zero])
                hex_row = []
                asc_row = []
                rowsum = 0
                
            
            rowsum += self.data[key]
            hex_row.append(self.data[key])
            asc_row.append(chr(self.data[key]))
        
        dump.reverse()
        in_con = False
        for r, (addr, hexv, ascval, cons) in enumerate(dump):
            #print(addr, hexv, ascval, cons)
            if int(cons) > 3:
                if not in_con:
                    dump_str.append("...")
                in_con = True
                
                pass
            elif int(cons) <=3:
                in_con = False
            if in_con == False:
                hex_str = ' '.join(f"{h:02X}" for h in hexv)
                asc_str = ''.join(f"{a:^3}" if 33 <= ord(a) <= 126 else ' . ' for a in ascval).replace('\n',' . ').replace('\r',' . ')
                dump_str.append(f'{Ansi.FG_BRIGHT_BLUE} {addr:04X}{Ansi.RESET}: {hex_str}, \t {asc_str} {cons}')
        
        dump_str.reverse()
        for string in dump_str:
            print(string)
            
class MappedMemory:
    def __init__(self,start:int,end:int) -> None:
        self.start = start
        self.end = end
        self.current_map:AddressSpace = None
        self.mapping = {}

    def read(self,address,peek=False):
        return self.current_map.read(address,peek)

    def write(self,address,value):
      if address in self.mapping.keys():  
        print(f'{Ansi.FG_BRIGHT_RED}Changing Map to key: {address:04X} AddressSpace: {self.mapping[address].uuid} Start: {self.start:04X} End: {self.end:04X}{Ansi.RESET}',end='')
        self.current_map = self.mapping[address]
      else:
        return self.current_map.write(address,value)

    def map(self, address_space, map_key):
      if map_key in self.mapping.keys():
        raise ValueError(f'Virtual Address Space: Map key {map_key} already exists.')
      else:
        self.mapping[map_key] = address_space
        if self.current_map is None:
          self.current_map = address_space

class MMU:
    def __init__(self):
        self.memory = {}
        self.mapped_memory = []
        self.watch_list = []

        # {key: [readmethod,writemethod]}

    def add(self, address_space:AddressSpace,take_ownership: bool = False):
        for k, v in address_space.data.items():
            self.memory[k] = [address_space.read,address_space.write]
    
    def watch(self, address):
        if not address in self.watch_list:
            self.watch_list.append(address)

    def add_virtual(self, mapped_memory:MappedMemory):
        for key in mapped_memory.mapping.keys():
            if key in self.memory.keys():
                self.memory[key] = [self.memory[key][0],mapped_memory.write]
            else:
               self.memory[key] = [mapped_memory.read,mapped_memory.write]
               
        for i in range(mapped_memory.start,mapped_memory.end+1):
            self.memory[i] = [mapped_memory.read,mapped_memory.write]

    def __getitem__(self,key):
        if key in self.memory.keys():
            if key in self.watch_list:
                print(f"Memory Watch: Read {key}:{self.memory[key][0](key)}")
            return self.memory[key][0](key)
      
    def read(self,key,peek=False):
        if key in self.memory.keys():
            if key in self.watch_list:
                print(f"Memory Watch: Read {key}:{self.memory[key][0](key)}")
            return self.memory[key][0](key,True)
    
    def __setitem__(self,key,value):
        if key in self.memory.keys():
            if key in self.watch_list:
                print(f"Memory Watch: Write {key}:{value}")
            return self.memory[key][1](key,value)
        assert False
    
    def write(self,key,value):
       self.__setitem__(key,value)
    
    def _dump(self):
        count = 1
        valstr = ''
        sorted_memeory = {k: self.memory[k] for k in sorted(self.memory)}
        dump = ''
        for key in sorted_memeory:
            #print(f'{key}: {sorted_memeory[key]}')
            valstr = valstr + f' {self.memory[key][0](key):02X}'

            if count == 1:
                print(f'{key:04X}:',end='')
                dump = dump + f'{key:04X}:'
            if count == 16:
                dump = dump + valstr + '\n'
                print(valstr)
                valstr = ''
                count = 1
            else:
                count +=1
            
        print(f'{valstr}')
        return dump

# No Magik Numbers
CPU_6502_RESET_VECTOR = 0xFFFC
CPU_6502_IRQBRK_VECTOR = 0xFFFE
CPU_6502_NMI_VECTOR = 0

CPU_6502_STACK_POINTER = 0xFD

class CPU:
    def __init__(self,ver='6502'):
        # Registers
        self.a = 0x00  # Accumulator
        self.x = 0x00  # X register
        self.y = 0x00  # Y register
        self.sp = 0xFD # Stack Pointer (on reset is usually 0xFD)
        self.pc = 0x0000 # Program Counter

        # Processor Status (Flags)
        #  N V U B D I Z C
        #  7 6 5 4 3 2 1 0
        self.c = 0 # Carry
        self.z = 0 # Zero
        self.i = 0 # Interrupt Disable
        self.d = 0 # Decimal Mode
        self.b = 0 # Break Command
        self.u = 1 # Unused (Always set to 1 internally)
        self.v = 0 # Overflow
        self.n = 0 # Negative

        self.resetV = CPU_6502_RESET_VECTOR
        self.irqbrkV = CPU_6502_IRQBRK_VECTOR
        self.timer = None

        # Memory: 64KB
        self.memory = MMU()

        self.ignore_ukn_opcode = False
        self.symbols = {}
                
        # Opcode table
        # Each opcode entry: (function, addressing_mode, cycles)
        # For brevity, we'll implement a small subset.
        # Official 6502 Opcodes
    # (Instruction, Addressing Mode, Cycles)

        self.opcode_table_C = {
            # ADC
            0x72: (self.ADC, self.indzp, 5),

            # Additional 65C02 instructions
            0x12: (self.ORA, self.indzp, 5),
            0x32: (self.AND, self.indzp, 5),
            0x52: (self.EOR, self.indzp, 5),
            0x92: (self.STA, self.indzp, 5),
            0xB2: (self.LDA, self.indzp, 5),
            0xD2: (self.CMP, self.indzp, 5),
            0xF2: (self.SBC, self.indzp, 5),

            # STZ (Store Zero)
            0x64: (self.STZ, self.zp, 3),
            0x74: (self.STZ, self.zpx, 4),
            0x9C: (self.STZ, self.abs, 4),
            0x9E: (self.STZ, self.absx, 5),

            # BRA (Branch Always)
            0x80: (self.BRA, self.rel, 3),

            # PHX, PLX (Push/Pull X)
            0xDA: (self.PHX, self.imp, 3),
            0xFA: (self.PLX, self.imp, 4),

            # PHY, PLY (Push/Pull Y)
            0x5A: (self.PHY, self.imp, 3),
            0x7A: (self.PLY, self.imp, 4),

            # INC Accumulator
            0x1A: (self.INC, self.acc, 2),

            # DEC Accumulator
            0x3A: (self.DEC, self.acc, 2),

            # TRB (Test and Reset Bits)
            0x14: (self.TRB, self.zp, 5),
            0x1C: (self.TRB, self.abs, 6),

            # TSB (Test and Set Bits)
            0x04: (self.TSB, self.zp, 5),
            0x0C: (self.TSB, self.abs, 6),

            # Additional BIT addressing modes for 65C02
            0x34: (self.BIT, self.zpx, 4),    # BIT Zero Page,X
            0x3C: (self.BIT, self.absx, 4),   # BIT Absolute,X
            0x89: (self.BIT, self.imm, 2),    # BIT Immediate
        }

        self.opcode_table = {
            # ADC
            0x69: (self.ADC, self.imm, 2),
            0x65: (self.ADC, self.zp, 3),
            0x75: (self.ADC, self.zpx,4),
            0x6D: (self.ADC, self.abs,4),
            0x7D: (self.ADC, self.absx,4), # +1 if page crossed
            0x79: (self.ADC, self.absy,4), # +1 if page crossed
            0x61: (self.ADC, self.indx,6),
            0x71: (self.ADC, self.indy,5), # +1 if page crossed

            # AND
            0x29: (self.AND, self.imm, 2),
            0x25: (self.AND, self.zp, 3),
            0x35: (self.AND, self.zpx,4),
            0x2D: (self.AND, self.abs,4),
            0x3D: (self.AND, self.absx,4), # +1 if page crossed
            0x39: (self.AND, self.absy,4), # +1 if page crossed
            0x21: (self.AND, self.indx,6),
            0x31: (self.AND, self.indy,5), # +1 if page crossed

            # ASL
            0x0A: (self.ASL, self.imp, 2),  # Accumulator
            0x06: (self.ASL, self.zp, 5),
            0x16: (self.ASL, self.zpx,6),
            0x0E: (self.ASL, self.abs,6),
            0x1E: (self.ASL, self.absx,7),

            # BCC
            0x90: (self.BCC, self.rel, 2), # +1 if branch taken, +1 if page crossed

            # BCS
            0xB0: (self.BCS, self.rel, 2),

            # BEQ
            0xF0: (self.BEQ, self.rel, 2),

            # BIT
            0x24: (self.BIT, self.zp, 3),
            0x2C: (self.BIT, self.abs,4),

            # BMI
            0x30: (self.BMI, self.rel, 2),

            # BNE
            0xD0: (self.BNE, self.rel, 2),

            # BPL
            0x10: (self.BPL, self.rel, 2),

            # BRK
            0x00: (self.BRK, self.imp, 7),

            # BVC
            0x50: (self.BVC, self.rel, 2),

            # BVS
            0x70: (self.BVS, self.rel, 2),

            # CLC
            0x18: (self.CLC, self.imp, 2),

            # CLD
            0xD8: (self.CLD, self.imp, 2),

            # CLI
            0x58: (self.CLI, self.imp, 2),

            # CLV
            0xB8: (self.CLV, self.imp, 2),

            # CMP
            0xC9: (self.CMP, self.imm, 2),
            0xC5: (self.CMP, self.zp, 3),
            0xD5: (self.CMP, self.zpx,4),
            0xCD: (self.CMP, self.abs,4),
            0xDD: (self.CMP, self.absx,4), # +1 if page crossed
            0xD9: (self.CMP, self.absy,4), # +1 if page crossed
            0xC1: (self.CMP, self.indx,6),
            0xD1: (self.CMP, self.indy,5), # +1 if page crossed

            # CPX
            0xE0: (self.CPX, self.imm, 2),
            0xE4: (self.CPX, self.zp, 3),
            0xEC: (self.CPX, self.abs,4),

            # CPY
            0xC0: (self.CPY, self.imm, 2),
            0xC4: (self.CPY, self.zp, 3),
            0xCC: (self.CPY, self.abs,4),

            # DEC
            0xC6: (self.DEC, self.zp, 5),
            0xD6: (self.DEC, self.zpx,6),
            0xCE: (self.DEC, self.abs,6),
            0xDE: (self.DEC, self.absx,7),

            # DEX
            0xCA: (self.DEX, self.imp, 2),

            # DEY
            0x88: (self.DEY, self.imp, 2),

            # EOR
            0x49: (self.EOR, self.imm, 2),
            0x45: (self.EOR, self.zp, 3),
            0x55: (self.EOR, self.zpx,4),
            0x4D: (self.EOR, self.abs,4),
            0x5D: (self.EOR, self.absx,4), # +1 if page crossed
            0x59: (self.EOR, self.absy,4), # +1 if page crossed
            0x41: (self.EOR, self.indx,6),
            0x51: (self.EOR, self.indy,5), # +1 if page crossed

            # INC
            0xE6: (self.INC, self.zp, 5),
            0xF6: (self.INC, self.zpx,6),
            0xEE: (self.INC, self.abs,6),
            0xFE: (self.INC, self.absx,7),

            # INX
            0xE8: (self.INX, self.imp, 2),

            # INY
            0xC8: (self.INY, self.imp, 2),

            # JMP
            0x4C: (self.JMP, self.abs,3),
            0x6C: (self.JMP, self.ind,5),

            # JSR
            0x20: (self.JSR, self.abs,6),

            # LDA
            0xA9: (self.LDA, self.imm, 2),
            0xA5: (self.LDA, self.zp, 3),
            0xB5: (self.LDA, self.zpx,4),
            0xAD: (self.LDA, self.abs,4),
            0xBD: (self.LDA, self.absx,4), # +1 if page crossed
            0xB9: (self.LDA, self.absy,4), # +1 if page crossed
            0xA1: (self.LDA, self.indx,6),
            0xB1: (self.LDA, self.indy,5), # +1 if page crossed

            # LDX
            0xA2: (self.LDX, self.imm, 2),
            0xA6: (self.LDX, self.zp, 3),
            0xB6: (self.LDX, self.zpy,4),
            0xAE: (self.LDX, self.abs,4),
            0xBE: (self.LDX, self.absy,4), # +1 if page crossed

            # LDY
            0xA0: (self.LDY, self.imm, 2),
            0xA4: (self.LDY, self.zp, 3),
            0xB4: (self.LDY, self.zpx,4),
            0xAC: (self.LDY, self.abs,4),
            0xBC: (self.LDY, self.absx,4), # +1 if page crossed

            # LSR
            0x4A: (self.LSR, self.imp, 2), # Accumulator
            0x46: (self.LSR, self.zp, 5),
            0x56: (self.LSR, self.zpx,6),
            0x4E: (self.LSR, self.abs,6),
            0x5E: (self.LSR, self.absx,7),

            # NOP
            0xEA: (self.NOP, self.imp,2),

            # ORA
            0x09: (self.ORA, self.imm, 2),
            0x05: (self.ORA, self.zp, 3),
            0x15: (self.ORA, self.zpx,4),
            0x0D: (self.ORA, self.abs,4),
            0x1D: (self.ORA, self.absx,4), # +1 if page crossed
            0x19: (self.ORA, self.absy,4), # +1 if page crossed
            0x01: (self.ORA, self.indx,6),
            0x11: (self.ORA, self.indy,5), # +1 if page crossed

            # PHA
            0x48: (self.PHA, self.imp,3),

            # PHP
            0x08: (self.PHP, self.imp,3),

            # PLA
            0x68: (self.PLA, self.imp,4),

            # PLP
            0x28: (self.PLP, self.imp,4),

            # ROL
            0x2A: (self.ROL, self.imp, 2), # Accumulator
            0x26: (self.ROL, self.zp, 5),
            0x36: (self.ROL, self.zpx,6),
            0x2E: (self.ROL, self.abs,6),
            0x3E: (self.ROL, self.absx,7),

            # ROR
            0x6A: (self.ROR, self.imp, 2), # Accumulator
            0x66: (self.ROR, self.zp, 5),
            0x76: (self.ROR, self.zpx,6),
            0x6E: (self.ROR, self.abs,6),
            0x7E: (self.ROR, self.absx,7),

            # RTI
            0x40: (self.RTI, self.imp,6),

            # RTS
            0x60: (self.RTS, self.imp,6),

            # SBC
            0xE9: (self.SBC, self.imm,2),
            0xE5: (self.SBC, self.zp,3),
            0xF5: (self.SBC, self.zpx,4),
            0xED: (self.SBC, self.abs,4),
            0xFD: (self.SBC, self.absx,4), # +1 if page crossed
            0xF9: (self.SBC, self.absy,4), # +1 if page crossed
            0xE1: (self.SBC, self.indx,6),
            0xF1: (self.SBC, self.indy,5), # +1 if page crossed

            # SEC
            0x38: (self.SEC, self.imp,2),

            # SED
            0xF8: (self.SED, self.imp,2),

            # SEI
            0x78: (self.SEI, self.imp,2),

            # STA
            0x85: (self.STA, self.zp,3),
            0x95: (self.STA, self.zpx,4),
            0x8D: (self.STA, self.abs,4),
            0x9D: (self.STA, self.absx,5),
            0x99: (self.STA, self.absy,5),
            0x81: (self.STA, self.indx,6),
            0x91: (self.STA, self.indy,6),

            # STX
            0x86: (self.STX, self.zp,3),
            0x96: (self.STX, self.zpy,4),
            0x8E: (self.STX, self.abs,4),

            # STY
            0x84: (self.STY, self.zp,3),
            0x94: (self.STY, self.zpx,4),
            0x8C: (self.STY, self.abs,4),

            # TAX
            0xAA: (self.TAX, self.imp,2),

            # TAY
            0xA8: (self.TAY, self.imp,2),

            # TSX
            0xBA: (self.TSX, self.imp,2),

            # TXA
            0x8A: (self.TXA, self.imp,2),

            # TXS
            0x9A: (self.TXS, self.imp,2),

            # TYA
            0x98: (self.TYA, self.imp,2)
        }
  
        if ver == '65C02':
            self.opcode_table = self.opcode_table | self.opcode_table_C  

    def reset(self):
        # Reset vector at FFFC-FFFD
        low = self.read(self.resetV)
        high = self.read(self.resetV+1)
        self.pc = (high << 8) | low
        self.sp = CPU_6502_STACK_POINTER
        self.set_flags(0x24) # Set flags to default state

    def set_flags(self, value):
        self.c = (value >> 0) & 1
        self.z = (value >> 1) & 1
        self.i = (value >> 2) & 1
        self.d = (value >> 3) & 1
        self.b = (value >> 4) & 1
        self.u = (value >> 5) & 1
        self.v = (value >> 6) & 1
        self.n = (value >> 7) & 1
    
    def set_z_flag(self, condition):
        self.z = 1 if condition else 0

    # Set Negative flag explicitly
    def set_n_flag(self, condition):
        self.n = 1 if condition else 0

    # Set Overflow flag explicitly
    def set_v_flag(self, condition):
        self.v = 1 if condition else 0

    # Set both Zero and Negative flags after most instructions
    def set_zn_flags(self, value):
        self.set_z_flag(value == 0)
        self.set_N_fl

    def get_flags(self):
        return (self.n << 7) | (self.v << 6) | (self.u << 5) | (self.b << 4) | (self.d << 3) | (self.i << 2) | (self.z << 1) | self.c

    def read(self, addr):
        #print(f"Read:{addr:04X} {self.memory[addr & 0xFFFF]:02X}")
        return self.memory[addr & 0xFFFF]

    def write(self, addr, value):
        self.memory[addr & 0xFFFF] = value & 0xFF

    def push(self, value):
        self.write(0x0100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def pull(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read(0x0100 + self.sp)

    # Addressing modes
    def imp(self):
        return None # Implied, no operand

    def imm(self):
        val = self.pc
        self.pc += 1
        return val

    def zp(self):
        addr = self.read(self.pc)
        self.pc += 1
        return addr & 0xFF

    def zpx(self):
        addr = (self.read(self.pc) + self.x) & 0xFF
        self.pc += 1
        return addr

    def zpy(self):
        addr = (self.read(self.pc) + self.y) & 0xFF
        self.pc += 1
        return addr
    
    def indzp(self):
        addr = (self.read(self.pc)) & 0xFF
        self.pc += 1
        return addr

    def acc(self):
        addr = -1
        return addr

    def abs(self):
        low = self.read(self.pc)
        high = self.read(self.pc + 1)
        self.pc += 2
        return (high << 8) | low

    def absx(self):
        base = self.abs()
        return (base + self.x) & 0xFFFF

    def absy(self):
        base = self.abs()
        return (base + self.y) & 0xFFFF

    def ind(self):
        # Read the two-byte pointer from the instruction
        low = self.read(self.pc)
        high = self.read(self.pc + 1)
        pointer = (high << 8) | low
        self.pc += 2

        # Simulate 6502 bug: If pointer low byte is 0xFF, the high byte comes from
        # address (pointer & 0xFF00), not (pointer+1).
        if (pointer & 0x00FF) == 0xFF:
            low_res = self.read(pointer)
            # high byte read from same page, not pointer+1
            high_res = self.read(pointer & 0xFF00)
        else:
            low_res = self.read(pointer)
            high_res = self.read(pointer + 1)

        final_addr = (high_res << 8) | low_res
        return final_addr

    def indx(self):
        zp_addr = (self.read(self.pc) + self.x) & 0xFF
        self.pc += 1
        low = self.read(zp_addr & 0xFF)
        high = self.read((zp_addr + 1) & 0xFF)
        return (high << 8) | low

    def indy(self):
        zp_addr = self.read(self.pc)
        self.pc += 1
        low = self.read(zp_addr & 0xFF)
        high = self.read((zp_addr + 1) & 0xFF)
        return ((high << 8) | low) + self.y

    # Flag helpers
    def set_zn(self, value):
        self.z = 1 if (value & 0xFF) == 0 else 0
        self.n = 1 if (value & 0x80) != 0 else 0

    def rel(self):
        offset = self.read(self.pc)
        self.pc += 1
        # Convert offset to signed
        if offset & 0x80:
            offset -= 0x100
        if offset < -128 or offset > 127:
            raise ValueError()
        return offset

    # Instructions
    def ADC(self, addr):
        val = self.read(addr)
        temp = self.a + val + self.c
        # Set carry if > 255
        self.c = 1 if temp > 0xFF else 0
        # Zero if result == 0
        result = temp & 0xFF
        self.z = 1 if result == 0 else 0
        # Overflow if sign changes
        # Overflow occurs if (A ^ val) & 0x80 == 0 and (A ^ result) & 0x80 != 0
        overflow = ((self.a ^ val) & 0x80) == 0 and ((self.a ^ result) & 0x80) != 0
        self.v = 1 if overflow else 0
        self.n = 1 if (result & 0x80) != 0 else 0
        self.a = result

    def AND(self, addr):
        val = self.read(addr)
        self.a &= val
        self.set_zn(self.a)

    def ASL(self, addr=None):
        # If accumulator mode (imp used as acc)
        if addr is None:
            # Accumulator version
            carry = (self.a >> 7) & 1
            self.a = (self.a << 1) & 0xFF
            self.c = carry
            self.set_zn(self.a)
        else:
            val = self.read(addr)
            carry = (val >> 7) & 1
            val = (val << 1) & 0xFF
            self.write(addr, val)
            self.c = carry
            self.set_zn(val)

    def BCC(self, offset):
        if self.c == 0:
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF
            # If page crossed or branch taken, add cycle
            # (Not strictly required if not simulating exact cycles)
    
    def BCS(self, offset):
        if self.c == 1:
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF

    def BEQ(self, offset):
        if self.z == 1:
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF

    def BIT(self, addr):
        val = self.read(addr)
        #print(f'Address {str(hex(addr))[2:].zfill(4).upper()}')
        temp = self.a & val
        #print({f'a: {str(hex(self.a))[2:].zfill(2).upper()} {int(self.a):08b}  val:{str(hex(val))[2:].zfill(2).upper()} temp:{str(hex(temp))[2:].zfill(2).upper()} {int(temp):08b}'})
        
        self.z = 1 if temp == 0 else 0
        self.v = 1 if (val & 0x40) != 0 else 0
        self.n = 1 if (val & 0x80) != 0 else 0
        #print(f'n={self.n}')
        
    def BMI(self, offset):
        if self.n == 1:
            self.pc = (self.pc + offset) & 0xFFFF

    def BNE(self, offset):
        if self.z == 0:
            self.pc = (self.pc + offset) & 0xFFFF

    def BPL(self, offset):
        if self.n == 0:
            self.pc = (self.pc + offset) & 0xFFFF

    # 65C02 0x80 BRA
    def BRA(self,offset):
        self.PC = (self.PC + offset) & 0xFFFF

    def BRK(self, addr):
        self.pc += 1
        self.push((self.pc >> 8) & 0xFF)
        self.push(self.pc & 0xFF)
        flags = self.get_flags() | 0x10  # B flag set
        self.push(flags)
        self.i = 1
        self.pc = self.read(self.irqbrkV) | (self.read(self.irqbrkV+1) << 8)
        
        
    def BVC(self, offset):
        if self.v == 0:
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF

    def BVS(self, offset):
        if self.v == 1:
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF

    def CLC(self, addr):
        self.c = 0

    def CLD(self, addr):
        self.d = 0

    def CLI(self, addr):
        self.i = 0

    def CLV(self, addr):
        self.v = 0

    def CMP(self, addr):
        val = self.read(addr)
        result = (self.a - val) & 0xFF
        self.c = 1 if self.a >= val else 0
        self.z = 1 if self.a == val else 0
        self.n = 1 if (result & 0x80) != 0 else 0
        #print(f"Comparing {hex(val)} ({chr(val)}), from {hex(addr)}  with {hex(self.a)} ({chr(self.a)}), result: {hex(result)}".replace('\n'," ").replace("\r"," "),end='')

    def CPX(self, addr):
        val = self.read(addr)
        result = (self.x - val) & 0xFF
        self.c = 1 if self.x >= val else 0
        self.z = 1 if self.x == val else 0
        self.n = 1 if (result & 0x80) != 0 else 0
        #print(f"CPX {hex(val)} ({chr(val)}), from {hex(addr)}  with {hex(self.x)} ({chr(self.x)}), result: {hex(result)}",end='')

    def CPY(self, addr):
        val = self.read(addr)
        result = (self.y - val) & 0xFF
        self.c = 1 if self.y >= val else 0
        self.z = 1 if self.y == val else 0
        self.n = 1 if (result & 0x80) != 0 else 0
        #print(f"Comparing {hex(val)} ({chr(val)}), from {hex(addr)}  with {hex(self.y)} ({chr(self.y)}), result: {hex(result)}",end='')

    def DEC(self, addr):
        if addr == -1:
            self.a = self.a - 1 & 0xFF
            self.set_zn(self.a)
        else:
            val = self.read(addr)
            val = (val - 1) & 0xFF
            self.write(addr, val)
            self.set_zn(val)

    def DEX(self, addr):
        self.x = (self.x - 1) & 0xFF
        self.set_zn(self.x)

    def DEY(self, addr):
        self.y = (self.y - 1) & 0xFF
        self.set_zn(self.y)

    def EOR(self, addr):
        val = self.read(addr)
        self.a ^= val
        self.set_zn(self.a)

    def INC(self, addr):
        if addr == -1:
            self.a = self.a + 1 & 0xFF
            self.set_zn(self.a)
        else:
            val = self.read(addr)
            val = (val + 1) & 0xFF
            self.write(addr, val)      
            self.set_zn(val)

    def INX(self, addr):
        self.x = (self.x + 1) & 0xFF
        self.set_zn(self.x)

    def INY(self, addr):
        self.y = (self.y + 1) & 0xFF
        self.set_zn(self.y)

    def _IRQ(self):
        if self.i == 1: return
        irq_str = f"IRQ Hardware IRQ"
        print(f"\n{Ansi.BOLD}{self.pc:04X}: {Ansi.BG_BRIGHT_RED} {irq_str:<127}{Ansi.RESET}",end='')
        #self.i = 1
        low_byte = self.pc & 0xFF
        high_byte = (self.pc >> 8) & 0xFF
        self.push(high_byte)
        self.push(low_byte)
        self.push(self.get_flags())

        low = self.read(0xFFFE)
        high = self.read(0xFFFE + 1)
        self.pc = (high << 8) | low
        self.i = 0

    def JMP(self, addr):
        self.pc = addr

    def JSR(self, addr):
        # Push (PC-1)
        temp = self.pc - 1
        self.push((temp >> 8) & 0xFF)
        self.push(temp & 0xFF)
        self.pc = addr

    def LDA(self, addr):
        val = self.read(addr)
        self.a = val
        self.set_zn(self.a)
        #print(f"[A'] <- {addr:04X}:{val:02X} {'(' + chr(val) + ')' if 0 < val < 127 else ' '}".replace("\n"," ").replace('\r'," "), end='')

    def LDX(self, addr):
        val = self.read(addr)
        self.x = val
        self.set_zn(self.x)

    def LDY(self, addr):
        val = self.read(addr)
        self.y = val
        self.set_zn(self.y)

    def LSR(self, addr=None):
        if addr is None:
            # Accumulator
            carry = self.a & 1
            self.a = (self.a >> 1) & 0xFF
            self.c = carry
            self.set_zn(self.a)
        else:
            val = self.read(addr)
            carry = val & 1
            val = (val >> 1) & 0xFF
            self.write(addr, val)
            self.c = carry
            self.set_zn(val)

    def NOP(self, addr):
        pass

    def ORA(self, addr):
        val = self.read(addr)
        self.a |= val
        self.set_zn(self.a)

    def PHA(self, addr):
        self.push(self.a)

    def PHP(self, addr):
        flags = self.get_flags() | 0x30  # set B and U bits
        self.push(flags)
    
    # 65C02
    def PHX(self,addr):
        self.push(self.x)
    
    # 65C02
    def PHY(self):
        self.push(self.Y)

    def PLA(self, addr):
        val = self.pull()
        self.a = val
        self.set_zn(self.a)

    def PLP(self, addr):
        val = self.pull()
        # Bits 4 and 5 are ignored in stored flags, so we handle that if needed
        self.set_flags((val & 0xEF) | 0x20) # U=1 always
    
    def PLX(self):
        self.X = self.pull()
        self.set_zn_flags(self.X)
    
    def PLY(self):
        self.Y = self.pull()
        self.set_zn_flags(self.Y)

    def ROL(self, addr=None):
        if addr is None:
            # Accumulator
            carry_in = self.c
            carry_out = (self.a >> 7) & 1
            self.a = ((self.a << 1) & 0xFF) | carry_in
            self.c = carry_out
            self.set_zn(self.a)
        else:
            val = self.read(addr)
            carry_in = self.c
            carry_out = (val >> 7) & 1
            val = ((val << 1) & 0xFF) | carry_in
            self.write(addr, val)
            self.c = carry_out
            self.set_zn(val)

    def ROR(self, addr=None):
        if addr is None:
            carry_in = self.c << 7
            carry_out = self.a & 1
            self.a = (carry_in | (self.a >> 1)) & 0xFF
            self.c = carry_out
            self.set_zn(self.a)
        else:
            val = self.read(addr)
            carry_in = self.c << 7
            carry_out = val & 1
            val = (carry_in | (val >> 1)) & 0xFF
            self.write(addr, val)
            self.c = carry_out
            self.set_zn(val)

    def RTI(self, addr):
        # pull flags
        val = self.pull()
        self.set_flags(val)
        low = self.pull()
        high = self.pull()
        self.pc = (high << 8) | low

    def RTS(self, addr):
        low = self.pull()
        high = self.pull()
        self.pc = ((high << 8) | low) + 1

    def SBC(self, addr):
        val = self.read(addr) ^ 0xFF  # invert val for SBC = ADC(val ^ 0xFF)
        temp = self.a + val + self.c
        self.c = 1 if temp > 0xFF else 0
        result = temp & 0xFF
        overflow = ((self.a ^ val) & 0x80) == 0 and ((self.a ^ result) & 0x80) != 0
        self.v = 1 if overflow else 0
        self.z = 1 if result == 0 else 0
        self.n = 1 if (result & 0x80) != 0 else 0
        self.a = result

    def SEC(self, addr):
        self.c = 1

    def SED(self, addr):
        self.d = 1

    def SEI(self, addr):
        self.i = 1

    def STA(self, addr):
        self.write(addr, self.a)

    def STX(self, addr):
        self.write(addr, self.x)

    def STY(self, addr):
        self.write(addr, self.y)
    
    # 65C02
    def STZ(self, addr):
        self.write(addr, 0x00)

    def TAX(self, addr):
        self.x = self.a
        self.set_zn(self.x)

    def TAY(self, addr):
        self.y = self.a
        self.set_zn(self.y)
    
    # 65C02
    def TRB(self, addr):
        value = self.read(addr)
        result = (~self.a) & value
        self.set_z_flag(self.a & value == 0)
        self.write(addr, result)
    
    def TSB(self, addr):
        value = self.read(addr)
        result = self.a | value
        self.set_z_flag(self.a & value == 0)
        self.write(addr, result)

    def TSX(self, addr):
        self.x = self.sp
        self.set_zn(self.x)

    def TXA(self, addr):
        self.a = self.x
        self.set_zn(self.a)

    def TXS(self, addr):
        self.sp = self.x

    def TYA(self, addr):
        self.a = self.y
        self.set_zn(self.a)

    def step(self):
        import datetime
        if self.timer is None:
            self.timer  = time.time()
        
        opcodesym = ''  # If symbols present we will load these
        opcode = self.read(self.pc)
        if self.pc in self.symbols.keys(): 
            opcodesym = Ansi.FG_BRIGHT_GREEN + "(" + self.symbols[self.pc].strip() + ")" 
        else:
            opcodesym = Ansi.FG_BRIGHT_GREEN         
        inst_addr = self.pc
        
        self.pc += 1

        if opcode not in self.opcode_table:
            # Unimplemented opcode - just NOP for now
            # In a real emulator, you might handle this differently.
            raise ValueError(f'{hex(inst_addr)} OPCODE NOT FOUND: {hex(opcode)}')
        else:    
            #try:
            instr, mode, cycles = self.opcode_table[opcode]
            addr = mode()
            instr(addr)
            time.sleep(SLEEP)
            
            #except KeyboardInterrupt:
                #print("Debug here")
                #exit()
                
            #except Exception as e:
                #print(e)
            #finally:
            
            a, x, y, z, i, d, b, u, v, n = self.a, self.x, self.y, self.z, self.i, self.d, self.b, self.u, self.v, self.n
        
            addr_str = f"{addr:04X}" if addr else "----"
            if addr is not None:
                addr_val = self.memory.read(addr,True)
                if addr_val is not None:
                    addr_str += f"  [{addr_val:02X}] {'(' + chr(addr_val) + ')' if 47 < addr_val < 127 else ''}"
                pass
            if addr in self.symbols.keys():
                addr_str += f"     {self.symbols[addr]:>10} "
            sp = self.sp
            stack = []
            stack_str = ''
            for ad in range(sp,0XfD):
                stack.append(self.read(0x0100 + ad +1))
            for s in stack:
                stack_str = stack_str + f' {s:02X}'

            '''
            move_cursor = "\x1b[1;100H" 
            sys.stdout.write(move_cursor)  
            sys.stdout.write(f"{inst_addr:04X}: {opcodesym:<25} {Ansi.BOLD}{Ansi.BG_BRIGHT_GREEN} {instr.__qualname__[-3:]} {Ansi.RESET}{Ansi.BG_BLUE}") 
            move_cursor = "\x1b[2;100H"
            sys.stdout.write(move_cursor)  
            sys.stdout.write(f"{Ansi.BG_YELLOW}{Ansi.FG_BRIGHT_BLUE} a:{a:02X}, x:{x:02X}, y:{y:02X} {Ansi.RESET}")        
            #print(f"\n{inst_addr:04X}: {opcodesym:<25} {Ansi.BOLD}{Ansi.BG_BRIGHT_GREEN} {instr.__qualname__[-3:]} {Ansi.RESET}{Ansi.BG_BLUE}  {mode.__qualname__[-3:]} {addr_str:<32}{Ansi.BG_YELLOW}{Ansi.FG_BRIGHT_BLUE} a:{a:02X}, x:{x:02X}, y:{y:02X} {Ansi.BG_GREEN} z:{z:01X} i:{i:01X} d:{d:01X} b:{b:01X} u:{u:01X} v:{v:01X} n:{n:01X} {Ansi.BG_BRIGHT_BLACK} {Ansi.BG_BRIGHT_CYAN}sp:[{sp:02X}]: [{stack_str}] {Ansi.RESET}",end=' ')
            '''
            if self.timer is not None:
                if int(time.time() - self.timer) >= 5.0:
                    self._IRQ()
                    self.timer = start_time = time.time()
            
    