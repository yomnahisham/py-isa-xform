"""
ZX16 Instruction Set Simulator (ISS) with Advanced Disassembly

This simulator accepts a ZX16 binary machine code file and executes it
by simulating the 16-bit RISC-V inspired processor architecture.
"""

import sys
import struct
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .disassembler import Disassembler, DisassembledInstruction
from .isa_loader import ISADefinition, Instruction
from .symbol_table import SymbolTable

class ZX16Simulator:
    def __init__(self):
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
        self._setup_disassembler()
        
    def _setup_disassembler(self):
        """Setup the advanced disassembler with ZX16 ISA definition"""
        # Create ZX16 ISA definition
        zx16_isa = self._create_zx16_isa_definition()
        
        # Initialize symbol table
        self.symbol_table = SymbolTable()
        
        # Create disassembler instance
        self.disassembler = Disassembler(zx16_isa, self.symbol_table)


    def _create_zx16_isa_definition(self) -> ISADefinition:
        """Create ISA definition for ZX16 architecture"""
        
        name = "ZX16"
        version = "1.0"
        description = "ZX16 16-bit RISC-V inspired processor"
        instruction_size = 16
        word_size = 16
        endianness = "little"
        
        # Define ZX16 registers
        registers = {
            "general": [
                {"name": "t0", "index": 0},
                {"name": "ra", "index": 1},
                {"name": "sp", "index": 2},
                {"name": "s0", "index": 3},
                {"name": "s1", "index": 4},
                {"name": "t1", "index": 5},
                {"name": "a0", "index": 6},
                {"name": "a1", "index": 7}
            ]
        }
        
        # Define ZX16 instructions with encoding patterns
        instructions = self._create_zx16_instructions()
        
        # Create ISA definition with named arguments to ensure correct order
        isa_def = ISADefinition(
            name=name,
            version=version,
            description=description,
            word_size=word_size,
            endianness=endianness,
            instruction_size=instruction_size,
            registers=registers,
            instructions=instructions
        )
            
        return isa_def


    def _create_zx16_instructions(self) -> List[Instruction]:
        """Create instruction definitions for ZX16"""
        instructions = []
        
        # R-type instructions
        r_type_instructions = [
        ("ADD", 0x0, 0x0, 0x0, "add rd, rs2"),
        ("SUB", 0x1, 0x0, 0x0, "sub rd, rs2"),
        ("SLT", 0x2, 0x1, 0x0, "slt rd, rs2"),
        ("SLTU", 0x3, 0x2, 0x0, "sltu rd, rs2"),
        ("SLL", 0x4, 0x3, 0x0, "sll rd, rs2"),
        ("SRL", 0x5, 0x3, 0x0, "srl rd, rs2"),
        ("SRA", 0x6, 0x3, 0x0, "sra rd, rs2"),
        ("OR", 0x7, 0x4, 0x0, "or rd, rs2"),
        ("AND", 0x8, 0x5, 0x0, "and rd, rs2"),
        ("XOR", 0x9, 0x6, 0x0, "xor rd, rs2"),
        ("MV", 0xA, 0x7, 0x0, "mv rd, rs2"),
        ("JR", 0xB, 0x0, 0x0, "jr rd"),
        ("JALR", 0xC, 0x0, 0x0, "jalr rd, rs2"),]
        
        for mnemonic, funct4, funct3, opcode, syntax in r_type_instructions:
            encoding = {
            "fields": [
                {"name": "funct4", "bits": "15:12", "value": f"0b{funct4:04b}"},
                {"name": "rd", "bits": "8:6", "type": "register"},        # PUT RD FIRST
                {"name": "rs2", "bits": "11:9", "type": "register"},      # PUT RS2 SECOND
                {"name": "funct3", "bits": "5:3", "value": f"0b{funct3:03b}"},
                {"name": "opcode", "bits": "2:0", "value": f"0b{opcode:03b}"}
            ]
        }
            description = f"{mnemonic} instruction"
            semantics = f"Performs {mnemonic.lower()} operation on rd and rs2"
            format_type = "R-type"
            
            # Create Instruction with all required arguments
            instr = Instruction(
                mnemonic=mnemonic,
                opcode=opcode,
                format=format_type,
                description=description,
                encoding=encoding,
                syntax=syntax,
                semantics=semantics
            )
            instructions.append(instr)
            
        # I-type instructions
        i_type_instructions = [
            ("ADDI", 0x0, 0x1, "addi rd, imm"),
            ("SLTI", 0x1, 0x1, "slti rd, imm"),
            ("SLTUI", 0x2, 0x1, "sltui rd, imm"),
            ("ORI", 0x4, 0x1, "ori rd, imm"),
            ("ANDI", 0x5, 0x1, "andi rd, imm"),
            ("XORI", 0x6, 0x1, "xori rd, imm"),
            ("LI", 0x7, 0x1, "li rd, imm"),
        ]
        
        for mnemonic, funct3, opcode, syntax in i_type_instructions:
            encoding = {
                "fields": [
                    {"name": "rd", "bits": "8:6", "type": "register"},            # PUT RD FIRST
                    {"name": "imm", "bits": "15:9", "type": "immediate", "signed": True},  # PUT IMM SECOND
                    {"name": "funct3", "bits": "5:3", "value": f"0b{funct3:03b}"},
                    {"name": "opcode", "bits": "2:0", "value": f"0b{opcode:03b}"}
                ]
            }
            description = f"{mnemonic} instruction"
            semantics = f"Performs {mnemonic.lower()} operation with immediate value"
            format_type = "I-type"
            
            # Create Instruction with all required arguments
            instr = Instruction(
                mnemonic=mnemonic,
                opcode=opcode,
                format=format_type,
                description=description,
                encoding=encoding,
                syntax=syntax,
                semantics=semantics
            )
            instructions.append(instr)
        return instructions

    
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
                print("DONE")
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
    
    def sign_extend(self, value: int, bits: int) -> int:
        """Sign extend a value from specified number of bits to 16 bits"""
        if value & (1 << (bits - 1)):
            return value | (0xFFFF << bits)
        return value & ((1 << bits) - 1)
    
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
                self.regs[rd] = (self.regs[rd] + self.regs[rs2]) & 0xFFFF
            elif funct4 == 0x1 and funct3 == 0x0:  # SUB
                self.regs[rd] = (self.regs[rd] - self.regs[rs2]) & 0xFFFF
            elif funct4 == 0x2 and funct3 == 0x1:  # SLT
                self.regs[rd] = 1 if self.sign_extend(self.regs[rd], 16) < self.sign_extend(self.regs[rs2], 16) else 0
            elif funct4 == 0x3 and funct3 == 0x2:  # SLTU
                self.regs[rd] = 1 if self.regs[rd] < self.regs[rs2] else 0
            elif funct4 == 0x4 and funct3 == 0x3:  # SLL
                shift = self.regs[rs2] & 0xF
                self.regs[rd] = (self.regs[rd] << shift) & 0xFFFF
            elif funct4 == 0x5 and funct3 == 0x3:  # SRL
                shift = self.regs[rs2] & 0xF
                self.regs[rd] = self.regs[rd] >> shift
            elif funct4 == 0x6 and funct3 == 0x3:  # SRA
                shift = self.regs[rs2] & 0xF
                val = self.sign_extend(self.regs[rd], 16)
                self.regs[rd] = (val >> shift) & 0xFFFF
            elif funct4 == 0x7 and funct3 == 0x4:  # OR
                self.regs[rd] = (self.regs[rd] | self.regs[rs2]) & 0xFFFF
            elif funct4 == 0x8 and funct3 == 0x5:  # AND
                self.regs[rd] = (self.regs[rd] & self.regs[rs2]) & 0xFFFF
            elif funct4 == 0x9 and funct3 == 0x6:  # XOR
                self.regs[rd] = (self.regs[rd] ^ self.regs[rs2]) & 0xFFFF
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
                self.regs[rd] = (self.regs[rd] + simm) & 0xFFFF
            elif funct3 == 0x1:  # SLTI
                self.regs[rd] = 1 if self.sign_extend(self.regs[rd], 16) < simm else 0
            elif funct3 == 0x2:  # SLTUI
                self.regs[rd] = 1 if self.regs[rd] < (simm & 0xFFFF) else 0
            elif funct3 == 0x3:  # SLLI/SRLI/SRAI
                shift = imm & 0xF
                if (imm >> 6) == 0:  # SLLI
                    self.regs[rd] = (self.regs[rd] << shift) & 0xFFFF
                elif (imm >> 6) == 1:  # SRLI
                    self.regs[rd] = self.regs[rd] >> shift
                else:  # SRAI
                    val = self.sign_extend(self.regs[rd], 16)
                    self.regs[rd] = (val >> shift) & 0xFFFF
            elif funct3 == 0x4:  # ORI
                self.regs[rd] = (self.regs[rd] | simm) & 0xFFFF
            elif funct3 == 0x5:  # ANDI
                self.regs[rd] = (self.regs[rd] & simm) & 0xFFFF
            elif funct3 == 0x6:  # XORI
                self.regs[rd] = (self.regs[rd] ^ simm) & 0xFFFF
            elif funct3 == 0x7:  # LI
                self.regs[rd] = simm & 0xFFFF
                
        elif opcode == 0x2:  # B-type
            imm = (inst >> 12) & 0xF
            rs2 = (inst >> 9) & 0x7
            rs1 = (inst >> 6) & 0x7
            funct3 = (inst >> 3) & 0x7
            offset = self.sign_extend(imm, 4) * 2
            
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
                self.pc = (self.pc + offset) & 0xFFFF
                pc_updated = True
                
        elif opcode == 0x3:  # S-type (Store)
            imm = (inst >> 12) & 0xF
            rs2 = (inst >> 9) & 0x7
            rs1 = (inst >> 6) & 0x7
            funct3 = (inst >> 3) & 0x7
            offset = self.sign_extend(imm, 4)
            address = (self.regs[rs1] + offset) & 0xFFFF
            
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
            address = (self.regs[rs2] + offset) & 0xFFFF
            
            if funct3 == 0x0:  # LB
                val = self.read_memory_byte(address)
                self.regs[rd] = self.sign_extend(val, 8) & 0xFFFF
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
                self.pc = (self.pc + offset) & 0xFFFF
            else:  # JAL
                self.regs[rd] = (self.pc + 2) & 0xFFFF
                self.pc = (self.pc + offset) & 0xFFFF
            pc_updated = True
            
        elif opcode == 0x6:  # U-type
            flag = (inst >> 15) & 0x1
            imm1 = (inst >> 9) & 0x3F
            rd = (inst >> 6) & 0x7
            imm2 = (inst >> 3) & 0x7
            
            # Combine immediate fields
            imm = (imm1 << 3) | imm2
            
            if flag == 0:  # LUI
                self.regs[rd] = (imm << 7) & 0xFFFF
            else:  # AUIPC
                self.regs[rd] = (self.pc + (imm << 7)) & 0xFFFF
                
        elif opcode == 0x7:  # System (ECALL)
            svc = (inst >> 6) & 0x3FF
            
            if svc == 1:  # Print integer
                print(self.regs[6], end='')  # a0 register
            elif svc == 5:  # Print string
                addr = self.regs[6]  # a0 register
                while addr < len(self.memory) and self.memory[addr] != 0:
                    print(chr(self.memory[addr]), end='')
                    addr += 1
            elif svc == 3:  # Terminate
                return False
        
        if not pc_updated:
            self.pc = (self.pc + 2) & 0xFFFF
            
        return True
    
    def run(self) -> None:
        """Main simulation loop"""
        instruction_count = 0
        max_instructions = 1000000  # Prevent infinite loops
        
        while instruction_count < max_instructions:
            if self.pc >= len(self.memory) - 1:
                print("Program counter out of bounds")
                break
                
            inst = self.fetch_instruction()
            if inst == 0:
                print("Encountered null instruction, terminating")
                break
                
            if not self.execute_instruction(inst):
                print("Program terminated by ECALL")
                break
                
            instruction_count += 1
        
        if instruction_count >= max_instructions:
            print("Maximum instruction limit reached")

