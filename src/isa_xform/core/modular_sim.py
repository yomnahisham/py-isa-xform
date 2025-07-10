import sys
import struct
import re
import numpy as np
import keyboard
from pynput.keyboard import Key, Listener
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .disassembler import Disassembler, DisassembledInstruction, DisassemblyResult
from .isa_loader import ISADefinition, Register
from .symbol_table import SymbolTable
from ..utils.bit_utils import (
    extract_bits, set_bits, sign_extend, parse_bit_range, 
    create_mask, bytes_to_int, int_to_bytes
)

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
        self.memory = bytearray(300)  # 64KB memory
        self.pc = isa_definition.address_space.default_code_start
        self.data_start = isa_definition.address_space.default_data_start
        self.stack_start = isa_definition.address_space.default_stack_start
        self.pc_step = self.isa_definition.word_size // 8
        self.regs = [0] * len(self.isa_definition.registers['general_purpose'])
        self.reg_names = [reg.alias[0] for reg in self.isa_definition.registers['general_purpose']]
        # get index of sp
        self.sp_index = self.reg_names.index('sp') if 'sp' in self.reg_names else -1
        self.regs[self.sp_index] = self.stack_start  # Initialize stack pointer to stack start address
        self.key = "start"

    def check_key_press(self, target_key: str) -> bool:
        """Checks if a specific key is pressed"""
        key_pressed = False
        def on_press(key):
            nonlocal key_pressed
            try:
                # For alphanumeric keys
                if key.char == target_key:
                    print(f"You pressed '{target_key}'!")
                    key_pressed = True
                    return False  # Stop the listener
            except AttributeError:
                # For special keys
                if key == getattr(Key, target_key, None):
                    print(f"You pressed {target_key}!")
                    key_pressed = True
                    return False
        
        listener = Listener(on_press=on_press)
        listener.start()
        listener.join(0.01)  # Wait for a short time to allow the listener to process events
        if listener.is_alive():
            listener.stop()
        
        self.key = 1 if key_pressed else 0
        return key_pressed
        

    def listen_for_key(self, target_key):
        def on_press(key):
            try:
                # For alphanumeric keys
                if key.char == target_key:
                    print(f"You pressed '{target_key}'!")
                    self.key = 1
                    return False  # Stop the listener
            except AttributeError:
                # For special keys
                if key == target_key:
                    print(f"You pressed {target_key}!")
                    self.key = 1
                    return False
                self.key = 0

        with Listener(on_press=on_press) as listener:
            listener.join()


    def load_memory_from_file(self, filename: str) -> bool:
        """Loads machine code from a file into memory"""
        if not Path(filename).exists():
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            return False
        try:
            # check for endiannness
            if self.isa_definition.endianness == 'little':
                with open(filename, 'rb') as f:
                    data = f.read()
                    if len(data) > len(self.memory):
                        print(f"Error: File '{filename}' exceeds memory size", file=sys.stderr)
                        return False
                    entry_point = data[8:12]
                    entry_point = int.from_bytes(entry_point, byteorder='little')
                    code_start = data[12:16]
                    code_start = int.from_bytes(code_start, byteorder='little')
                    code_size = data[16:20]
                    code_size = int.from_bytes(code_size, byteorder='little')
                    self.memory[code_start:code_start + code_size] = data[entry_point:entry_point + code_size]
                    print(self.memory[self.pc:self.pc + code_size])
                    entry_point += code_size
                    data_start = data[20:24]
                    data_start = int.from_bytes(data_start, byteorder='little')
                    data_size = data[24:28]
                    data_size = int.from_bytes(data_size, byteorder='little')
                    print(f"Data Start: {data_start} Data Size: {data_size}")
                    self.memory[data_start:data_start + data_size] = data[entry_point:entry_point + data_size]
                    print(self.memory[data_start:data_start + data_size])
                    #self.memory[:len(data)] = data
            else:
                with open(filename, 'rb') as f:
                    data = f.read()
                    if len(data) > len(self.memory):
                        print(f"Error: File '{filename}' exceeds memory size", file=sys.stderr)
                        return False
                    code_start = data[12:16]
                    code_start = int.from_bytes(code_start, byteorder='big')
                    code_size = data[16:20]
                    code_size = int.from_bytes(code_size, byteorder='big')
                    self.memory[self.pc:self.pc + code_size] = data[code_start:code_start + code_size]
                    data_start = data[20:24]
                    data_start = int.from_bytes(data_start, byteorder='big')
                    data_size = data[24:28]
                    data_size = int.from_bytes(data_size, byteorder='big')
                    self.memory[self.data_start:self.data_start + data_size] = data[data_start:data_start + data_size]
                    # Reverse the byte order for big-endian
                    #self.memory[:len(data)] = data[::-1]
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
        if 0 <= addr < len(self.memory) - self.pc_step:
            if self.isa_definition.endianness == 'little':
                return struct.unpack('<H', self.memory[addr:addr + self.pc_step])[0] 
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
        operands = re.findall(r'(?:0x[0-9a-fA-F]+|0b[01]+|0o[0-7]+|-?\d+|[a-zA-Z_]\w*)', operand_string)
        return operands
    
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
        for operand in operands:
            if operand in reg_names:
                idx = reg_names.index(operand)
                result = result.replace(operand, f"regs[{idx}]")
            else:
                
                # print(f"Warning: Operand '{operand}' not found in register names or aliases.", file=sys.stderr)
                continue
            
        result = result.replace("memory", "self.memory")
        result = result.replace("PC", "self.pc")
        return result        
    
    
    def get_key(self, target_key: str) -> int:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == target_key:
                return 1
        return 0
    
    def map_disassembly_result_to_pc(self, disassembly_result: DisassemblyResult) -> Dict[int, DisassembledInstruction]:
        """Maps disassembled instructions to their program counter (PC) addresses"""
        pc_map = {}
        for instruction in disassembly_result.instructions:
            if instruction is not None:
                pc_map[instruction.address] = instruction
        return pc_map

    
    def execute_instruction(self, disassembled_instruction: DisassembledInstruction) -> bool:
        """Executes a disassembled instruction"""
        if disassembled_instruction.instruction:
            if disassembled_instruction.instruction.mnemonic == "ECALL":
                code = disassembled_instruction.operands[0]
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
                    print(self.memory[self.regs[6]])
                    # addr = self.regs[6]  # a0 register
                    # string = ""
                    # while addr < len(self.memory) and self.memory[addr] != 0:
                    #     string += chr(self.memory[addr])
                    #     addr += 1
                    #print(string)
                elif name == "print_int":
                    print(self.memory[self.regs[6]])
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
                    #self.regs[7] = self.get_key(chr(self.regs[6])) # a0 register is the key to read, a1 register will hold the result
                    self.check_key_press(chr(self.regs[6]))
                    self.regs[7] = self.key
                elif name == "registers_dump":
                    for i, reg in enumerate(self.regs):
                        print(f"{self.reg_names[i]}: {reg}")
                elif name == "memory_dump":
                    start = self.regs[6]  # a0 register
                    end = self.regs[7]  # a1 register
                    for addr in range(start, end + 1):
                        if addr < len(self.memory):
                            print(f"0x{addr:04X}: {self.read_memory_byte(addr)}")
                
                return True
        
            

                
            else:
                generic_assembly = disassembled_instruction.instruction.syntax
                instruction = disassembled_instruction.instruction
                actual_assembly = f"{instruction.mnemonic}  {', '.join(disassembled_instruction.operands)}"
                code = instruction.semantics

                generic_parameters = self.extract_parameters(generic_assembly)
                actual_parameters = self.extract_parameters(actual_assembly)
                code = self.generic_to_register_name(code, generic_parameters, actual_parameters)
                executable_string = self.register_name_to_index(code, actual_parameters)
                print(f"Executing: {executable_string}")
                exec(executable_string, {'regs': self.regs, 'memory': self.memory, 'self': self, 'unsigned': unsigned, 'sign_extend': sign_extend, 'read_memory_word': self.read_memory_word, 'write_memory_word': self.write_memory_word})
                return True
        return True
        

    def run(self, step: bool = False):
        """Runs the simulator, disassembling and executing instructions in memory"""
        disassembly_result = self.disassembler.disassemble(self.memory, self.pc)
        instuctions_map = self.map_disassembly_result_to_pc(disassembly_result)
        loop = "start"
        print(f"Code Start: {self.pc}")
        print(f"Data Start: {self.data_start} ")
        #print(f"Memory: {self.memory} ")

        #while self.pc < len(self.memory) and (loop != 'q' or (not step)):
        while self.pc < len(self.memory): 
            current_instruction = instuctions_map[self.pc] if self.pc in instuctions_map else None
            if current_instruction is None:
                print(f"Skipping instruction at PC: {self.pc} (NoneType)")
                continue

            print(f"PC: {self.pc:04X} - {current_instruction.mnemonic} {', '.join(current_instruction.operands)}")
            temp_pc = self.pc
            if self.execute_instruction(current_instruction):
                if temp_pc == self.pc:
                    self.pc += self.pc_step
                if "NOP" in current_instruction.mnemonic:
                    continue
                else:
                    if step:
                        values = [reg for reg in self.regs]
                        print(self.regs)
                        #print(f"Registers: {', '.join(f'{name}: {value}' for name, value in zip(self.reg_names, values))}")
                        #loop = input("Press Enter to continue, 'q' to quit: ").strip().lower()
                    else:
                        if self.pc >= len(disassembly_result.instructions):
                            print("Reached end of disassembled instructions")
                            break
                
            else:
                print("Execution terminated by instruction")
                break
        print("Simulation completed")

