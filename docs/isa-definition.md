# ISA Definition Guide

This guide explains how to define custom instruction set architectures (ISAs) for use with py-isa-xform.

## Overview

An ISA definition is a JSON file that completely specifies an instruction set architecture. This includes:
- Basic architecture properties (word size, endianness)
- Register definitions
- Instruction specifications
- Addressing modes
- Assembly syntax rules

## ISA Definition Structure

### Basic Properties

```json
{
  "name": "MyCustomISA",
  "version": "1.0",
  "description": "A custom 16-bit RISC processor",
  "word_size": 16,
  "endianness": "little",
  "instruction_size": 16,
  "memory_model": "von_neumann"
}
```

**Fields:**
- `name` - Unique identifier for the ISA
- `version` - Version string for compatibility tracking
- `description` - Human-readable description
- `word_size` - Size of a word in bits (8, 16, 32, 64)
- `endianness` - Byte order ("little" or "big")
- `instruction_size` - Size of instructions in bits
- `memory_model` - "von_neumann" or "harvard"

### Register Definitions

```json
{
  "registers": {
    "general_purpose": [
      {"name": "R0", "size": 16, "alias": ["ZERO"]},
      {"name": "R1", "size": 16, "alias": ["AT"]},
      {"name": "R2", "size": 16, "alias": ["V0"]},
      {"name": "R3", "size": 16, "alias": ["V1"]}
    ],
    "special_purpose": [
      {"name": "PC", "size": 16, "description": "Program Counter"},
      {"name": "SP", "size": 16, "description": "Stack Pointer"},
      {"name": "FLAGS", "size": 16, "description": "Status Flags"}
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
      "opcode": "0000",
      "format": "R-type",
      "description": "Add two registers",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "15:12", "value": "0000"},
          {"name": "rd", "bits": "11:8", "type": "register"},
          {"name": "rs1", "bits": "7:4", "type": "register"},
          {"name": "rs2", "bits": "3:0", "type": "register"}
        ]
      },
      "syntax": "ADD $rd, $rs1, $rs2",
      "semantics": "$rd = $rs1 + $rs2",
      "flags_affected": ["Z", "N", "C", "V"]
    },
    {
      "mnemonic": "LDI",
      "opcode": "0001",
      "format": "I-type",
      "description": "Load immediate value",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "15:12", "value": "0001"},
          {"name": "rd", "bits": "11:8", "type": "register"},
          {"name": "immediate", "bits": "7:0", "type": "immediate", "signed": false}
        ]
      },
      "syntax": "LDI $rd, #imm",
      "semantics": "$rd = imm",
      "flags_affected": ["Z", "N"]
    }
  ]
}
```

**Instruction Fields:**
- `mnemonic` - Assembly language name
- `opcode` - Binary opcode value
- `format` - Instruction format type
- `description` - Human-readable description
- `encoding` - Bit-level encoding specification
- `syntax` - Assembly syntax pattern
- `semantics` - Operational description
- `flags_affected` - Which flags are modified

### Encoding Field Types

1. **Opcode Field**
   ```json
   {"name": "opcode", "bits": "15:12", "value": "0000"}
   ```

2. **Register Field**
   ```json
   {"name": "rd", "bits": "11:8", "type": "register"}
   ```

3. **Immediate Field**
   ```json
   {"name": "immediate", "bits": "7:0", "type": "immediate", "signed": true}
   ```

4. **Address Field**
   ```json
   {"name": "address", "bits": "11:0", "type": "address"}
   ```

### Addressing Modes

Define how operands are accessed:

```json
{
  "addressing_modes": [
    {
      "name": "register_direct",
      "syntax": "$reg",
      "description": "Direct register access"
    },
    {
      "name": "immediate",
      "syntax": "#value",
      "description": "Immediate value"
    },
    {
      "name": "register_indirect",
      "syntax": "($reg)",
      "description": "Memory address in register"
    },
    {
      "name": "indexed",
      "syntax": "offset($reg)",
      "description": "Register plus offset"
    }
  ]
}
```

### Assembly Syntax Rules

