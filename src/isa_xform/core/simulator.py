"""
ZX16 Instruction Set Simulator (ISS) with Advanced Disassembly

This simulator accepts a ZX16 binary machine code file and executes it
by simulating the 16-bit RISC-V inspired processor architecture.
"""

import sys
import struct
import keyboard
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .disassembler import Disassembler, DisassembledInstruction
from .isa_loader import ISADefinition, Instruction
from .symbol_table import SymbolTable

class ZX16Simulator:
    def __init__(self, disassembler: Disassembler):
        # Memory: 64KB (65536 bytes)
        self.memory = bytearray(65536)
        
        # Registers: 8 x 16-bit registers
        self.regs = [0] * 8

        
        # Program counter
        self.pc = 0
        
        # Register names for debugging
        self.reg_names = ["t0", "ra", "sp", "s0", "s1", "t1", "a0", "a1"]
        
        # Initialize stack pointer
        self.regs[2] = 61438  # STACK_TOP

        # Initialize the advanced disassembler
        self.disassembler = disassembler

    
    def load_memory_from_file(self, filename: str) -> None:
        """Load binary machine code file into memory"""
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                if len(data) > len(self.memory):
                    raise ValueError("Binary file too large for memory")
                
                for i, byte in enumerate(data):
                    if i < len(self.memory):
                        self.memory[i] = byte
                
                print(f"Loaded {len(data)} bytes into memory")
                return data
                
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error loading file: {e}", file=sys.stderr)
            sys.exit(1)
        
    
    def disassemble_instruction(self, inst: int, pc: int) -> str:
        """Use the advanced disassembler to disassemble instruction"""
        try:
            # Convert instruction to bytes (little-endian)
            inst_bytes = struct.pack('<H', inst)
            
            # Use the advanced disassembler
            result = self.disassembler.disassemble(inst_bytes, pc)
            
            if result.instructions:
                disasm_instr = result.instructions[0]
                if disasm_instr.operands:
                    return f"{disasm_instr.mnemonic} {', '.join(disasm_instr.operands)}"
                else:
                    return disasm_instr.mnemonic
            else:
                return f"unknown (0x{inst:04X})"
                
        except Exception as e:
            return

    
    def fetch_instruction(self) -> int:
        """Fetch 16-bit instruction from memory"""
        if self.pc >= len(self.memory) - 1:
            return 0
        return self.memory[self.pc] | (self.memory[self.pc + 1] << 8)
    
    def read_memory_byte(self, address: int) -> int:
        """Read a byte from memory at specified address"""
        if address < 0 or address >= len(self.memory):
            raise ValueError("Memory address out of bounds")
        return self.memory[address]
    
    def write_memory_byte(self, address: int, value: int) -> None:
        """Write a byte to memory at specified address"""
        if address < 0 or address >= len(self.memory):
            raise ValueError("Memory address out of bounds")
        self.memory[address] = value & 0xFF

    def read_memory_word(self, address: int) -> int:
        """Read a 16-bit word from memory at specified address"""
        if address < 0 or address >= len(self.memory) - 1:
            raise ValueError("Memory address out of bounds")
        return self.memory[address] | (self.memory[address + 1] << 8)
    
    def write_memory_word(self, address: int, value: int) -> None:
        """Write a 16-bit word to memory at specified address"""
        if address < 0 or address >= len(self.memory) - 1:
            raise ValueError("Memory address out of bounds")
        self.memory[address] = value
        self.memory[address + 1] = (value >> 8)

    def sign_extend(self, value: int, bits: int) -> int:
        """Sign extend a value from specified number of bits to 16 bits"""
        if value & (1 << (bits - 1)):
            mask = (1 << bits) - 1
            return value | (~mask)
        return value & ((1 << bits) - 1)
    
    def keyboard_press(self, event):
        """Handle keyboard press events"""
        return event.scan_code

    
    def execute_instruction(self, inst: int) -> bool:
        """Execute instruction and return True to continue, False to halt"""
        opcode = inst & 0x7
        pc_updated = False
        
        if opcode == 0x0:  # R-type
            funct4 = (inst >> 12) & 0xF
            rs2 = (inst >> 9) & 0x7
            rd = (inst >> 6) & 0x7
            funct3 = (inst >> 3) & 0x7
            
            if funct4 == 0x0 and funct3 == 0x0:  # ADD
                self.regs[rd] = (self.regs[rd] + self.regs[rs2])
            elif funct4 == 0x1 and funct3 == 0x0:  # SUB
                self.regs[rd] = (self.regs[rd] - self.regs[rs2])
            elif funct4 == 0x2 and funct3 == 0x1:  # SLT
                self.regs[rd] = 1 if self.sign_extend(self.regs[rd], 16) < self.sign_extend(self.regs[rs2], 16) else 0
            elif funct4 == 0x3 and funct3 == 0x2:  # SLTU
                self.regs[rd] = 1 if self.regs[rd] < self.regs[rs2] else 0
            elif funct4 == 0x4 and funct3 == 0x3:  # SLL
                shift = self.regs[rs2] & 0xF
                self.regs[rd] = (self.regs[rd] << shift)
            elif funct4 == 0x5 and funct3 == 0x3:  # SRL
                shift = self.regs[rs2] & 0xF
                self.regs[rd] = self.regs[rd] >> shift
            elif funct4 == 0x6 and funct3 == 0x3:  # SRA
                shift = self.regs[rs2] & 0xF
                val = self.sign_extend(self.regs[rd], 16)
                self.regs[rd] = (val >> shift)
            elif funct4 == 0x7 and funct3 == 0x4:  # OR
                self.regs[rd] = (self.sign_extend(self.regs[rd], 16) | self.sign_extend(self.regs[rs2], 16))
            elif funct4 == 0x8 and funct3 == 0x5:  # AND
                self.regs[rd] = (self.sign_extend(self.regs[rd], 16) & self.sign_extend(self.regs[rs2], 16))
            elif funct4 == 0x9 and funct3 == 0x6:  # XOR
                self.regs[rd] = (self.sign_extend(self.regs[rd], 16) ^ self.sign_extend(self.regs[rs2], 16))
            elif funct4 == 0xA and funct3 == 0x7:  # MV
                self.regs[rd] = self.regs[rs2]
            elif funct4 == 0xB and funct3 == 0x0:  # JR
                self.pc = self.regs[rd]
                pc_updated = True
            elif funct4 == 0xC and funct3 == 0x0:  # JALR
                temp = self.pc + 2
                self.pc = self.regs[rs2]
                self.regs[rd] = temp
                pc_updated = True
                
        elif opcode == 0x1:  # I-type
            imm = (inst >> 9) & 0x7F
            rd = (inst >> 6) & 0x7
            funct3 = (inst >> 3) & 0x7
            simm = self.sign_extend(imm, 7)
            
            if funct3 == 0x0:  # ADDI
                self.regs[rd] = (self.regs[rd] + simm)
            elif funct3 == 0x1:  # SLTI
                self.regs[rd] = 1 if self.sign_extend(self.regs[rd], 16) < simm else 0
            elif funct3 == 0x2:  # SLTUI
                self.regs[rd] = 1 if self.regs[rd] < (simm) else 0
            elif funct3 == 0x3:  # SLLI/SRLI/SRAI
                shift = imm & 0xF
                if (imm >> 6) == 0:  # SLLI
                    self.regs[rd] = (self.regs[rd] << shift) 
                elif (imm >> 6) == 1:  # SRLI
                    self.regs[rd] = self.regs[rd] >> shift
                else:  # SRAI
                    val = self.sign_extend(self.regs[rd], 16)
                    self.regs[rd] = (val >> shift) 
            elif funct3 == 0x4:  # ORI
                self.regs[rd] = (self.regs[rd] | simm)
            elif funct3 == 0x5:  # ANDI
                self.regs[rd] = (self.regs[rd] & simm)
            elif funct3 == 0x6:  # XORI
                self.regs[rd] = (self.regs[rd] ^ simm)
            elif funct3 == 0x7:  # LI
                print(simm)
                self.regs[rd] = simm
                
        elif opcode == 0x2:  # B-type
            imm = (inst >> 12) & 0xF
            rs2 = (inst >> 9) & 0x7
            rs1 = (inst >> 6) & 0x7
            funct3 = (inst >> 3) & 0x7
            offset = self.sign_extend(imm, 4)
            
            branch_taken = False
            if funct3 == 0x0:  # BEQ
                branch_taken = self.regs[rs1] == self.regs[rs2]
            elif funct3 == 0x1:  # BNE
                branch_taken = self.regs[rs1] != self.regs[rs2]
            elif funct3 == 0x2:  # BZ
                branch_taken = self.regs[rs1] == 0
            elif funct3 == 0x3:  # BNZ
                branch_taken = self.regs[rs1] != 0
            elif funct3 == 0x4:  # BLT
                branch_taken = self.sign_extend(self.regs[rs1], 16) < self.sign_extend(self.regs[rs2], 16)
            elif funct3 == 0x5:  # BGE
                branch_taken = self.sign_extend(self.regs[rs1], 16) >= self.sign_extend(self.regs[rs2], 16)
            elif funct3 == 0x6:  # BLTU
                branch_taken = self.regs[rs1] < self.regs[rs2]
            elif funct3 == 0x7:  # BGEU
                branch_taken = self.regs[rs1] >= self.regs[rs2]
            
            if branch_taken:
                self.pc = (self.pc + offset)
                pc_updated = True
                
        elif opcode == 0x3:  # S-type (Store)
            imm = (inst >> 12) & 0xF
            rs2 = (inst >> 9) & 0x7
            rs1 = (inst >> 6) & 0x7
            funct3 = (inst >> 3) & 0x7
            offset = self.sign_extend(imm, 4)
            address = (self.regs[rs1] + offset)
            
            if funct3 == 0x0:  # SB
                self.write_memory_byte(address, self.regs[rs2])
            elif funct3 == 0x1:  # SW
                self.write_memory_word(address, self.regs[rs2])
                
        elif opcode == 0x4:  # L-type (Load)
            imm = (inst >> 12) & 0xF
            rs2 = (inst >> 9) & 0x7
            rd = (inst >> 6) & 0x7
            funct3 = (inst >> 3) & 0x7
            offset = self.sign_extend(imm, 4)
            address = (self.regs[rs2] + offset)
            
            if funct3 == 0x0:  # LB
                val = self.read_memory_byte(address)
                self.regs[rd] = self.sign_extend(val, 8)
            elif funct3 == 0x1:  # LW
                self.regs[rd] = self.read_memory_word(address)
            elif funct3 == 0x4:  # LBU
                self.regs[rd] = self.read_memory_byte(address)
                
        elif opcode == 0x5:  # J-type
            link = (inst >> 15) & 0x1
            imm1 = (inst >> 9) & 0x3F
            rd = (inst >> 6) & 0x7
            imm2 = (inst >> 3) & 0x7
            
            # Combine immediate fields
            offset = self.sign_extend((imm1 << 3) | imm2, 9) * 2
            
            if link == 0:  # J
                self.pc = (self.pc + offset)
            else:  # JAL
                self.regs[rd] = (self.pc + 2)
                self.pc = (self.pc + offset)
            pc_updated = True
            
        elif opcode == 0x6:  # U-type
            flag = (inst >> 15) & 0x1
            imm1 = (inst >> 9) & 0x3F
            rd = (inst >> 6) & 0x7
            imm2 = (inst >> 3) & 0x7
            
            # Combine immediate fields
            imm = (imm1 << 3) | imm2
            
            if flag == 0:  # LUI
                self.regs[rd] = (imm << 7)
            else:  # AUIPC
                self.regs[rd] = (self.pc + (imm << 7))
                
        elif opcode == 0x7:  # System (ECALL)
            svc = (inst >> 6) & 0x3FF
            if svc == 1: # Read string
                addr = self.regs[6]  # a0 register
                max_length = self.regs[7]  # a1 register
                string = input("Enter a string: ")
                if len(string) > max_length:
                    print(f"Input exceeds maximum length of {max_length} characters")
                    return True
                for i, char in enumerate(string):
                    if addr + i < len(self.memory):
                        self.write_memory_byte(addr + i, ord(char))
                self.write_memory_byte(addr + len(string), 0)  # Null-terminate the string
                self.regs[6] = len(string)  # Store length in a0 register
            elif svc == 0x2:  # Read integer
                try:
                    value = int(input("Enter an integer: "))
                    self.regs[6] = value  # Store in a0 register
                except ValueError:
                    print("Invalid input, expected an integer")
            elif svc == 0x3:  # Print string
                addr = self.regs[6]  # a0 register
                string = ""
                while addr < len(self.memory) and self.memory[addr] != 0:
                    string += chr(self.memory[addr])
                    addr += 1
                print("Print: " + string)
            elif svc == 0x4:  # Play tone
                frequency = self.regs[6]  # a0 register
                duration_ms = self.regs[7]  # a1 register
                print(f"Playing tone at {frequency}Hz for {duration_ms}ms")
            elif svc == 0x5:  # Set audio volume
                volume = self.regs[6]  # a0 register
                if 0 <= volume <= 255:
                    print(f"Setting audio volume to {volume}")
                else:
                    print("Volume must be between 0 and 255")
            elif svc == 0x6:  # Stop audio playback
                print("Audio playback stopped")
            elif svc == 0x7:  # Read keyboard
                key = keyboard.on_press(self.keyboard_press)
                self.regs[6] = key  # Store key name in a0 register
                print(f"Key pressed: {key}")
            elif svc == 0x8:  #  Registers dump
                print("Register dump:")
                for i, reg in enumerate(self.regs):
                    print(f"{self.reg_names[i]}: {reg}")
            elif svc == 0x9:  # Memory dump
                start = self.regs[6]  # a0 register
                end = self.regs[7]  # a1 register
                print("Memory dump:")
                for addr in range(start, end + 1):
                    if addr < len(self.memory):
                        print(f"0x{addr:04X}: {self.read_memory_byte(addr)}")
            elif svc == 0xA:  # Terminate
                print("Program Terminated")
                return False
        
        if not pc_updated:
            self.pc = (self.pc + 2)
            
        return True
    
    def run(self) -> None:
        key = "c"
        instruction_count = 0
        while self.pc < len(self.memory) and instruction_count < 1000 and key != "q":  # Add safety limit
            # Fetch a 16-bit instruction from memory (little-endian)
            inst = self.memory[self.pc] | (self.memory[self.pc + 1] << 8)
            
            # Skip if instruction is 0 (might indicate end of program)
            if inst == 0:
                print(f"Encountered null instruction at 0x{self.pc:04X}, stopping")
                break
            
            # Use advanced disassembler
            disasm = self.disassemble_instruction(inst, self.pc)
            print(f"0x{self.pc:04X}: {inst} {disasm}")
            
            # Execute instruction
            if not self.execute_instruction(inst):
                print("Execution terminated by instruction")
                break
                
            instruction_count += 1
            
            # Terminate if PC goes out of bounds
            if self.pc >= len(self.memory):
                print("PC out of bounds, stopping")
                break
            print(f"Registers: {self.regs}") 
            # for num in self.regs:
            #     print(bin(num))
            q = input()

        print(f"Execution completed after {instruction_count} instructions")
        

