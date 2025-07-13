import sys
import struct
import re
import numpy as np
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from isa_xform.core.disassembler import Disassembler, DisassembledInstruction, DisassemblyResult
from isa_xform.core.isa_loader import ISADefinition, ISALoader, Register
from isa_xform.core.symbol_table import SymbolTable
from isa_xform.utils.bit_utils import (
    extract_bits, set_bits, sign_extend, parse_bit_range, 
    create_mask, bytes_to_int, int_to_bytes
)

@dataclass
class Register:
    def __init__(self, name: str, alias: str, size: int = 16, value: int = 0):
        self.name = name
        self.alias = alias
        self.value = value
        self.size = size
        self.mask = (1 << self.size) - 1
        self.sign_bit = 1 << (self.size - 1)
        self.value = self._normalize(self.value)
    
    def _normalize(self, value: int) -> int:
        """Normalize value to register size"""
        return value & self.mask
    
    def _to_signed(self, value: int) -> int:
        """Convert unsigned value to signed based on register size"""
        if value & self.sign_bit:
            return value - (1 << self.size)
        return value
    
    def _from_signed(self, value: int) -> int:
        """Convert signed value to unsigned representation"""
        if value < 0:
            return (1 << self.size) + value
        return value
    
    
    # Arithmetic operations
    def __add__(self, other):
        if isinstance(other, Register):
            result = (self.value + other.value) & self.mask
        else:
            result = (self.value + other) & self.mask
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __sub__(self, other):
        if isinstance(other, Register):
            result = (self.value - other.value) & self.mask
        else:
            result = (self.value - other) & self.mask
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __mul__(self, other):
        if isinstance(other, Register):
            result = (self.value * other.value) & self.mask
        else:
            result = (self.value * other) & self.mask
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __truediv__(self, other):
        if isinstance(other, Register):
            signed_self = self._to_signed(self.value)
            signed_other = self._to_signed(other.value)
            result = self._from_signed(int(signed_self / signed_other))
        else:
            signed_self = self._to_signed(self.value)
            result = self._from_signed(int(signed_self / other))
        return Register(self.size, result & self.mask)
    
    def __mod__(self, other):
        if isinstance(other, Register):
            result = (self.value % other.value) & self.mask
        else:
            result = (self.value % other) & self.mask
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    # Logical operations
    def __and__(self, other):
        if isinstance(other, Register):
            result = self.value & other.value
        else:
            result = self.value & other
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __or__(self, other):
        if isinstance(other, Register):
            result = self.value | other.value
        else:
            result = self.value | other
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __xor__(self, other):
        if isinstance(other, Register):
            result = self.value ^ other.value
        else:
            result = self.value ^ other
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __lshift__(self, other):
        if isinstance(other, Register):
            shift = other.value
        else:
            shift = other
        result = (self.value << shift) & self.mask
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __rshift__(self, other):
        if isinstance(other, Register):
            shift = other.value
        else:
            shift = other
        result = self.value >> shift
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    def __invert__(self):
        result = (~self.value) & self.mask
        return Register(name=self.name, alias= self.alias, size=self.size, value=result)
    
    # Comparison operations
    def __eq__(self, other):
        if isinstance(other, Register):
            return self.value == other.value
        return self.value == other
    
    def __lt__(self, other):
        if isinstance(other, Register):
            return self._to_signed(self.value) < self._to_signed(other.value)
        return self._to_signed(self.value) < other
    
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)
    
    def __gt__(self, other):
        if isinstance(other, Register):
            return self._to_signed(self.value) > self._to_signed(other.value)
        return self._to_signed(self.value) > other
    
    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)
    
    # In-place operations
    def __iadd__(self, other):
        if isinstance(other, Register):
            self.value = (self.value + other.value) & self.mask
        else:
            self.value = (self.value + other) & self.mask
        return self
    
    def __isub__(self, other):
        if isinstance(other, Register):
            self.value = (self.value - other.value) & self.mask
        else:
            self.value = (self.value - other) & self.mask
        return self
    
    def __imul__(self, other):
        if isinstance(other, Register):
            self.value = (self.value * other.value) & self.mask
        else:
            self.value = (self.value * other) & self.mask
        return self
    
    def __ilshift__(self, other):
        if isinstance(other, Register):
            shift = other.value
        else:
            shift = other
        self.value = (self.value << shift) & self.mask
        return self
    
    def __irshift__(self, other):
        if isinstance(other, Register):
            shift = other.value
        else:
            shift = other
        self.value = self.value >> shift
        return self
    
    def __iand__(self, other):
        if isinstance(other, Register):
            self.value = self.value & other.value
        else:
            self.value = self.value & other
        return self
    
    def __ior__(self, other):
        if isinstance(other, Register):
            self.value = self.value | other.value
        else:
            self.value = self.value | other
        return self
    
    def __ixor__(self, other):
        if isinstance(other, Register):
            self.value = self.value ^ other.value
        else:
            self.value = self.value ^ other
        return self
    
    # Utility methods
    def signed_value(self) -> int:
        """Get the signed interpretation of the register value"""
        return self._to_signed(self.value)
    
    def unsigned_value(self) -> int:
        """Get the unsigned interpretation of the register value"""
        return self.value
    
    def set_value(self, value: int):
        """Set the register value"""
        self.value = self._normalize(value)
    
    def __str__(self):
        return f"{self.name} ({self.alias[0]}): {self.signed_value()}"
    
    def __repr__(self):
        return self.__str__()

