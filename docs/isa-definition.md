# ISA Definition Guide

This guide explains how to define custom instruction set architectures (ISAs) for use with py-isa-xform.

## Overview

An ISA definition is a JSON file that completely specifies an instruction set architecture. This includes:
- Basic architecture properties (word size, endianness)
- Register definitions
- Instruction specifications
- Pseudo-instructions
- Assembly syntax rules
- Constants and services

## ISA Definition Structure

### Basic Properties

```json
{
  "name": "ZX16",
  "version": "1.0",
  "description": "ZX16 16-bit RISC-V inspired ISA",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "address_space": {
    "size": 65536,
    "default_code_start": 32
  }
}
```

**Fields:**
- `name` - Unique identifier for the ISA
- `version` - Version string for compatibility tracking
- `description` - Human-readable description
- `instruction_size` - Size of instructions in bits
- `word_size` - Size of a word in bits (8, 16, 32, 64)
- `endianness` - Byte order ("little" or "big")
- `address_space` - Memory layout configuration

### Register Definitions

```json
{
  "registers": {
    "general_purpose": [
      {"name": "x0", "size": 16, "alias": ["t0"], "description": "Temporary (caller-saved)"},
      {"name": "x1", "size": 16, "alias": ["ra"], "description": "Return address"},
      {"name": "x2", "size": 16, "alias": ["sp"], "description": "Stack pointer"},
      {"name": "x3", "size": 16, "alias": ["s0"], "description": "Saved/Frame pointer"},
      {"name": "x4", "size": 16, "alias": ["s1"], "description": "Saved"},
      {"name": "x5", "size": 16, "alias": ["t1"], "description": "Temporary (caller-saved)"},
      {"name": "x6", "size": 16, "alias": ["a0"], "description": "Argument 0/Return value"},
      {"name": "x7", "size": 16, "alias": ["a1"], "description": "Argument 1"}
    ]
  }
}
```

**Register Fields:**
- `name` - Primary register name
- `size` - Register size in bits
- `alias` - Alternative names for the register
- `description` - Human-readable description

### Instruction Definitions

Instructions are the heart of the ISA definition:

```json
{
  "instructions": [
    {
      "mnemonic": "ADD",
      "format": "R-type",
      "description": "Add registers (two-operand)",
      "syntax": "ADD rd, rs2",
      "semantics": "rd = rd + rs2",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "rs2", "bits": "11:9", "type": "register"},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "000"}
        ]
      }
    },
    {
      "mnemonic": "ADDI",
      "format": "I-type",
      "description": "Add immediate",
      "syntax": "ADDI rd, imm",
      "semantics": "rd = rd + imm",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "imm", "bits": "11:9", "type": "immediate", "signed": true},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "001"}
        ]
      }
    }
  ]
}
```

**Instruction Fields:**
- `mnemonic` - Assembly language name
- `format` - Instruction format type (R-type, I-type, J-type, etc.)
- `description` - Human-readable description
- `syntax` - Assembly syntax pattern
- `semantics` - Operational description
- `encoding` - Bit-level encoding specification

### Encoding Field Types

1. **Fixed Value Field**
   ```json
   {"name": "funct4", "bits": "15:12", "value": "0000"}
   ```

2. **Register Field**
   ```json
   {"name": "rd", "bits": "8:6", "type": "register"}
   ```

3. **Immediate Field**
   ```json
   {"name": "imm", "bits": "11:9", "type": "immediate", "signed": true}
   ```

4. **Address Field**
   ```json
   {"name": "address", "bits": "11:0", "type": "address"}
   ```

### Pseudo-Instructions

Define macro-like instructions that expand to real instructions:

```json
{
  "pseudo_instructions": [
    {
      "mnemonic": "NOP",
      "description": "No operation",
      "syntax": "NOP",
      "expansion": "ADD x0, x0"
    },
    {
      "mnemonic": "CLR",
      "description": "Clear register",
      "syntax": "CLR rd",
      "expansion": "XOR rd, rd"
    },
    {
      "mnemonic": "INC",
      "description": "Increment register",
      "syntax": "INC rd",
      "expansion": "ADDI rd, 1"
    },
    {
      "mnemonic": "DEC",
      "description": "Decrement register",
      "syntax": "DEC rd",
      "expansion": "ADDI rd, -1"
    },
    {
      "mnemonic": "CALL",
      "description": "Call function",
      "syntax": "CALL label",
      "expansion": "JAL x1, label"
    },
    {
      "mnemonic": "RET",
      "description": "Return from function",
      "syntax": "RET",
      "expansion": "JR x1"
    }
  ]
}
```

### Assembly Syntax Rules

```json
{
  "assembly_syntax": {
    "comment_chars": ["#", ";"],
    "label_suffix": ":",
    "register_prefix": "",
    "immediate_prefix": "",
    "string_delimiters": ["\"", "'"],
    "case_sensitive": false,
    "instruction_separator": "\n"
  }
}
```

### Constants

Define system constants and memory layout:

