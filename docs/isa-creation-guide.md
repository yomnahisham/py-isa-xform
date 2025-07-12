# ISA Creation Guide for py-isa-xform

This guide explains how to create custom ISA definitions that work seamlessly with the py-isa-xform toolkit. The guide is based on the ZX16 ISA structure, which has been thoroughly tested and proven to work perfectly with all toolkit features.

## Overview

An ISA definition is a JSON file that describes your instruction set architecture in a modular, extensible format. The toolkit uses this definition to understand how to assemble, disassemble, and execute instructions for your custom architecture. The ZX16 ISA serves as the reference implementation, demonstrating all the features and best practices for creating a complete, functional ISA.

When you create an ISA definition, you're essentially telling the toolkit: "Here's how my architecture works - these are my registers, these are my instructions, and here's how they should behave." The toolkit then uses this information to automatically generate assemblers, disassemblers, and simulators for your architecture.

## Basic Structure

Your ISA definition must be a valid JSON file containing several key sections. The structure follows a hierarchical organization where each section defines a specific aspect of your architecture. The most important sections are the basic properties, address space configuration, instruction architecture, register definitions, and instruction definitions.

The basic properties section defines fundamental characteristics like instruction size, word size, and endianness. These values are used throughout the toolkit to ensure proper bit manipulation, memory access, and data formatting. The address space configuration defines how memory is organized and where different sections (code, data, stack) are located.

For example, if you're creating a 32-bit RISC architecture, you would set `instruction_size: 32` and `word_size: 32`. If you're creating an 8-bit microcontroller, you might use `instruction_size: 16` and `word_size: 8`. The endianness field determines whether multi-byte values are stored with the most significant byte first (big-endian) or last (little-endian).

## Required Configuration Sections

### Basic Properties

Every ISA must define basic architectural properties. The `name` field provides a human-readable identifier for your ISA, while `version` helps track different iterations. The `instruction_size` and `word_size` fields define the bit width of instructions and data words respectively. The `endianness` field determines byte order for multi-byte values.

For example, the ZX16 ISA defines:
```json
{
  "name": "ZX16",
  "version": "1.0",
  "description": "16-bit educational RISC architecture",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little"
}
```

This tells the toolkit that ZX16 uses 16-bit instructions, 16-bit data words, and little-endian byte ordering. These values affect everything from how instructions are encoded to how data is stored in memory.

### Address Space Configuration

The address space section defines the memory layout and organization. The `size` field specifies the total address space in bits, while the default start addresses define where code, data, and stack sections begin. The memory layout subsection provides detailed mapping of different memory regions, including interrupt vectors, code sections, data sections, stack sections, and memory-mapped I/O areas.

For a 16-bit architecture like ZX16, the address space might look like:
```json
{
  "address_space": {
    "size": 16,
    "default_code_start": 0,
    "default_data_start": 32768,
    "default_stack_start": 65535,
    "memory_layout": {
      "code_section": {"start": 0, "end": 32767},
      "data_section": {"start": 32768, "end": 65534},
      "stack_section": {"start": 65535, "end": 65535}
    }
  }
}
```

This configuration tells the assembler where to place code (starting at address 0), where to put data (starting at address 32768), and where the stack should grow from (address 65535). The memory layout helps the toolkit understand the purpose of different memory regions.

### PC Behavior

Program counter behavior is crucial for control flow instructions. The `points_to` field defines whether the PC points to the current instruction or the next instruction. The `offset_for_jumps` field specifies the PC offset used in jump calculations. The disassembly subsection defines how jump targets are calculated during disassembly, ensuring that relative addresses are correctly resolved.

For example, in ZX16:
```json
{
  "pc_behavior": {
    "points_to": "current_instruction",
    "offset_for_jumps": 2,
    "jump_offset_calculation": "target_minus_pc",
    "disassembly": {
      "jump_target_calculation": "pc_plus_offset",
      "pc_value_for_jumps": "instruction_address"
    }
  }
}
```

This configuration means that when the PC points to an instruction, jump offsets are calculated as `target_address - current_pc`, and during disassembly, jump targets are calculated as `current_pc + offset`. The offset of 2 accounts for the fact that ZX16 instructions are 2 bytes long.

### Instruction Architecture

