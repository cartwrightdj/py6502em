import os
import socket
import threading
import time
import re


DEBUG_OPCODES = True
SLEEP = .1



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
                    #self.client_socket.sendall("Hello".encode('ascii'))
                    print(f'Sening: {out} {hex(out), chr(out)}')
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

class AddressSpace:
    def __init__(self,start:int, end:int, bits=8, read_only=False,name='AddressSpace'):
        self.start = start
        self.end = end
        self.bits = bits
        self.read_only = read_only
        self.name = name if name else f'AddressSpace: {hex(start)}-{hex(end)}'
        self._data = {i:0 for i in range(end+1)}

        self.f = open(name + '_.mem', 'wb')
        self.f.truncate(self.end - self.start + 1)
        print(f"Created file '{name + '_.mem'}' of size {self.end - self.start + 1} bytes.")

    def read(self, address:int):
        if int(address) in self._data.keys():
            return self._data[int(address)]
        raise ValueError(f"Address {hex(address)} does not exist in {self.name}")
    
    def peek(self,address:int):
        return self.read(address)

    def write(self,address:int, value:int):
        if int(address) in self._data.keys():
            if 2**self.bits > value >= 0: 
                self._data[int(address)] = value
                
                self.f.seek(address)
                if isinstance(1,bytes):
                    self.f.write(value)
                else:
                    self.f.write(value.to_bytes(1, 'little'))
            else:
                raise ValueError(f'Value {value} is to large')
        else:
            raise ValueError(f"Address {hex(address)} does not exist in {self.name}")

    def ownes(self,address:int):
        return address in self._data.keys()
    
    def remove_ownership(self,address:int):
        if int(address) in self._data.keys():
            del self._data[address]
        else:
            raise ValueError(f"{self.name} does not own address {address}")

class ACIA(AddressSpace):
    def __init__(self, start, end, read_only=False, name='ACIA'):
        super().__init__(start, end, read_only, name)


class Device:
    def __init__(self,start,end,mode,name='MemoryBlock'):
        self.start = start
        self.end = end
        self.mode = mode
        self.name = name
        self.input_buffer = []
        self.output_buffer = []
        self.status = 0x02 
        self.server = ACIA_Server(self)
        self.server.start()
        
    def key_press(self,char):
        if char != 10:
            self.input_buffer.append(char)
            print(f'Key Press: {char} [{chr(char)}]')
       
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

    def read_data(self):
        # Reading data register clears the receive full bit
        if len(self.input_buffer) > 0:
            char = self.input_buffer.pop(0)
            # after reading, if no more chars, clear bit 0
            if len(self.input_buffer) == 0:
                self.status &= ~0x01
            return char
        else:
            # no data, return something like 0x00
            return 0x00
            
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
          
    def read(self,address):
        if address == self.start: 
            
            data = self.read_data()
            #data = data + 0x80
            #print(f'Sending {data} ({chr(data)})')
            return data 
        
        #KBDCR
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