```json
{
  "constants": {
    "RESET_VECTOR": 0,
    "INT_VECTORS": 0,
    "CODE_START": 32,
    "MMIO_BASE": 61440,
    "MMIO_SIZE": 4096,
    "STACK_TOP": 61438,
    "MEM_SIZE": 65536
  }
}
```

### ECALL Services

Define system call services:

```json
{
  "ecall_services": {
    "0x000": {
      "name": "print_char",
      "description": "Print character from a0 register",
      "parameters": {
        "a0": "Character to print"
      },
      "return": "None"
    },
    "0x001": {
      "name": "read_char",
      "description": "Read a character from user input into a0 register",
      "parameters": {},
      "return": "a0: Character read from input"
    },
    "0x002": {
      "name": "print_string",
      "description": "Print string starting at address in a0 register",
      "parameters": {
        "a0": "Address of null-terminated string"
      },
      "return": "None"
    },
    "0x3FF": {
      "name": "exit",
      "description": "Exit program with code in a0 register",
      "parameters": {
        "a0": "Exit code"
      },
      "return": "None"
    }
  }
}
```

## Complete Example: ZX16 ISA

```json
{
  "name": "ZX16",
  "version": "1.0",
  "description": "ZX16 16-bit RISC-V inspired ISA",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "address_space": {
    "size": 65536,
    "default_code_start": 32
  },
  
  "registers": {
    "general_purpose": [
      {"name": "x0", "size": 16, "alias": ["t0"], "description": "Temporary (caller-saved)"},
      {"name": "x1", "size": 16, "alias": ["ra"], "description": "Return address"},
      {"name": "x2", "size": 16, "alias": ["sp"], "description": "Stack pointer"},
      {"name": "x3", "size": 16, "alias": ["s0"], "description": "Saved/Frame pointer"},
      {"name": "x4", "size": 16, "alias": ["s1"], "description": "Saved"},
      {"name": "x5", "size": 16, "alias": ["t1"], "description": "Temporary (caller-saved)"},
      {"name": "x6", "size": 16, "alias": ["a0"], "description": "Argument 0/Return value"},
      {"name": "x7", "size": 16, "alias": ["a1"], "description": "Argument 1"}
    ]
  },
  
  "instructions": [
    {
      "mnemonic": "ADD",
      "format": "R-type",
      "description": "Add registers (two-operand)",
      "syntax": "ADD rd, rs2",
      "semantics": "rd = rd + rs2",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "rs2", "bits": "11:9", "type": "register"},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "000"}
        ]
      }
    },
    {
      "mnemonic": "ADDI",
      "format": "I-type",
      "description": "Add immediate",
      "syntax": "ADDI rd, imm",
      "semantics": "rd = rd + imm",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "imm", "bits": "11:9", "type": "immediate", "signed": true},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "001"}
        ]
      }
    }
  ],
  
  "pseudo_instructions": [
    {
      "mnemonic": "NOP",
      "description": "No operation",
      "syntax": "NOP",
      "expansion": "ADD x0, x0"
    },
    {
      "mnemonic": "CALL",
      "description": "Call function",
      "syntax": "CALL label",
      "expansion": "JAL x1, label"
    }
  ],
  
  "assembly_syntax": {
    "comment_chars": ["#", ";"],
    "label_suffix": ":",
    "register_prefix": "",
    "immediate_prefix": "",
    "string_delimiters": ["\"", "'"],
    "case_sensitive": false,
    "instruction_separator": "\n"
  },
  
  "constants": {
    "RESET_VECTOR": 0,
    "CODE_START": 32,
    "MMIO_BASE": 61440,
    "STACK_TOP": 61438,
    "MEM_SIZE": 65536
  },
  
  "ecall_services": {
    "0x000": {
      "name": "print_char",
      "description": "Print character from a0 register",
      "parameters": {
        "a0": "Character to print"
      },
      "return": "None"
    },
    "0x3FF": {
      "name": "exit",
      "description": "Exit program with code in a0 register",
      "parameters": {
        "a0": "Exit code"
      },
      "return": "None"
    }
  }
}
```

## Validation Rules

The ISA definition must satisfy several validation rules:

1. **Opcode Uniqueness** - Each instruction must have a unique encoding pattern
2. **Bit Field Coverage** - All instruction bits must be accounted for
3. **Register Consistency** - Register references must match definitions
4. **Syntax Consistency** - Assembly syntax must be unambiguous
5. **Encoding Completeness** - All instruction fields must be properly defined

## Best Practices

1. **Start Simple** - Begin with a minimal instruction set
2. **Document Thoroughly** - Use descriptive names and comments
3. **Test Early** - Validate your ISA definition frequently
4. **Be Consistent** - Use consistent naming conventions
5. **Plan for Growth** - Leave room for future extensions

## Common Pitfalls

1. **Overlapping Encodings** - Make sure instruction encodings are unique
2. **Incomplete Bit Fields** - All bits must be defined
3. **Register Conflicts** - Avoid conflicting register names
4. **Syntax Ambiguity** - Ensure assembly syntax is unambiguous
5. **Missing Dependencies** - Define all referenced components 