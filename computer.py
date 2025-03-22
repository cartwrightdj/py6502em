
class Clock:
    def __init__(self) -> None:
        self._connections = []
    
    def up(self):
        pass

    def down(self):
        pass

PC = 1

class CPU():
    
    def __init__(self) -> None:
        self._mop_queue = self._fetch
        self._mar = None
        self._registers = {
            PC:'0' * 16
        }

        self._memory = None
    
    def _next_op(self):
        self._mop_queue()

    def _decode(self):
        print('>> decode')
        #self.inst, self.op1, self.op2 = self._mar[:6], self._mar[6:11], self._mar[11:16]

    def _fetch(self):
        print('>> fetch')
        #self._mar = self._memory.read(self._registers[PC])
        self._mop_queue = self._decode


cpu = CPU()
cpu._next_op()
cpu._next_op()

class Register:
    def __init__(self,name: str, bits: int = 16) -> None:
        self._name = name
        self._bits = bits
        self._bit_map = None
        self._value = '0' * bits

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value