This section defines the instruction encoding format and constraints. The `instruction_size` and `instruction_size_bytes` fields specify the bit and byte size of instructions. The `variable_length` field indicates whether instructions can have different sizes. The `alignment` field defines memory alignment requirements, while `address_bits` and `address_mask` define address space constraints.

For ZX16:
```json
{
  "instruction_architecture": {
    "instruction_size": 16,
    "instruction_size_bytes": 2,
    "variable_length": false,
    "alignment": 2,
    "max_instruction_length": 16,
    "address_bits": 16,
    "address_mask": 65535
  }
}
```

This tells the toolkit that all ZX16 instructions are exactly 16 bits (2 bytes) long, must be aligned to 2-byte boundaries, and can address up to 65536 different memory locations (16-bit address space).

### Register and Operand Formatting

Register formatting defines how registers are displayed in assembly output. The `prefix` and `suffix` fields control register name formatting, while the `case` field determines capitalization. The `zero_register` field identifies the register that always contains zero. The alternatives subsection provides alias names for registers, allowing multiple names for the same register.

For example:
```json
{
  "register_formatting": {
    "prefix": "r",
    "suffix": "",
    "case": "lower",
    "zero_register": "r0",
    "alternatives": {
      "r0": ["zero", "zr"],
      "r1": ["ra", "return"],
      "r2": ["sp", "stack"],
      "r3": ["fp", "frame"]
    }
  }
}
```

This configuration means registers are displayed as `r0`, `r1`, etc., but assembly code can also use `zero`, `ra`, `sp`, etc. The zero register is `r0`, which always contains the value 0.

Operand formatting controls how different operand types are displayed. The `immediate_prefix` and `hex_prefix` fields define prefixes for immediate values and hexadecimal numbers. The `address_format` and `immediate_format` fields define string templates for formatting addresses and immediates. The separators subsection defines punctuation used in assembly syntax.

```json
{
  "operand_formatting": {
    "immediate_prefix": "#",
    "hex_prefix": "0x",
    "binary_prefix": "0b",
    "register_prefix": "r",
    "address_format": "0x{addr:X}",
    "immediate_format": "{value}",
    "register_format": "r{reg}",
    "separators": {
      "operand": ", ",
      "address": "(",
      "address_close": ")"
    }
  }
}
```

This means immediates are displayed with a `#` prefix (like `#42`), hex values with `0x` (like `0xFF`), and addresses in hex format. The separators define how operands are formatted, so `LW r1, 4(r2)` becomes the standard format.

### Instruction Categories and Control Flow

Instruction categories organize instructions by function, making the ISA more maintainable and enabling category-specific optimizations. The control flow subsection identifies different types of control flow instructions, while the main categories section groups instructions by their primary function.

```json
{
  "instruction_categories": {
    "control_flow": {
      "jumps": ["J", "JAL", "RET"],
      "branches": ["BEQ", "BNE", "BLT", "BGE"],
      "calls": ["CALL", "ECALL"],
      "returns": ["RET"]
    },
    "data_movement": ["LI", "LW", "SW", "MOV"],
    "arithmetic": ["ADD", "SUB", "MUL", "DIV"],
    "logical": ["AND", "OR", "XOR", "NOT"]
  }
}
```

The `control_flow_instructions` and `jump_instructions` arrays list all instructions that affect program flow. These lists are used by the toolkit to identify instructions that require special handling during assembly and disassembly.

```json
{
  "control_flow_instructions": ["J", "JAL", "JALR", "JR", "BEQ", "BNE", "BLT", "BGE", "CALL", "ECALL", "RET"],
  "jump_instructions": ["J", "JAL", "JALR", "JR", "CALL", "RET"]
}
```

## Register Definitions

Registers are the foundation of any ISA. Each register must have a unique name, size, and description. The size field is particularly important as it defines the register's bit width and is used for sign extension and overflow calculations. Registers are typically organized into general-purpose and special-purpose categories.

General-purpose registers are used for data manipulation and addressing, while special-purpose registers have specific architectural roles like the program counter or status flags. Each register can have multiple alias names, allowing assembly code to use different names for the same register.

