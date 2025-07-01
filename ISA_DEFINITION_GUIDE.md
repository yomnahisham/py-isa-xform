# Custom ISA Definition Guide

This guide explains **exactly how to write your own custom ISA definition** for use with the py-isa-xform toolkit.

---

## 1. File Format
- Your ISA definition must be a **JSON file**.
- Place it in `src/isa_definitions/` or provide the path when loading.

---

## 2. Top-Level Structure
```json
{
  "name": "MyISA",
  "version": "1.0",
  "description": "A short description of your ISA",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "address_space": { "size": 65536, "default_code_start": 32 },
  "registers": { ... },
  "instructions": [ ... ],
  "directives": [ ... ],
  "pseudo_instructions": [ ... ],
  "assembly_syntax": { ... }
}
```

---

## 3. Registers
Define your register set:
```json
"registers": {
  "general_purpose": [
    {"name": "x0", "size": 16, "alias": ["zero"], "description": "Always zero"},
    {"name": "x1", "size": 16, "alias": ["ra"], "description": "Return address"}
    // ...
  ]
}
```

---

## 4. Instructions
Each instruction is an object in the `instructions` array:
```json
{
  "mnemonic": "ADD",
  "format": "R-type",
  "description": "Add registers",
  "syntax": "ADD rd, rs2",
  "semantics": "rd = rd + rs2",
  "implementation": "# Python code (optional)\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = (rd_val + rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)",
  "encoding": {
    "fields": [
      {"name": "funct4", "bits": "15:12", "value": "0000"},
      {"name": "rs2", "bits": "11:9", "type": "register"},
      {"name": "rd", "bits": "8:6", "type": "register"},
      {"name": "func3", "bits": "5:3", "value": "000"},
      {"name": "opcode", "bits": "2:0", "value": "000"}
    ]
  }
}
```
- `implementation` is **optional**. If present, it must be valid Python code as a string.
- Use helper functions: `read_register`, `write_register`, `set_flag`, etc.

---

## 5. Directives
Each directive is an object in the `directives` array:
```json
{
  "name": ".magic",
  "description": "Custom magic data",
  "action": "custom_magic",
  "argument_types": ["number"],
  "syntax": ".magic value",
  "implementation": "# Python code (optional)\nvalue = int(args[0])\nresult = bytes([value ^ 0xAB, value & 0xFF])\ncontext.current_address += len(result)\nassembler.context.current_address = context.current_address\nassembler.symbol_table.set_current_address(context.current_address)"
}
```
- `implementation` is **optional**. If present, it must be valid Python code as a string.
- Use: `args`, `assembler`, `context`, etc.

---

## 6. Pseudo-Instructions (Optional)
```json
{
  "mnemonic": "INC",
  "description": "Increment register",
  "syntax": "INC rd",
  "expansion": "ADDI rd, 1"
}
```

---

## 7. Assembly Syntax (Optional)
```json
"assembly_syntax": {
  "comment_char": ";",
  "label_suffix": ":",
  "register_prefix": "",
  "immediate_prefix": "#",
  "hex_prefix": "0x",
  "binary_prefix": "0b",
  "case_sensitive": false
}
```

---

## 8. Implementation Code Environment
- **Instructions**: Have access to `registers`, `memory`, `pc`, `flags`, `operands`, `context`, and helpers.
- **Directives**: Have access to `assembler`, `symbol_table`, `memory`, `current_address`, `section`, `args`, `context`, and helpers.
- **Allowed built-ins**: `int`, `range`, `len`, `bytes`, `abs`, `min`, `max`, etc.
- **Result**: Set a variable `result` to a `bytes` or `bytearray` if you want to emit data.

---

## 9. Example: Minimal Custom ISA
```json
{
  "name": "MiniISA",
  "version": "1.0",
  "description": "Minimal example ISA",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "registers": {
    "general_purpose": [
      {"name": "r0", "size": 16},
      {"name": "r1", "size": 16}
    ]
  },
  "instructions": [
    {
      "mnemonic": "MOV",
      "format": "R-type",
      "description": "Move",
      "syntax": "MOV rd, rs2",
      "semantics": "rd = rs2",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "15:12", "value": "0001"},
          {"name": "rs2", "bits": "11:8", "type": "register"},
          {"name": "rd", "bits": "7:4", "type": "register"}
        ]
      }
    }
  ],
  "directives": [
    {
      "name": ".fill",
      "description": "Fill memory",
      "action": "custom_fill",
      "argument_types": ["number", "number"],
      "syntax": ".fill value count",
      "implementation": "value = int(args[0]); count = int(args[1]); result = bytes([value] * count); context.current_address += count; assembler.context.current_address = context.current_address; assembler.symbol_table.set_current_address(context.current_address)"
    }
  ]
}
```

---

## 10. Tips
- **Validate your JSON** before use.
- **Test** with the CLI: `python3 -m isa_xform.cli assemble --isa my_isa --input myprog.s --output myprog.bin`
- **Check the docs** in `docs/custom-instructions.md` for more advanced features.

---

## 11. Troubleshooting
- If you get errors about field widths, check your encoding and immediate constraints.
- If your implementation code fails, check for Python syntax errors and use only allowed built-ins.
- For help, see the examples in `src/isa_definitions/` and the documentation in `docs/`.

---

**Happy ISA designing!** 