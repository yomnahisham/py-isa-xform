# ISA Creation Guide

This guide explains how to create custom Instruction Set Architectures (ISAs) for the py-isa-xform toolkit using the ISA Scaffold Generator.

## Quick Start

### Using the Scaffold Generator

The scaffold generator creates ISA definitions with boilerplate implementations for common instruction types.

```bash
# Generate a basic ISA with common instructions
python -m isa_xform.core.isa_scaffold --name "MY_ISA" --instructions "ADD,SUB,AND,OR,XOR,ADDI,LI,J,ECALL" --directives ".org,.word,.byte"

# Generate a more complex ISA
python -m isa_xform.core.isa_scaffold --name "ADVANCED_ISA" \
  --instructions "ADD,SUB,AND,OR,XOR,ADDI,ANDI,ORI,XORI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL" \
  --directives ".org,.word,.byte,.ascii,.align" \
  --word-size 16 \
  --instruction-size 16
```

## Detailed Guide

### ISA Scaffold Generator

The scaffold generator (`isa_xform.core.isa_scaffold`) automatically creates ISA definitions with:

- **Instruction Templates**: Pre-built implementations for common instruction types
- **Directive Templates**: Standard assembly directives with implementations
- **Register Definitions**: Standard register sets with aliases
- **Pseudo Instructions**: Common pseudo-instructions like NOP, MV, etc.

#### Supported Instruction Types

1. **R-type** (Register-to-register operations)
   - Examples: ADD, SUB, AND, OR, XOR, SLT, SLTU
   - Syntax: `{mnemonic} rd, rs2`
   - Semantics: `rd = rd {operation} rs2`

2. **I-type** (Register-immediate operations)
   - Examples: ADDI, ANDI, ORI, XORI, SLTI, LI
   - Syntax: `{mnemonic} rd, imm`
   - Semantics: `rd = rd {operation} sign_extend(imm)`

3. **J-type** (Jump instructions)
   - Examples: J, JAL
   - Syntax: `{mnemonic} label` or `{mnemonic} rd, label`
   - Semantics: `PC = label` or `rd = PC + 2; PC = label`

4. **SYS-type** (System calls)
   - Examples: ECALL, EBREAK
   - Syntax: `{mnemonic} svc`
   - Semantics: `Trap to service number`

#### Supported Directives

- `.org` - Set origin address
- `.word` - Define word data
- `.byte` - Define byte data
- `.ascii` - Define ASCII string
- `.align` - Align to boundary

#### Command Line Options

```bash
python -m isa_xform.core.isa_scaffold --help
```

- `--name`: Name of the ISA (required)
- `--instructions`: Comma-separated list of instructions (required)
- `--directives`: Comma-separated list of directives (optional)
- `--word-size`: Word size in bits (default: 16)
- `--instruction-size`: Instruction size in bits (default: 16)
- `--output`: Output file path (default: {name}_isa.json)

#### Example Usage

```bash
# Generate a minimal ISA
python -m isa_xform.core.isa_scaffold --name "MINIMAL" --instructions "ADD,LI,J"

# Generate a comprehensive ISA
python -m isa_xform.core.isa_scaffold --name "COMPREHENSIVE" \
  --instructions "ADD,SUB,AND,OR,XOR,ADDI,ANDI,ORI,XORI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL" \
  --directives ".org,.word,.byte,.ascii,.align"

# Generate a 32-bit ISA
python -m isa_xform.core.isa_scaffold --name "RISC32" \
  --instructions "ADD,SUB,AND,OR,XOR,ADDI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL" \
  --word-size 32 \
  --instruction-size 32
```

## Customizing Your ISA

### Modifying Instructions

1. **Change Opcodes**: Update the `value` fields in the encoding
2. **Add New Instructions**: Copy existing instruction and modify
3. **Custom Implementations**: Replace the `implementation` field with your code

Example - Adding a custom instruction:

```json
{
  "mnemonic": "CUSTOM",
  "format": "R-type",
  "description": "Custom instruction",
  "syntax": "CUSTOM rd, rs2",
  "semantics": "rd = custom_operation(rd, rs2)",
  "implementation": "# Custom instruction implementation\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = custom_operation(rd_val, rs2_val)\nwrite_register(operands['rd'], result)",
  "encoding": {
    "fields": [
      {"name": "funct4", "bits": "15:12", "value": "1111"},
      {"name": "rs2", "bits": "11:9", "type": "register"},
      {"name": "rd", "bits": "8:6", "type": "register"},
      {"name": "func3", "bits": "5:3", "value": "111"},
      {"name": "opcode", "bits": "2:0", "value": "000"}
    ]
  }
}
```