For ZX16, the register definition looks like:
```json
{
  "registers": {
    "general_purpose": [
      {
        "name": "r0",
        "size": 16,
        "alias": ["zero", "zr"],
        "description": "Always zero"
      },
      {
        "name": "r1",
        "size": 16,
        "alias": ["ra", "return"],
        "description": "Return address"
      },
      {
        "name": "r2",
        "size": 16,
        "alias": ["sp", "stack"],
        "description": "Stack pointer"
      }
    ],
    "special": [
      {
        "name": "pc",
        "size": 16,
        "description": "Program counter"
      },
      {
        "name": "flags",
        "size": 16,
        "description": "Status flags"
      }
    ]
  }
}
```

This defines 16-bit registers where `r0` always contains zero, `r1` holds return addresses, and `r2` is the stack pointer. The special registers include the program counter and status flags.

## Instruction Definitions

Instructions are the core of your ISA. Each instruction must define its mnemonic, format, syntax, semantics, and implementation. The mnemonic is the assembly language name, while the format describes the instruction's encoding structure. The syntax field defines the assembly language format, and the semantics field describes what the instruction does.

The implementation field contains Python code that executes the instruction. This code has access to register read/write functions, memory access functions, flag manipulation functions, and the current execution context. The implementation must handle all aspects of instruction execution, including operand fetching, computation, result storage, and flag updates.

Here's an example ADD instruction for ZX16:
```json
{
  "mnemonic": "ADD",
  "format": "R-type",
  "description": "Add two registers",
  "syntax": "ADD rd, rs1, rs2",
  "semantics": "rd = rs1 + rs2",
  "implementation": "# Add instruction implementation\nrs1_val = read_register(operands['rs1'])\nrs2_val = read_register(operands['rs2'])\nresult = (rs1_val + rs2_val) & 65535\nwrite_register(operands['rd'], result)\nset_flag('Z', result == 0)\nset_flag('N', (result & 32768) != 0)",
  "encoding": {
    "fields": [
      {"name": "funct4", "bits": "15:12", "value": "0000"},
      {"name": "rs2", "bits": "11:8", "type": "register"},
      {"name": "rs1", "bits": "7:4", "type": "register"},
      {"name": "rd", "bits": "3:0", "type": "register"}
    ]
  }
}
```

The encoding section defines the bit-level layout of the instruction. Each field specifies its name, bit range, type, and value. Field types include fixed values, register references, immediate values, and addresses. For immediate fields, the signed field determines whether the value should be sign-extended.

For a load immediate instruction:
```json
{
  "mnemonic": "LI",
  "format": "I-type",
  "description": "Load immediate value",
  "syntax": "LI rd, imm",
  "semantics": "rd = sign_extend(imm)",
  "implementation": "# Load immediate implementation\nimm_val = operands['imm']\nif imm_val & 128:\n    imm_val = imm_val | 65408\nwrite_register(operands['rd'], imm_val & 65535)",
  "encoding": {
    "fields": [
      {"name": "imm", "bits": "15:8", "type": "immediate", "signed": true},
      {"name": "rd", "bits": "7:4", "type": "register"},
      {"name": "opcode", "bits": "3:0", "value": "0001"}
    ]
  }
}
```

This instruction loads an 8-bit signed immediate into a register, with the immediate value stored in bits 15-8 and the destination register in bits 7-4.

## Directive Definitions

Directives are assembly language commands that control the assembly process rather than generating machine code. Each directive must define its name, description, action type, and implementation. The implementation field contains Python code that performs the directive's function, such as setting the current address or defining data.

Directives typically handle address management, data definition, and assembly control. Common directives include origin setting, data definition, and symbol management. Each directive can accept arguments of different types, and the argument_types field defines what types of arguments are expected.

For example, the `.org` directive:
```json
{
  "name": ".org",
  "description": "Set origin address",
  "action": "set_origin",
  "implementation": "# Set origin directive implementation\nif args:\n    addr = int(args[0], 0)\n    context.current_address = addr\n    assembler.context.current_address = addr\n    assembler.symbol_table.set_current_address(addr)",
  "argument_types": ["number"],
  "syntax": ".org address",
  "examples": [".org 0x1000", ".org 4096"]
}
```

This directive sets the current assembly address, allowing you to control where code and data are placed in memory. The implementation code parses the address argument and updates the assembler's current address.

