
class RegisterFile:
    def __init__(self, zero_locked=True):
        self.zero_locked = zero_locked
        self.registers = {}
        self.alias_map = {}

        # Define registers directly
        reg_defs = [
            ("x0", ["t0"]),
            ("x1", ["ra"]),
            ("x2", ["sp"]),
            ("x3", ["s0"]),
            ("x4", ["s1"]),
            ("x5", ["t1"]),
            ("x6", ["a0"]),
            ("x7", ["a1"]),
        ]

        for name, aliases in reg_defs:
            self.registers[name] = 0
            for alias in aliases:
                self.alias_map[alias] = name

    def _canonical(self, name):
        return self.alias_map.get(name, name)

    def get(self, name):
        canonical = self._canonical(name)
        return self.registers.get(canonical, 0)

    def set(self, name, value):
        canonical = self._canonical(name)
        if self.zero_locked and canonical == "x0":
            return
        self.registers[canonical] = value & 0xFFFF  # 16-bit masking

    def dump(self):
        reverse_alias_map = {v: k for k, v in self.alias_map.items()}
        for name in sorted(self.registers):
            alias = reverse_alias_map.get(name, "")
            alias_str = f" ({alias})" if alias else ""
            print(f"{name}{alias_str}: 0x{self.registers[name]:04X}")

def read_asm_file(filepath):
    """
    Reads an assembly (.asm) file line by line.

    Parameters:
        filepath (str): Path to the .asm file

    Returns:
        List[str]: A list of non-empty, non-comment lines
    """
    instructions = []

    try:
        with open(filepath, 'r') as file:
            for line in file:
                # Remove leading/trailing whitespace
                clean_line = line.strip()
                
                # Skip empty lines and full-line comments
                if not clean_line or clean_line.startswith('#') or clean_line.startswith('//'):
                    continue

                # Optionally strip inline comments
                if '#' in clean_line:
                    clean_line = clean_line.split('#')[0].strip()
                elif '//' in clean_line:
                    clean_line = clean_line.split('//')[0].strip()

                if clean_line:  # If anything left after stripping
                    instructions.append(clean_line)

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")

    return instructions

def main():
    filepath = "/Users/LiloBilo/Lilo's Desktop/uni/Assembly/test.asm"  # change this to your actual file path
    instructions = read_asm_file(filepath)

    print("Parsed Instructions:")
    for instr in instructions:
        print(f"  {instr}")


if __name__ == "__main__":
    main()