class Simulator:
    def __init__(self, isa_definition: ISADefinition, symbol_table: Optional[SymbolTable] = None, disassembler: Optional[Disassembler] = None):
        self.isa_definition = isa_definition
        self.symbol_table = symbol_table if symbol_table else SymbolTable()
        self.disassembler = disassembler if disassembler else Disassembler(isa_definition, self.symbol_table)
        self.memory = bytearray(65536)  # 64KB memory
        self.pc = isa_definition.address_space.default_code_start
        self.data_start = isa_definition.address_space.default_data_start
        self.stack_start = isa_definition.address_space.default_stack_start
        self.pc_step = self.isa_definition.word_size // 8
        self.regs = [Register(name=reg.name, alias=reg.alias, size=self.isa_definition.word_size) for reg in isa_definition.registers['general_purpose']]
        self.sp_index = next((i for i, reg in enumerate(self.regs) if reg.alias[0] == 'sp'), 0)
        self.regs[self.sp_index]._normalize(self.stack_start)
        self.key = "start"
        self.key_state = {}
        self.running = True
        self.PCrange = isa_definition.address_space.memory_layout["code_section"]["end"]

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
                    entry_point += code_size
                    data_start = data[20:24]
                    data_start = int.from_bytes(data_start, byteorder='little')
                    data_size = data[24:28]
                    data_size = int.from_bytes(data_size, byteorder='little')
                    self.memory[data_start:data_start + data_size] = data[entry_point:entry_point + data_size]
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
            print(f"Loaded {len(data)} bytes from '{filename}' into memory")
            return True
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            return False
    
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
        reg_aliases = [reg.alias[0] if hasattr(reg, 'alias') and reg.alias else str(reg) for reg in reg_objs]
        for operand in operands:
            if operand in reg_names:
                idx = reg_names.index(operand)
                pattern = f" {re.escape(operand)}"
                result = result.replace(pattern, f" regs[{idx}].value")
                result = result.replace(f"{operand} ", f"regs[{idx}].value ")
            elif operand in reg_aliases:
                idx = reg_aliases.index(operand)
                pattern = f" {re.escape(operand)}"
                result = result.replace(pattern, f" regs[{idx}].value")
                result = result.replace(f"{operand} ", f"regs[{idx}].value ")
            elif operand.endswith(' '):
                print(operand)
            else:
                continue
            
        result = result.replace("memory", "self.memory")
        result = result.replace("PC", "self.pc")
        return result        
    
    
    
    def map_disassembly_result_to_pc(self, disassembly_result: DisassemblyResult) -> Dict[int, DisassembledInstruction]:
        """Maps disassembled instructions to their program counter (PC) addresses"""
        pc_map = {}
        for instruction in disassembly_result.instructions:
            if instruction is not None:
                pc_map[instruction.address] = instruction
        return pc_map
    
    def print_registers(self):
        """Prints the current state of registers"""
        print(self.regs)
    
    
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
                    key_code = self.regs[6]  # Key code requested by user program
                    self.regs[7] = self.key_state.get(key_code, 0)
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
                exec(executable_string, {'regs': self.regs, 'memory': self.memory, 'self': self})
                return True
        return True
    
    def read_memory_byte(self, addr: int) -> int:
        if 0 <= addr < len(self.memory):
            return self.memory[addr]
        else:
            print(f"Warning: Attempted to read from invalid memory address 0x{addr:04X}")
            return 0

    def dump_memory(self, start: int, end: int):
        for addr in range(start, end + 1):
            print(f"0x{addr:04X}: {self.read_memory_byte(addr):02X}")
            

    ###################### GRAPHICS ######################
import pygame

# ========== Constants ==========
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
TILE_SIZE = 16
ROWS = SCREEN_HEIGHT // TILE_SIZE
COLS = SCREEN_WIDTH // TILE_SIZE

TILE_MAP_ADDR = 0xF000
TILE_DATA_ADDR = 0xF200
PALETTE_ADDR = 0xFA00