### Adding Custom Directives

```json
{
  "name": ".custom",
  "description": "Custom directive",
  "action": "custom_action",
  "implementation": "# Custom directive implementation\n# Your custom logic here\npass",
  "argument_types": ["string"],
  "syntax": ".custom arg1, arg2, ...",
  "examples": [".custom example"]
}
```

### Modifying Register Set

```json
"registers": {
  "general_purpose": [
    {"name": "r0", "size": 16, "alias": ["zero"], "description": "Always zero"},
    {"name": "r1", "size": 16, "alias": ["sp"], "description": "Stack pointer"},
    // ... add more registers
  ]
}
```

## Testing Your ISA

### 1. Basic Testing

```bash
# Test assembly
python -m isa_xform.cli assemble --isa your_isa --input test.s --output test.bin

# Test disassembly
python -m isa_xform.cli disassemble --isa your_isa --input test.bin --output test_dis.s

# Compare original and disassembled
diff test.s test_dis.s
```

### 2. Create Test Programs

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

### 3. Validation Checklist

- [ ] All instructions assemble correctly
- [ ] All instructions disassemble correctly
- [ ] Immediate values are within bounds
- [ ] Register numbers are valid
- [ ] Labels resolve correctly
- [ ] Directives work as expected
- [ ] Pseudo-instructions expand correctly

## Best Practices

### 1. Instruction Design

- **Consistent Encoding**: Use consistent bit patterns for similar instructions
- **Opcode Space**: Plan your opcode space carefully to avoid conflicts
- **Immediate Sizes**: Consider the range of immediate values needed
- **Register Usage**: Follow standard calling conventions

### 2. Implementation Code

- **Safety**: Always validate inputs and bounds
- **Flags**: Set appropriate status flags for arithmetic operations
- **Memory**: Handle memory access safely
- **Comments**: Document complex implementations

### 3. Documentation

- **Clear Descriptions**: Provide clear descriptions for all instructions
- **Examples**: Include usage examples
- **Constraints**: Document any limitations or constraints
- **Compatibility**: Note any compatibility with existing ISAs

### 4. Testing

- **Edge Cases**: Test with boundary values
- **Error Conditions**: Test with invalid inputs
- **Integration**: Test with the full toolchain
- **Performance**: Consider performance implications

## Troubleshooting

### Common Issues

1. **Assembly Fails**: Check instruction encoding and field definitions
2. **Disassembly Wrong**: Verify field extraction logic
3. **Immediate Overflow**: Check immediate field sizes
4. **Register Invalid**: Verify register numbering
5. **Label Not Found**: Check symbol table handling

### Debugging Tips

1. **Use Verbose Output**: Enable debug logging
2. **Check Binary**: Use hexdump to inspect generated binary
3. **Step Through**: Use a debugger to trace execution
4. **Compare**: Compare with working examples

## Examples

### Minimal ISA Example

```bash
# Generate minimal ISA
python -m isa_xform.core.isa_scaffold --name "MINIMAL" --instructions "ADD,LI,J"

# Test it
echo "LI a0, 42\nADD a0, a0\nJ start" > test.s
python -m isa_xform.cli assemble --isa minimal --input test.s --output test.bin
python -m isa_xform.cli disassemble --isa minimal --input test.bin --output test_dis.s
```

### Advanced ISA Example

```bash
# Generate comprehensive ISA
python -m isa_xform.core.isa_scaffold --name "ADVANCED" \
  --instructions "ADD,SUB,AND,OR,XOR,ADDI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL" \
  --directives ".org,.word,.byte,.ascii,.align"

# Create test program
cat > test.s << 'EOF'
.org 0x100
start:
    LI a0, 10
    LI a1, 20
    ADD a0, a1
    ECALL 0x3FF
EOF

# Test assembly and disassembly
python -m isa_xform.cli assemble --isa advanced --input test.s --output test.bin
python -m isa_xform.cli disassemble --isa advanced --input test.bin --output test_dis.s
```

## Next Steps

1. **Start Simple**: Begin with a minimal ISA and add features gradually
2. **Test Thoroughly**: Create comprehensive test suites
3. **Document**: Document your ISA design decisions
4. **Share**: Consider sharing your ISA with the community
5. **Iterate**: Refine your ISA based on usage and feedback

For more information, see the [API Reference](api-reference.md) and [Architecture Guide](architecture.md).

> **Note:** If you include both `LI` and `ADDI` in your ISA, and they share the same encoding, the disassembler will always show one mnemonic (usually the first match). To avoid ambiguity, only include one of them, or use a pseudo-instruction for `LI` that expands to `ADDI`. 