class MMU:
    def __init__(self):
    # Internal hashmap to store items
        self._addr_spaces = {}
        self._watches = {}

    # Add an item to the container
    def add(self, item):
        print(f'Adding {item.name} {str(hex(item.start)).zfill(4).upper()}:{str(hex(item.end)).zfill(4).upper()}')
        for i in range(item.start,item.end+1):
            if i in self._addr_spaces.keys():
                print(f"Overwriting address {hex(i)}, new owner: {item.name}")
            self._addr_spaces[int(i)] = item

    def add_watch(self,address,end=None,name='Watch'):
        if end is None:
            self._watches[address] = name
        else:
            for i in range(address,end):
                self._watches[i] = name
    
    def watch(self,address,value=None):
        if address in self._watches.keys():
            if value is None:
                print(f'[{self._watches[address]}]:<-{self._addr_spaces[address].peek(address):02X} {self._addr_spaces[address].peek(address)}')
            else:
                print(f'[{self._watches[address]}]:->{value:02X}')

    # Get an item by key
    def __getitem__(self, address):
        if address in self._addr_spaces:  
            #print(f'Reading {address} from {self._addr_spaces[address].name}')
            self.watch(address)         
            return self._addr_spaces[address].read(address)
        raise KeyError(f"Key '{address}' not found in container")

    # Set an item by key
    def __setitem__(self, address, value):
        if value < 0: raise ValueError("Signed values should be in 2s Compliment")
        if address in self._addr_spaces:   
            self.watch(address,value)         
            self._addr_spaces[address].write(address, value)                
        else:
            raise KeyError(f"Address '{str(hex(address))[2:].zfill(4).upper()} ({int(address)})' in not in the MemoryMap")

    # Delete an item by key
    def __delitem__(self, key):
        if key in self._data:
            del self._addr_spaces[key]
        else:
            raise KeyError(f"Key '{key}' not found in container")

    # Check if a key is in the container
    def __contains__(self, key):
        return key in self._data

    # Length of the container
    def __len__(self):
        return len(self._data)

    # Iterator to make the container iterable
    def __iter__(self):
        return iter(self._data)

    # String representation for easy debugging
    def __repr__(self):
        return f"Registers({self._data})"

    # Additional helper method to get all items
    def get_items(self):
        return self._data.copy()

    def dump(self):
        
        c = 0  # Counter to keep track of keys
        hex_line = ""  # String to accumulate hex values
        char_line = ""
        lines = []
        
        
        for key in self._addr_spaces.keys():
            if int(key) % 16 == 0:
                if c != 0:
                    # Print the accumulated hex values for the previous batch
                    lines.append(hex_line.strip() + '\t\t' + '[' + char_line + ']\n')
                    #print(hex_line, char_line)
                # Start a new line with the first key in the batch
                if isinstance(key, int):
                    formatted_key = f'{hex(key)}[{key:05d}]'
                else:
                    formatted_key = f'[{str(key)}]'
                hex_value = f'{self._addr_spaces[key].read(key):02X} '
                hex_line = f'{formatted_key} {hex_value}'
                char_line = ''
                char = f'{chr(self._addr_spaces[key].read(key))} '
                if char.strip() == '': char = '_'
                char_line += char 
                #char_line = re.sub(r'[\r\n]+', ' ', char_line)
            else:
                # Append only the hex value without the key name
                key - int(key)
                hex_value = f'{key:02X}'
                hex_line += f'{self._addr_spaces[key].read(key):02X} '
                char = f'{chr(self._addr_spaces[key].read(key))} '
                if char.strip() == '': char = ' '
                char_line += char 
                #char_line = re.sub(r'[\r\n]+', ' ', char_line)
            c += 1
        
        # Print the last line if it exists
        if hex_line:
            lines.append(hex_line.strip() + '\t\t' + '[' + char_line.replace('\n','').strip() + ']\n')
            #print(hex_line)
        
        with open('memory_dump.txt', 'w',encoding="utf-8") as f:
            f.writelines(lines)

    def _load_from_bf(self,filename,start):
        startx = start
        start = start
        with open(filename, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            print(hex(start),line)
            bytes = line.split(' ')
            for byte in bytes:
                self.__setitem__(start,int(byte.strip(),16))
                start += 1
        print(f"Loaded {filename} from {hex(startx)} to {hex(start-1)}")
      
class CPU:
    def __init__(self):
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

        # Memory: 64KB
        self.memory = MMU()
        self.memory.add(AddressSpace(0,0XFF,name='ZeroPage'))
        self.memory.add(AddressSpace(0x100,2**16,name='MainMemory'))
        self.memory.add(AddressSpace(0xFFFC,0xFFFD,name='6502 Reset Vector'))
        ACIA =Device(0xD010,0xD013,'rw','ACIA')
        self.memory.add(ACIA)

        
        self.memory.add_watch(0x00,name='ARG COUNTER')
        self.memory.add_watch(0x514,name='RUNPTR')
        
        thread = threading.Thread(target=self.timer, args=(5,))
        thread.start()

        
        # Opcode table
        # Each opcode entry: (function, addressing_mode, cycles)
        # For brevity, we'll implement a small subset.
        # Official 6502 Opcodes
    # (Instruction, Addressing Mode, Cycles)
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

    def timer(self,length):
        while True:
            print('Timer Started')
            time.sleep(length)
            print('Initiating IRQ')
            self._IRQ()

    def reset(self):
        # Reset vector at FFFC-FFFD
        low = self.read(0xFFFC)
        high = self.read(0xFFFD)
        self.pc = (high << 8) | low
        self.sp = 0xFD
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

    def get_flags(self):
        return (self.n << 7) | (self.v << 6) | (self.u << 5) | (self.b << 4) | (self.d << 3) | (self.i << 2) | (self.z << 1) | self.c

    def read(self, addr):
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
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF
            print(f'Branching to {str(hex(self.pc))[2:].zfill(2).upper()}')

    def BNE(self, offset):
        if self.z == 0:
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF

    def BPL(self, offset):
        if self.n == 0:
            old_pc = self.pc
            self.pc = (self.pc + offset) & 0xFFFF

    def BRK(self, addr):
        self.pc += 1
        self.push((self.pc >> 8) & 0xFF)
        self.push(self.pc & 0xFF)
        flags = self.get_flags() | 0x10  # B flag set
        self.push(flags)
        self.i = 1
        self.pc = self.read(0xFFFE) | (self.read(0xFFFF) << 8)
        assert False
        
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
        print(f"Comparing {hex(val)} ({chr(val)}), from {hex(addr)}  with {hex(self.a)} ({chr(self.a)}), result: {hex(result)}")

    def CPX(self, addr):
        val = self.read(addr)
        result = (self.x - val) & 0xFF
        self.c = 1 if self.x >= val else 0
        self.z = 1 if self.x == val else 0
        self.n = 1 if (result & 0x80) != 0 else 0

    def CPY(self, addr):
        val = self.read(addr)
        result = (self.y - val) & 0xFF
        self.c = 1 if self.y >= val else 0
        self.z = 1 if self.y == val else 0
        self.n = 1 if (result & 0x80) != 0 else 0
        print(f"Comparing {hex(val)} ({chr(val)}), from {hex(addr)}  with {hex(self.y)} ({chr(self.y)}), result: {hex(result)}")

    def DEC(self, addr):
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
        low_byte = self.pc & 0xFF
        high_byte = (self.pc >> 8) & 0xFF
        self.push(high_byte)
        self.push(low_byte)
        self.push(self.get_flags())

        low = self.read(0xFFFE)
        high = self.read(0xFFFE + 1)
        self.pc = (high << 8) | low

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
        print(f"Loaded 'A' with value {hex(val)} ({chr(val)}), from {hex(addr)}", end='')

    def LDX(self, addr):
        val = self.read(addr)
        self.x = val
        self.set_zn(self.x)

    def LDY(self, addr):
        val = self.read(addr)
        self.y = val
        self.set_zn(self.y)
        print(f"Loaded 'Y' with value {hex(val)}, from {hex(addr)}",end='')

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

    def PLA(self, addr):
        val = self.pull()
        self.a = val
        self.set_zn(self.a)

    def PLP(self, addr):
        val = self.pull()
        # Bits 4 and 5 are ignored in stored flags, so we handle that if needed
        self.set_flags((val & 0xEF) | 0x20) # U=1 always

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

    def TAX(self, addr):
        self.x = self.a
        self.set_zn(self.x)

    def TAY(self, addr):
        self.y = self.a
        self.set_zn(self.y)

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
        opcode = self.read(self.pc)
        if not (0 <= opcode <= 255):
            assert False
        
        inst_addr = self.pc
        
        self.pc += 1

        if opcode not in self.opcode_table:
            # Unimplemented opcode - just NOP for now
            # In a real emulator, you might handle this differently.
            print(f'{hex(inst_addr)} OPCODE NOT FOUND: {hex(opcode)}')
            

        instr, mode, cycles = self.opcode_table[opcode]
        
        a, x, y, z, n = hex(self.a), hex(self.x), hex(self.y), hex(self.z), hex(self.n)

        addr = mode()
        print(f"\n{hex(inst_addr)}\t {instr.__qualname__[-3:]}\t {mode.__qualname__[-3:]}\t {addr}\t a:{a}, x:{x}, y:{y}\t Flags: z:{z} n:{n}",end=' ')
        #print(f'{hex(inst_addr)}:{hex(opcode)} {instr.__qualname__}, {mode.__qualname__}::{hex(addr)}:{hex(self.memory[addr])}')
        try:
            instr(addr)
        except:
            self.memory.dump()
            print(f"\n\n{hex(inst_addr)}\t {instr.__qualname__[-3:]}\t {mode.__qualname__[-3:]}\t {addr}\t a:{a}, x:{x}, y:{y}\t Flags: z:{z} n:{n}",end=' ')
            assert False
        time.sleep(SLEEP)
        return cycles

# Example usage:
if __name__ == "__main__":
    cpu = CPU()
    # Simple test: Load immediate values and transfer
    # Set reset vector to 0x8000
    
    cpu.write(0xFFFC, 0x00)
    cpu.write(0xFFFD, 0x20)

    cpu.write(0xFFFE, 0x99)
    cpu.write(0xFFFF, 0x21)

   
    
    cpu.memory._load_from_bf('wozmon2.bytes',0xEE00)
    print(hex(cpu.memory[0xEE00]))
    
    #cpu.memory.dump()
    cpu.memory._load_from_bf('os.bytes',0x2000)

    #cpu.memory.dump()
    #assert False
       
    cpu.reset()
    cycles = 0
    
    while True:
        c = cpu.step()
        
        cycles += c
        



    
