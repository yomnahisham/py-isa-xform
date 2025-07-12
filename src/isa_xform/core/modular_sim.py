import sys
import struct
import re
import numpy as np
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

def safe_int16(val):
    """Wraps to signed 16-bit using NumPy for safe overflow-tolerant math"""
    return np.array(val, dtype=np.uint16).view(np.int16)


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
        self.reg_names = [reg.alias[0] for reg in self.isa_definition.registers['general_purpose']]
        self.sp_index = self.reg_names.index('sp') if 'sp' in self.reg_names else -1
        self.regs = [safe_int16(0) for _ in range(len(self.isa_definition.registers['general_purpose']))]
        if self.sp_index != -1:
            self.regs[self.sp_index] = safe_int16(self.stack_start)
        self.key = "start"
        self.key_state = {}
        self.running = True
        self.PCrange = isa_definition.address_space.memory_layout["code_section"]["end"]

    def load_memory_from_file(self, filename: str) -> bool:
        if not Path(filename).exists():
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            return False
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                if len(data) > len(self.memory):
                    print(f"Error: File '{filename}' exceeds memory size", file=sys.stderr)
                    return False
                if self.isa_definition.endianness == 'little':
                    entry_point = int.from_bytes(data[8:12], byteorder='little')
                    code_start = int.from_bytes(data[12:16], byteorder='little')
                    code_size = int.from_bytes(data[16:20], byteorder='little')
                    self.memory[code_start:code_start + code_size] = data[entry_point:entry_point + code_size]
                    entry_point += code_size
                    data_start = int.from_bytes(data[20:24], byteorder='little')
                    data_size = int.from_bytes(data[24:28], byteorder='little')
                    self.memory[data_start:data_start + data_size] = data[entry_point:entry_point + data_size]
                else:
                    code_start = int.from_bytes(data[12:16], byteorder='big')
                    code_size = int.from_bytes(data[16:20], byteorder='big')
                    self.memory[self.pc:self.pc + code_size] = data[code_start:code_start + code_size]
                    data_start = int.from_bytes(data[20:24], byteorder='big')
                    data_size = int.from_bytes(data[24:28], byteorder='big')
                    self.memory[self.data_start:self.data_start + data_size] = data[data_start:data_start + data_size]
            print(f"Loaded {len(data)} bytes from '{filename}' into memory")
            return True
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            return False

    def extract_parameters(self, syntax: str) -> List[str]:
        parts = syntax.split()
        if len(parts) < 2:
            print(f"Error: Invalid syntax '{syntax}'", file=sys.stderr)
            return []
        operand_string = ' '.join(parts[1:])
        operands = re.findall(r'(?:0x[0-9a-fA-F]+|0b[01]+|0o[0-7]+|-?\d+|[a-zA-Z_]\w*)', operand_string)
        return operands

    def generic_to_register_name(self, syntax: str, generic: List[str], operands: List[str]) -> str:
        for g, o in zip(generic, operands):
            syntax = syntax.replace(g, o)
        return syntax

    def register_name_to_index(self, syntax: str, operands: List[str]) -> str:
        result = syntax
        reg_objs = self.isa_definition.registers['general_purpose']
        reg_names = [reg.name if hasattr(reg, 'name') else str(reg) for reg in reg_objs]
        reg_aliases = [reg.alias[0] if hasattr(reg, 'alias') and reg.alias else str(reg) for reg in reg_objs]

        for operand in operands:
            if operand in reg_names:
                idx = reg_names.index(operand)
                result = result.replace(operand, f"regs[{idx}]")
            elif operand in reg_aliases:
                idx = reg_aliases.index(operand)
                result = result.replace(operand, f"regs[{idx}]")

        result = result.replace("memory", "self.memory")
        result = result.replace("PC", "self.pc")
        result = result.replace("sign_extend", "safe_int16")
        result = result.replace("unsigned", "np.uint16")

        if '=' in result:
            lhs, rhs = result.split('=', 1)
            result = f"{lhs.strip()} = safe_int16({rhs.strip()})"

        return result

    def map_disassembly_result_to_pc(self, disassembly_result: DisassemblyResult) -> Dict[int, DisassembledInstruction]:
        return {i.address: i for i in disassembly_result.instructions if i is not None}

    def execute_instruction(self, disassembled_instruction: DisassembledInstruction) -> bool:
        if disassembled_instruction.instruction:
            if disassembled_instruction.instruction.mnemonic == "ECALL":
                code = f"0x{int(disassembled_instruction.operands[0]):03X}"
                name = self.isa_definition.ecall_services[code].name
                if name == "exit":
                    print("Exiting simulation")
                    return False
                elif name == "read_string":
                    addr = self.regs[6]
                    max_length = self.regs[7]
                    string = input()
                    if len(string) > max_length:
                        print(f"Input exceeds max length {max_length}")
                        return True
                    for i, c in enumerate(string):
                        if addr + i < len(self.memory):
                            self.write_memory_byte(addr + i, ord(c))
                    self.write_memory_byte(addr + len(string), 0)
                    self.regs[6] = safe_int16(len(string))
                elif name == "read_integer":
                    try:
                        self.regs[6] = safe_int16(int(input("Enter an integer: ")))
                    except ValueError:
                        print("Invalid input")
                elif name == "print_string":
                    addr = self.regs[6]
                    s = ""
                    while addr < len(self.memory) and self.memory[addr] != 0:
                        s += chr(self.memory[addr])
                        addr += 1
                    print(s)
                elif name == "print_int":
                    print(self.regs[6])
                elif name == "play_tone":
                    print(f"Playing tone {self.regs[6]}Hz for {self.regs[7]}ms")
                elif name == "set_audio_volume":
                    volume = self.regs[6]
                    if 0 <= volume <= 255:
                        print(f"Setting volume to {volume}")
                    else:
                        print("Volume out of range")
                elif name == "stop_audio_playback":
                    print("Audio stopped")
                elif name == "read_keyboard":
                    key_code = self.regs[6]
                    self.regs[7] = self.key_state.get(key_code, 0)
                elif name == "registers_dump":
                    for i, reg in enumerate(self.regs):
                        print(f"{self.reg_names[i]}: {reg}")
                elif name == "memory_dump":
                    start, end = self.regs[6], self.regs[7]
                    for addr in range(start, end + 1):
                        if addr < len(self.memory):
                            print(f"0x{addr:04X}: {self.read_memory_byte(addr)}")
                return True
            else:
                asm = disassembled_instruction.instruction
                generic = self.extract_parameters(asm.syntax)
                actual = self.extract_parameters(f"{asm.mnemonic}  {', '.join(disassembled_instruction.operands)}")
                transformed = self.generic_to_register_name(asm.semantics, generic, actual)
                executable = self.register_name_to_index(transformed, actual)
                print(f"Executing: {executable}")
                exec(executable, {
                    'regs': self.regs,
                    'memory': self.memory,
                    'self': self,
                    'np': np,
                    'safe_int16': safe_int16
                })
                return True
        return True

    def read_memory_byte(self, addr: int) -> int:
        if 0 <= addr < len(self.memory):
            return self.memory[addr]
        print(f"Warning: Invalid memory address 0x{addr:04X}")
        return 0

    def write_memory_byte(self, addr: int, value: int):
        if 0 <= addr < len(self.memory):
            self.memory[addr] = value & 0xFF

    def dump_memory(self, start: int, end: int):
        for addr in range(start, end + 1):
            print(f"0x{addr:04X}: {self.read_memory_byte(addr):02X}")