# ========== Palette Reader ==========
def get_palette(memory):
    palette = []
    for i in range(16):
        byte = memory[PALETTE_ADDR + i]
        r = ((byte >> 5) & 0b111) * 255 // 7
        g = ((byte >> 2) & 0b111) * 255 // 7
        b = (byte & 0b11) * 255 // 3
        palette.append((r, g, b))
    return palette

# ========== Tile Reader ==========
def get_tile(memory, tile_index):
    base = TILE_DATA_ADDR + tile_index * 128
    pixels = []
    for i in range(128):
        if base + i >= len(memory):
            pixels.append(0)  # default to color index 0 (black)
            pixels.append(0)
        else:
            byte = memory[base + i]
            pixels.append(byte & 0x0F)
            pixels.append((byte >> 4) & 0x0F)
    return pixels

# ========== Draw Screen ==========
def draw_screen(screen, memory):
    palette = get_palette(memory)
    for row in range(ROWS):
        for col in range(COLS):
            tile_index = memory[TILE_MAP_ADDR + row * COLS + col]
            tile_pixels = get_tile(memory, tile_index)
            for y in range(TILE_SIZE):
                for x in range(TILE_SIZE):
                    color_index = tile_pixels[y * TILE_SIZE + x]
                    color = palette[color_index]
                    screen.set_at((col * TILE_SIZE + x, row * TILE_SIZE + y), color)
    
def run_simulator_with_graphics(simulator, step=False):
    simulator.running = True

    # Init pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ZX16 Simulator + Graphics")
    clock = pygame.time.Clock()

    monitored_keys = {
        pygame.K_w: 0x77,         # 'w'
        pygame.K_s: 0x73,         # 's'
        pygame.K_UP: 0x26,        # up arrow
        pygame.K_DOWN: 0x28       # down arrow
    }
    simulator.key_state = {code: 0 for code in monitored_keys.values()}

    print(f"Code Start: {simulator.pc}")
    print(f"Data Start: {simulator.data_start}")

    instructions_map = simulator.map_disassembly_result_to_pc(
        simulator.disassembler.disassemble(simulator.memory, simulator.pc)
    )

    while simulator.pc < len(simulator.memory) and simulator.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                simulator.running = False
                pygame.quit()
                return

        # Update keys
        keys = pygame.key.get_pressed()
        for pygame_key, internal_code in monitored_keys.items():
            simulator.key_state[internal_code] = 1 if keys[pygame_key] else 0

        # Handle PC out of code bounds
        if simulator.pc >= simulator.PCrange:
            print(f"PC {simulator.pc:04X} out of memory bounds (max: {len(simulator.memory) - 1:04X})")
            break

        # Re-disassemble if needed
        if simulator.pc not in instructions_map:
            disassembly_result = simulator.disassembler.disassemble(simulator.memory, simulator.pc)
            instructions_map.update(simulator.map_disassembly_result_to_pc(disassembly_result))

        current_instruction = instructions_map.get(simulator.pc)
        if current_instruction is None or current_instruction.instruction is None:
            print(f"Skipping instruction at PC: {simulator.pc:04X} (no instruction found)")
            simulator.pc += simulator.pc_step
            continue

        # Print instruction
        print(f"PC: {simulator.pc:04X} - {current_instruction.instruction.mnemonic} {', '.join(current_instruction.operands)}")
        simulator.print_registers()

        # Execute instruction
        prev_pc = simulator.pc
        try:
            success = simulator.execute_instruction(current_instruction)
        except Exception as e:
            print(f"Error executing instruction at PC {simulator.pc:04X}: {e}")
            break

        if not success:
            print("Execution terminated by instruction.")
            break

        # If PC hasn't changed, increment
        if simulator.pc == prev_pc:
            simulator.pc += simulator.pc_step

        # Step mode
        if step:
            input("Press Enter to continue (or Ctrl+C to quit)...")

        draw_screen(screen, simulator.memory)
        pygame.display.flip()
        clock.tick(30)

    print("Simulation completed")
    simulator.dump_memory(0xFA00, 0xFA03)

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <machine_code_file>", file=sys.stderr)
        sys.exit(1)


    filename = sys.argv[1]
    print(f"Start: Loading {filename}")
    
    # Check if file exists
    if not Path(filename).exists():
        print(f"Error: File '{filename}' not found", file=sys.stderr)
        sys.exit(1)
    
    isa_loader = ISALoader()
    symbol_table = SymbolTable()
    disassembler = Disassembler(isa_loader.load_isa("zx16"), symbol_table)
    simulator = Simulator(isa_loader.load_isa("zx16"), symbol_table, disassembler)
    if not simulator.load_memory_from_file(filename):
        sys.exit(1)

    run_simulator_with_graphics(simulator)

    return 0


if __name__ == "__main__":
    main()