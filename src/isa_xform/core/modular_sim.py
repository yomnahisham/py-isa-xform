import sys
import struct
import keyboard
from pynput import keyboard
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .disassembler import Disassembler, DisassembledInstruction
from .isa_loader import ISADefinition, Instruction, AddressSpace
from .symbol_table import SymbolTable

class Simulator:
    def __init__(self, isa_definition: ISADefinition, address_space: AddressSpace, symbol_table: Optional[SymbolTable] = None, disassembler: Optional[Disassembler] = None):
        self.isa_definition = isa_definition
        self.symbol_table = symbol_table if symbol_table else SymbolTable()
        self.disassembler = disassembler if disassembler else Disassembler(isa_definition, self.symbol_table)
        self.memory = bytearray(65536)  # 64KB memory
        self.pc = 0
        self.pc_step = self.isa_definition.word_size // 8
        self.regs = [0] * len(self.isa_definition.registers)
        self.reg_names = [reg.name for reg in self.isa_definition.registers]
        self.regs[self.reg_names.index("pc")] = self.isa_definition.address_space.default_code_start


    def load_memory_from_file(self, filename: str) -> bool:
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                if len(data) > len(self.memory):
                    print(f"Error: File '{filename}' exceeds memory size", file=sys.stderr)
                    return False
                self.memory[:len(data)] = data
            print(f"Loaded {len(data)} bytes from '{filename}' into memory")
            return True
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            return False
    
    def read_memory_byte(self, addr: int) -> int:
        if 0 <= addr < len(self.memory):
            return self.memory[addr]
        else:
            print(f"Error: Memory access out of bounds at address {addr}", file=sys.stderr)
            return 0
    
    def write_memory_byte(self, addr: int, value: int):
        if 0 <= addr < len(self.memory):
            self.memory[addr] = value & 0xFF
        else:
            print(f"Error: Memory access out of bounds at address {addr}", file=sys.stderr)
    
    def read_memory_word(self, addr: int) -> int: # TO BE VISITED
        if 0 <= addr < len(self.memory) - 1:
            if self.isa_definition.endianness == 'little':
                return struct.unpack('<H', self.memory[addr:addr + self.pc_step])[0] #NOT SURE ABOUT + PC_STEP
            else:                
                return struct.unpack('>H', self.memory[addr:addr + self.pc_step])[0] 
        else:
            print(f"Error: Memory access out of bounds at address {addr}", file=sys.stderr)
            return 0
        
    def write_memory_word(self, addr: int, value: int): # TO BE VISITED
        if 0 <= addr < len(self.memory) - 1:
            if self.isa_definition.endianness == 'little':
                self.memory[addr:addr + self.pc_step] = struct.pack('<H', value & 0xFFFF)
            else:
                self.memory[addr:addr + self.pc_step] = struct.pack('>H', value & 0xFFFF)
        else:
            print(f"Error: Memory access out of bounds at address {addr}", file=sys.stderr)

    
    def sign_extend(self, value: int, bits: int) -> int:
        if value & (1 << (bits - 1)):
            value -= 1 << bits
        return value
    
    def run(self):
        while self.pc < len(self.memory):
            instruction = self.read_memory_word(self.pc)
            if instruction == 0:
                print("Program terminated")
                break
            disassembled = self.disassembler.disassemble_instruction(instruction, self.pc)
            if disassembled is None:
                print(f"Error: Unknown instruction at address {self.pc:04X}")
                break
            print(f"0x{self.pc:04X}: {disassembled.mnemonic} {disassembled.operands}")

            if not self.execute_instruction(disassembled):
                print("Execution terminated by instruction")
                break

            self.pc += self.pc_step

            if self.pc >= len(self.memory):
                print("Reached end of memory")
                break

            print(f"Registers: {': '.join(f'{name}: {value}' for name, value in zip(self.reg_names, self.regs))}")
        print("Simulation complete")

