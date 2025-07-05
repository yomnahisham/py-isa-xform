import sys
import struct
import re
import numpy as np
import keyboard
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .disassembler import Disassembler, DisassembledInstruction, DisassemblyResult
from .isa_loader import ISADefinition, Instruction, AddressSpace
from .symbol_table import SymbolTable

def sign_extend(value: int, bits: int) -> int:
    """Sign extend a value from specified number of bits to 16 bits"""
    if value & (1 << (bits - 1)):
        mask = (1 << bits) - 1
        return value | (~mask)
    return value & ((1 << bits) - 1)

def unsigned(value: int) -> int:
    unsigned = np.uint16(value)
    return unsigned
class Simulator:
    def __init__(self, isa_definition: ISADefinition, symbol_table: Optional[SymbolTable] = None, disassembler: Optional[Disassembler] = None):
        self.isa_definition = isa_definition
        self.symbol_table = symbol_table if symbol_table else SymbolTable()
        self.disassembler = disassembler if disassembler else Disassembler(isa_definition, self.symbol_table)
        self.memory = bytearray(65536)  # 64KB memory
        #self.pc = isa_definition.address_space.default_code_start
        self.pc = 0
        self.pc_step = self.isa_definition.word_size // 8
        self.regs = [0] * len(self.isa_definition.registers['general_purpose'])  # Initialize registers
        self.reg_names = [reg for reg in self.isa_definition.registers]
        self.key = "start"


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
    
    def extract_parameters(self, syntax: str) -> List[str]:
        """ Extracts parameter names from assembly string"""
        parts = syntax.split()
        if len(parts) < 2:
            print(f"Error: Invalid syntax '{syntax}'", file=sys.stderr)
            return []
        
        operand_string = ' '.join(parts[1:])  # Join everything after the mnemonic

        operands = re.findall(r'\b[a-zA-Z]\w*|\d+', operand_string)
        operand_list = list(dict.fromkeys(operands))  # Remove duplicates while preserving order
        return operand_list
    
    def generic_to_register_name(self, syntax: str, generic: List[str], operands: List[str]) -> str:
        """Converts generic operand names to actual register names in the syntax"""
        replacement_dict = dict(zip(generic, operands))
        for old_name, new_name in replacement_dict.items():
            syntax = syntax.replace(old_name, new_name)
        return syntax
    
    def register_name_to_index(self, syntax: str, operands: List[str]) -> str:
        """Converts register name to index based on ISA definition"""
        result = syntax
        reg_objs = self.isa_definition.registers['general_purpose']
        reg_names = [reg.name if hasattr(reg, 'name') else str(reg) for reg in reg_objs]
        reg_aliases = [reg.alias[0] if hasattr(reg, 'alias') and reg.alias else None for reg in reg_objs]
        for operand in operands:
            if operand in reg_names:
                idx = reg_names.index(operand)
            elif operand in reg_aliases:
                idx = reg_aliases.index(operand)
            else:
                # print(f"Warning: Operand '{operand}' not found in register names or aliases.", file=sys.stderr)
                continue
            result = result.replace(operand, f"regs[{idx}]")
        result = result.replace("memory", "self.memory")
        result = result.replace("PC", "self.pc")
        return result        
    
    def disassemble_instruction(self, instruction: int, pc: int) -> Optional[DisassembledInstruction]:
        if self.isa_definition.endianness == 'little':
            instruction = struct.pack('<H', self.read_memory_word(pc))
        else:
            instruction = struct.pack('>H', self.read_memory_word(pc))

        disassembled = self.disassembler.disassemble(instruction, pc)
        if disassembled.instructions:
            instruction = disassembled.instructions[0]
            if instruction.operands:
                print(f"0x{self.pc:04x}: {instruction.mnemonic} {', '.join(instruction.operands)}")
                return disassembled
            else:
                print(f"{instruction.mnemonic}")
                return disassembled
        return f"Error: Unknown instruction at address {pc:04X}"
    
    def get_key(self, target_key: str) -> int:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == target_key:
                return 1
        return 0

    
    def execute_instruction(self, disassembled_instruction: DisassemblyResult):
        """Executes a disassembled instruction"""
        if disassembled_instruction.instructions[0].instruction.mnemonic == "ECALL":
            code = disassembled_instruction.instructions[0].operands[0]
            code = f"0x{int(code):03X}"
            name = self.isa_definition.ecall_services[code].name
            if name == "exit":
                print("Exiting simulation")
                return False
            elif name == "read_string":
                addr = self.regs[6]  # a0 register
                max_length = self.regs[7]  # a1 register
                string = input()
                if len(string) > max_length:
                    print(f"Input exceeds maximum length of {max_length} characters")
                    return True
                for i, char in enumerate(string):
                    if addr + i < len(self.memory):
                        self.write_memory_byte(addr + i, ord(char))
                self.write_memory_byte(addr + len(string), 0)  # Null-terminate the string
                self.regs[6] = len(string)  # Store length in a0 register
            elif name == "read_integer":
                try:
                    value = int(input("Enter an integer: "))
                    self.regs[6] = int(value)  # Store in a0 register
                except ValueError:
                    print("Invalid input, expected an integer")
            elif name == "print_string":
                addr = self.regs[6]  # a0 register
                string = ""
                while addr < len(self.memory) and self.memory[addr] != 0:
                    string += chr(self.memory[addr])
                    addr += 1
                print(string)
            elif name == "print_int":
                return
            elif name == "play_tone":
                frequency = self.regs[6]  # a0 register
                duration_ms = self.regs[7]  # a1 register
                print(f"Playing tone at {frequency}Hz for {duration_ms}ms")
            elif name == "set_audio_volume":
                volume = self.regs[6]  # a0 register
                if 0 <= volume <= 255:
                    print(f"Setting audio volume to {volume}")
                else:
                    print("Volume must be between 0 and 255")
            elif name == "stop_audio_playback":
                print("Audio playback stopped")
            elif name == "read_keyboard":
                self.regs[7] = self.get_key(chr(self.regs[6])) # a0 register is the key to read, a1 register will hold the result
            elif name == "registers_dump":
                for i, reg in enumerate(self.regs):
                    print(f"{self.reg_names[i]}: {reg}")
            elif name == "memory_dump":
                start = self.regs[6]  # a0 register
                end = self.regs[7]  # a1 register
                for addr in range(start, end + 1):
                    if addr < len(self.memory):
                        print(f"0x{addr:04X}: {self.read_memory_byte(addr)}")
            
            print(f"Executing ECALL service: {name} with code {code}") 
            return True

            
        else:
            generic_syntax = disassembled_instruction.instructions[0].instruction.syntax
            instruction = disassembled_instruction.instructions[0]
            actual_syntax = f"{instruction.mnemonic}  {', '.join(instruction.operands)}"
            semantics = disassembled_instruction.instructions[0].instruction.semantics

            generic_parameters = self.extract_parameters(generic_syntax)
            actual_parameters = self.extract_parameters(actual_syntax)
            #operands_map = self.map_operands_to_registers(generic_parameters, actual_parameters)
            semantics = self.generic_to_register_name(semantics, generic_parameters, actual_parameters)
            executable_string = self.register_name_to_index(semantics, actual_parameters)
            print(f"Executing: {executable_string}")
            exec(executable_string, {'regs': self.regs, 'memory': self.memory, 'self': self, 'unsigned': unsigned, 'sign_extend': sign_extend, 'read_memory_word': self.read_memory_word, 'write_memory_word': self.write_memory_word})
            return True
        
    
    def run(self):
        while self.pc < len(self.memory) and self.key != 'q':
            instruction = self.read_memory_word(self.pc)

            if instruction == 0:
                print("Program terminated")
                break
            disassembled = self.disassemble_instruction(instruction, self.pc)
            if disassembled is None:
                print(f"Error: Unknown instruction at address {self.pc:04X}")
                break

            if not self.execute_instruction(disassembled):
                print("Execution terminated by instruction")
                break

            self.pc += self.pc_step

            if self.pc >= len(self.memory):
                print("Reached end of memory")
                break
            print(f"Registers: {self.regs}")
            self.key = keyboard.read_event().name
            alias_names = [reg.alias[0] if reg.alias else reg.name for reg in self.isa_definition.registers['general_purpose']]
            #print(f"Registers: {': '.join(f'{name}: {value}' for name, value in zip(alias_names, self.regs))}")
            #key = input("Press Enter to continue, 'q' to quit: ").strip().lower()
        print("Simulation complete")

