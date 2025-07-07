# Automatic Data Region Detection

The disassembler can automatically detect data regions based on your ISA definition, eliminating the need to manually specify `--data-regions` in most cases.

## How It Works

When you don't specify `--data-regions`, the disassembler automatically uses your ISA's memory layout to determine which regions should be treated as data:

- **Interrupt vectors** are treated as data
- **Data sections** are treated as data  
- **MMIO regions** are treated as data
- **Code sections** are treated as instructions

## ISA Memory Layout Requirements

Your ISA definition must include an `address_space` section with a `memory_layout` field:

```json
{
  "address_space": {
    "memory_layout": {
      "interrupt_vectors": {"start": 0, "end": 30},
      "code_section": {"start": 32, "end": 61439},
      "data_section": {"start": 32768, "end": 61437},
      "mmio": {"start": 61440, "end": 65535}
    }
  }
}
```

## Usage Examples

### Basic Usage (Automatic Detection)

```bash
# No --data-regions needed - uses ISA memory layout
isa_xform disassemble --isa zx16 --input program.bin --output program.s
```

### User Override (When Needed)

```bash
# Override automatic detection with custom regions
isa_xform disassemble --isa zx16 --input program.bin --output program.s \
  --data-regions 0x100-0x200 0x500-0x600
```

## Examples by ISA

### ZX16 ISA

**Memory Layout:**
- Interrupt vectors: 0x0000-0x001E (data)
- Code section: 0x0020-0xEFFF (instructions)
- Data section: 0x8000-0xEFFD (data)
- MMIO: 0xF000-0xFFFF (data)

**Automatic Behavior:**
```bash
# Binary starting at 0x0 (interrupt vectors)
isa_xform disassemble --isa zx16 --input vectors.bin --output vectors.s --start-address 0
# Result: 0x0-0x1E treated as data, 0x20+ treated as instructions

# Binary starting at 0x20 (code section)
isa_xform disassemble --isa zx16 --input code.bin --output code.s --start-address 0x20
# Result: All treated as instructions
```

### Simple RISC ISA

**Memory Layout:**
- Code section: 0x1000-0x1FFF (instructions)
- Data section: 0x2000-0x2FFF (data)
- Stack section: 0x3000-0x3FFF (data)

**Automatic Behavior:**
```bash
# Binary starting at 0x1000 (code section)
isa_xform disassemble --isa simple_risc --input code.bin --output code.s --start-address 0x1000
# Result: All treated as instructions

# Binary starting at 0x2000 (data section)
isa_xform disassemble --isa simple_risc --input data.bin --output data.s --start-address 0x2000
# Result: All treated as data
```

## Benefits

1. **No Manual Configuration**: Users don't need to know memory layout details
2. **ISA Compliance**: Automatically respects the ISA's intended memory organization
3. **Consistency**: Same behavior across different binaries for the same ISA
4. **Flexibility**: Can still override with `--data-regions` when needed
5. **Portability**: Works with any ISA that defines a memory layout

## When to Use Manual Override

Use `--data-regions` when:

- Your ISA doesn't define a memory layout
- You need custom data regions not defined in the ISA
- You want to override the automatic detection for specific cases
- You're working with non-standard memory layouts

## Best Practices

1. **Define Memory Layout**: Always include a complete `memory_layout` in your ISA definition
2. **Use Automatic Detection**: Rely on automatic detection for standard cases
3. **Document Overrides**: When using `--data-regions`, document why the override is needed
4. **Test Both Modes**: Verify that both automatic and manual modes work correctly

## Example ISA Definition

Here's a complete example of an ISA with memory layout:

```json
{
  "name": "MyISA",
  "version": "1.0",
  "address_space": {
    "default_code_start": 0x1000,
    "default_data_start": 0x2000,
    "memory_layout": {
      "interrupt_vectors": {"start": 0x0000, "end": 0x00FF},
      "code_section": {"start": 0x1000, "end": 0x1FFF},
      "data_section": {"start": 0x2000, "end": 0x2FFF},
      "stack_section": {"start": 0x3000, "end": 0x3FFF},
      "mmio": {"start": 0xF000, "end": 0xFFFF}
    }
  }
}
```

With this definition, users can simply run:

```bash
isa_xform disassemble --isa MyISA --input program.bin --output program.s
```

And the disassembler will automatically handle data vs code regions based on the ISA's memory layout. 