The `.word` directive for defining data:
```json
{
  "name": ".word",
  "description": "Define word data",
  "action": "define_word",
  "implementation": "# Define word directive implementation\nresult = bytearray()\nfor arg in args:\n    value = int(arg, 0)\n    result.extend([value & 255, (value >> 8) & 255])\n    context.current_address += 2\nassembler.context.current_address = context.current_address\nassembler.symbol_table.set_current_address(context.current_address)",
  "argument_types": ["number"],
  "syntax": ".word value1, value2, ...",
  "examples": [".word 0x1234", ".word 42, 0xABCD"]
}
```

This directive creates 16-bit data values in memory, converting each argument to bytes and placing them at the current address.

## Pseudo-Instructions

Pseudo-instructions are assembly language conveniences that expand into one or more real instructions. They provide a more user-friendly interface for common operations. Each pseudo-instruction defines its mnemonic, description, syntax, and expansion. The expansion field specifies the real instruction or instructions that the pseudo-instruction expands into.

The disassembly section controls how pseudo-instructions are handled during disassembly. The `hide_operands` field determines whether operands are shown, while the `show_as_pseudo` field controls whether the instruction is displayed as a pseudo-instruction or its expansion. The `reconstruction_type` field defines how the instruction should be reconstructed during disassembly.

For example, a NOP pseudo-instruction:
```json
{
  "mnemonic": "NOP",
  "description": "No operation",
  "syntax": "NOP",
  "expansion": "ADD r0, r0, r0",
  "disassembly": {
    "hide_operands": true,
    "show_as_pseudo": true
  }
}
```

This expands `NOP` into `ADD r0, r0, r0`, which does nothing since r0 always contains zero. During disassembly, it will be shown as `NOP` rather than the expanded instruction.

A CALL pseudo-instruction:
```json
{
  "mnemonic": "CALL",
  "description": "Call function",
  "syntax": "CALL label",
  "expansion": "JAL r1, label",
  "disassembly": {
    "hide_operands": false,
    "show_as_pseudo": true,
    "reconstruction_type": "jump_with_return"
  }
}
```

This expands `CALL label` into `JAL r1, label`, which jumps to the label and saves the return address in r1. During disassembly, it will be reconstructed as `CALL` if the pattern matches.

## Assembly Syntax and Constants

Assembly syntax defines the formatting rules for assembly language output. This includes comment characters, label suffixes, register prefixes, and immediate prefixes. The case_sensitive field determines whether the assembler treats identifiers as case-sensitive.

```json
{
  "assembly_syntax": {
    "comment_chars": ["#", ";"],
    "label_suffix": ":",
    "register_prefix": "r",
    "immediate_prefix": "#",
    "string_delimiters": ["\"", "'"],
    "case_sensitive": false,
    "instruction_separator": "\n"
  }
}
```

This configuration allows comments with `#` or `;`, labels ending with `:`, and case-insensitive identifiers. The immediate prefix `#` is used for immediate values.

Constants define architectural constants used throughout the ISA. These include memory addresses, vector locations, and system parameters. Constants are typically defined as decimal values and are used in instruction implementations and directive processing.

```json
{
  "constants": {
    "RESET_VECTOR": 0,
    "INT_VECTORS": 0,
    "CODE_START": 0,
    "MMIO_BASE": 32768,
    "MMIO_SIZE": 32768,
    "STACK_TOP": 65535,
    "MEM_SIZE": 65536
  }
}
```

These constants define the reset vector address, memory-mapped I/O base address, and memory size for the architecture.

## ECALL Services

ECALL services define system calls available to programs. Each service has a unique identifier, name, description, parameters, and return value specification. The parameters field defines what registers are used to pass arguments, while the return field specifies what the service returns.

ECALL services provide the interface between user programs and the system environment. Common services include character output, string output, program termination, and system information queries. The service identifiers are typically defined as hexadecimal values.

```json
{
  "ecall_services": {
    "0x00": {
      "name": "print_char",
      "description": "Print character from r1 register",
      "parameters": {
        "r1": "Character to print"
      },
      "return": "None"
    },
    "0x01": {
      "name": "print_string",
      "description": "Print string starting at address in r1 register",
      "parameters": {
        "r1": "Address of null-terminated string"
      },
      "return": "None"
    },
    "0x02": {
      "name": "exit",
      "description": "Exit program with code in r1 register",
      "parameters": {
        "r1": "Exit code"
      },
      "return": "None"
    }
  }
}
```