```json
{
  "assembly_syntax": {
    "comment_char": ";",
    "label_suffix": ":",
    "register_prefix": "$",
    "immediate_prefix": "#",
    "hex_prefix": "0x",
    "binary_prefix": "0b",
    "case_sensitive": false,
    "directives": [
      ".org",
      ".word",
      ".byte",
      ".space"
    ]
  }
}
```

## Complete Example: Simple 16-bit RISC ISA

```json
{
  "name": "SimpleRISC16",
  "version": "1.0",
  "description": "A simple 16-bit RISC processor for educational purposes",
  "word_size": 16,
  "endianness": "little",
  "instruction_size": 16,
  "memory_model": "von_neumann",
  
  "registers": {
    "general_purpose": [
      {"name": "R0", "size": 16, "alias": ["ZERO"]},
      {"name": "R1", "size": 16},
      {"name": "R2", "size": 16},
      {"name": "R3", "size": 16},
      {"name": "R4", "size": 16},
      {"name": "R5", "size": 16},
      {"name": "R6", "size": 16},
      {"name": "R7", "size": 16}
    ],
    "special_purpose": [
      {"name": "PC", "size": 16, "description": "Program Counter"},
      {"name": "SP", "size": 16, "description": "Stack Pointer"},
      {"name": "FLAGS", "size": 16, "description": "Status Flags"}
    ]
  },
  
  "instructions": [
    {
      "mnemonic": "ADD",
      "opcode": "0000",
      "format": "R-type",
      "description": "Add two registers",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "15:12", "value": "0000"},
          {"name": "rd", "bits": "11:9", "type": "register"},
          {"name": "rs1", "bits": "8:6", "type": "register"},
          {"name": "rs2", "bits": "5:3", "type": "register"},
          {"name": "unused", "bits": "2:0", "value": "000"}
        ]
      },
      "syntax": "ADD $rd, $rs1, $rs2",
      "semantics": "$rd = $rs1 + $rs2"
    },
    {
      "mnemonic": "SUB",
      "opcode": "0001",
      "format": "R-type",
      "description": "Subtract two registers",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "15:12", "value": "0001"},
          {"name": "rd", "bits": "11:9", "type": "register"},
          {"name": "rs1", "bits": "8:6", "type": "register"},
          {"name": "rs2", "bits": "5:3", "type": "register"},
          {"name": "unused", "bits": "2:0", "value": "000"}
        ]
      },
      "syntax": "SUB $rd, $rs1, $rs2",
      "semantics": "$rd = $rs1 - $rs2"
    },
    {
      "mnemonic": "LDI",
      "opcode": "1000",
      "format": "I-type",
      "description": "Load immediate value",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "15:12", "value": "1000"},
          {"name": "rd", "bits": "11:9", "type": "register"},
          {"name": "immediate", "bits": "8:0", "type": "immediate", "signed": false}
        ]
      },
      "syntax": "LDI $rd, #imm",
      "semantics": "$rd = imm"
    }
  ],
  
  "addressing_modes": [
    {
      "name": "register_direct",
      "syntax": "$reg",
      "description": "Direct register access"
    },
    {
      "name": "immediate",
      "syntax": "#value",
      "description": "Immediate value"
    }
  ],
  
  "assembly_syntax": {
    "comment_char": ";",
    "label_suffix": ":",
    "register_prefix": "$",
    "immediate_prefix": "#",
    "hex_prefix": "0x",
    "binary_prefix": "0b",
    "case_sensitive": false,
    "directives": [
      ".org",
      ".word",
      ".byte"
    ]
  }
}
```

## Validation Rules

The ISA definition must satisfy several validation rules:

1. **Opcode Uniqueness** - Each instruction must have a unique opcode
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

1. **Overlapping Opcodes** - Make sure opcodes are unique
2. **Incomplete Bit Fields** - All bits must be defined
3. **Register Conflicts** - Avoid conflicting register names
4. **Syntax Ambiguity** - Ensure assembly syntax is unambiguous
5. **Missing Dependencies** - Define all referenced components 