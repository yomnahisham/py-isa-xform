# Custom ISA Creation Guide

This guide explains **exactly how to write your own custom ISA definition** for use with the py-isa-xform toolkit.

---

## 1. File Format & Location
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

## 3. Register Set
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
- `implementation` is **required** and must be valid Python code as a string.
- Use helper functions: `read_register`, `write_register`, `set_flag`, etc.

### 4.1. Branch/Jump Instructions with Relative Offsets
If your ISA includes branch or jump instructions that use a **relative offset** (not an absolute address), you must specify how the offset is calculated using the `"offset_base"` field:
- `"offset_base": "current"` — Offset is relative to the current instruction address (PC).
- `"offset_base": "next"` — Offset is relative to the next instruction address (PC + instruction size).

**Example (ZX16-style, offset from current instruction):**
```json
{
  "mnemonic": "BEQ",
  "format": "B-type",
  "syntax": "BEQ rs1, rs2, offset",
  "encoding": { ... },
  "offset_base": "current"
}
```
**Example (RISC-V-style, offset from next instruction):**
```json
{
  "mnemonic": "BEQ",
  "format": "B-type",
  "syntax": "BEQ rs1, rs2, offset",
  "encoding": { ... },
  "offset_base": "next"
}
```
**If you omit this field for a relative branch/jump, the assembler/disassembler will not know how to calculate the offset correctly.**

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
- `implementation` is **required** and must be valid Python code as a string.
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

## 9. Testing Your ISA

### 9.1. Basic Testing
```bash
# Test assembly
python -m isa_xform.cli assemble --isa your_isa --input test.s --output test.bin
# Test disassembly
python -m isa_xform.cli disassemble --isa your_isa --input test.bin --output test_dis.s
# Compare original and disassembled
diff test.s test_dis.s
```

### 9.2. Create Test Programs
Create simple test programs to verify your ISA:
```assembly
; test.s
.org 0x100
start:
    LI a0, 42          ; Load immediate
    LI a1, 10          ; Load immediate
    ADD a0, a1         ; Add registers
    ECALL 0x3FF        ; Exit with result in a0
```

### 9.3. Validation Checklist
- [ ] All instructions assemble correctly
- [ ] All instructions disassemble correctly
- [ ] Immediate values are within bounds
- [ ] Register numbers are valid
- [ ] Labels resolve correctly
- [ ] Directives work as expected
- [ ] Pseudo-instructions expand correctly

---

## 10. Best Practices
- **Consistent Encoding**: Use consistent bit patterns for similar instructions
- **Opcode Space**: Plan your opcode space carefully to avoid conflicts
- **Immediate Sizes**: Consider the range of immediate values needed
- **Register Usage**: Follow standard calling conventions
- **Safety**: Always validate inputs and bounds
- **Flags**: Set appropriate status flags for arithmetic operations
- **Memory**: Handle memory access safely
- **Comments**: Document complex implementations
- **Clear Descriptions**: Provide clear descriptions for all instructions
- **Examples**: Include usage examples
- **Constraints**: Document any limitations or constraints
- **Compatibility**: Note any compatibility with existing ISAs
- **Edge Cases**: Test with boundary values
- **Error Conditions**: Test with invalid inputs
- **Integration**: Test with the full toolchain
- **Performance**: Consider performance implications

---

## 11. Troubleshooting
- If you get errors about field widths, check your encoding and immediate constraints.
- If your implementation code fails, check for Python syntax errors and use only allowed built-ins.
- For help, see the examples in `src/isa_definitions/` and the documentation in `docs/`.

---

**Happy ISA designing!** 