This defines three system calls: printing a character, printing a string, and exiting the program. The ECALL instruction uses the value in a register to determine which service to invoke.

## Validation and Testing

Before using your ISA, validate that all required fields are present and correctly formatted. Check that register sizes are defined, instruction implementations are valid Python code, and encoding fields don't overlap. Test your ISA with simple assembly and disassembly operations to ensure it works correctly.

The toolkit provides comprehensive error checking and will report specific issues with your ISA definition. Common issues include missing required fields, invalid Python code in implementations, overlapping bit ranges in encodings, and undefined registers or instructions.

To test your ISA, start with simple programs:
```bash
# Test assembly
python -m src.isa_xform.cli assemble --isa your_isa.json --input test.s --output test.bin

# Test disassembly
python -m src.isa_xform.cli disassemble --isa your_isa.json --input test.bin --output test_dis.s
```

Create a simple test file `test.s`:
```
LI r1, 42
ADD r2, r1, r1
SW r2, 100(r0)
```

This will help you verify that your ISA can assemble and disassemble basic instructions correctly.

## Best Practices

Start with a simple ISA and gradually add complexity. Use the ZX16 ISA as a reference for structure and organization. Define all registers before using them in instructions, and ensure all instruction names referenced in pseudo-instructions are defined. Use decimal values instead of hexadecimal for better readability and consistency.

Test your ISA thoroughly with various instruction types and edge cases. Pay special attention to control flow instructions, as they often require special handling. Ensure that sign extension and immediate formatting work correctly for all instruction types.

When defining instruction encodings, make sure bit ranges don't overlap and that all bits are accounted for. Use descriptive field names that match your assembly syntax. For example, if your assembly uses `rd, rs1, rs2`, your encoding fields should use the same names.

For implementations, use the available functions provided by the toolkit:
- `read_register(reg_name)` - Read a register value
- `write_register(reg_name, value)` - Write a value to a register
- `read_memory(address, size)` - Read from memory
- `write_memory(address, value, size)` - Write to memory
- `set_flag(flag_name, value)` - Set a status flag
- `context.pc` - Access the program counter

## Complete Example Structure

The ZX16 ISA provides a complete, working example of all these concepts. It demonstrates proper register definition, comprehensive instruction coverage, effective directive implementation, and robust pseudo-instruction support. The ZX16 ISA has been extensively tested and serves as the reference implementation for the toolkit.

When creating your own ISA, use the ZX16 structure as a template and modify it to match your architectural requirements. The modular design allows you to add or remove features as needed while maintaining compatibility with the toolkit's assembly and disassembly capabilities.

You can find the complete ZX16 ISA definition in `src/isa_definitions/zx16.json`. Study this file to understand how all the pieces fit together. Pay attention to how the instruction encodings are structured, how the implementations handle different operand types, and how the formatting rules create readable assembly output.

## Troubleshooting

If your ISA doesn't work as expected, check the error messages carefully. Common issues include missing required fields, invalid JSON syntax, undefined registers or instructions, and incorrect bit range specifications. The toolkit provides detailed error messages that will help you identify and fix issues.

Test your ISA incrementally, starting with simple instructions and gradually adding more complex features. This approach helps isolate issues and ensures that each component works correctly before moving on to the next.

Common error messages and solutions:
- "Missing required field 'size'" - Every register must have a size field
- "Unknown register 'r5'" - Define all registers before using them in instructions
- "Invalid encoding: overlapping bits" - Check that bit ranges don't overlap
- "Missing implementation" - Every instruction and directive must have an implementation field

## Conclusion

Creating a custom ISA for the py-isa-xform toolkit is straightforward when following the established patterns. The ZX16 ISA demonstrates all the necessary components and provides a solid foundation for your own designs. By following this guide and using the ZX16 structure as a reference, you can create robust, functional ISAs that work seamlessly with the toolkit's assembly, disassembly, and execution capabilities.

The modular design of the toolkit allows for extensive customization while maintaining consistency and reliability. Whether you're creating a simple educational ISA or a complex production architecture, the toolkit provides the tools and structure needed to bring your design to life.

Remember that the ZX16 ISA in `src/isa_definitions/zx16.json` is your best reference. It shows exactly how to structure every part of an ISA definition and has been thoroughly tested with the toolkit. Use it as your starting point and modify it to match your architectural requirements. 