##### GRAPHICS ######################
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
    disassembly_result = simulator.disassembler.disassemble(simulator.memory, simulator.pc)
    instructions_map = simulator.map_disassembly_result_to_pc(disassembly_result)
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
    print(f"Data Start: {simulator.data_start} ")

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

        # Fetch and execute instruction
        if simulator.pc not in instructions_map:
            if simulator.pc >= simulator.PCrange:
                print(f"PC {simulator.pc:04X} out of memory bounds (max: {len(simulator.memory) - 1:04X})")
                simulator.running = False
                break
            else:
                print(f"Skipping instruction at PC: {simulator.pc:04X} (no instruction found)")
                simulator.pc += simulator.pc_step
                break
                continue

        current_instruction = instructions_map[simulator.pc]


        print(f"PC: {simulator.pc:04X} - {current_instruction.mnemonic} {', '.join(current_instruction.operands)}")
        temp_pc = simulator.pc

        if simulator.execute_instruction(current_instruction):
            if temp_pc == simulator.pc:
                simulator.pc += simulator.pc_step

            if "NOP" in current_instruction.mnemonic:
                break

            print(f"Registers: {simulator.regs}")

        else:
            print("Execution terminated by instruction")
            break

        draw_screen(screen, simulator.memory)
        pygame.display.flip()
        clock.tick(30)

    print("Simulation completed")
    simulator.dump_memory(0xF12C, 0xF12F)



