"""
Generic smart expansion module for handling pseudo-instruction expansions
that need intelligent bit redistribution when immediate values overflow.

This system is fully ISA-driven and works with any pseudo-instruction expansion
pattern, using any instructions (including user-defined ones). It automatically
parses the expansion, extracts bit constraints from the ISA, and redistributes bits
as needed. The only special case is a fallback for LA-like expansions (e.g., AUIPC+ADDI)
for backward compatibility with legacy code.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import re


@dataclass
class ExpansionStep:
    """Represents a single step in a pseudo-instruction expansion"""
    instruction: str
    register: str
    field: str
    bit_range: Tuple[int, int]


@dataclass
class SmartExpansionConfig:
    """Configuration for smart expansion behavior"""
    enabled: bool
    strategy: str
    max_addi_bits: int
    max_auipc_bits: int
    overflow_threshold: int


class ExpansionParser:
    """Parses any expansion string into structured steps (generic, not tied to any instruction names)"""
    
    def parse_expansion(self, expansion_str: str) -> List[ExpansionStep]:
        """Parse any expansion string into structured steps"""
        steps = []
        for instruction_str in expansion_str.split(';'):
            instruction_str = instruction_str.strip()
            
            # Parse: "INSTR rd, label[15:12]" -> (instruction, field, bit_range)
            match = re.match(r'(\w+)\s+(\w+),\s*(\w+)\[(\d+):(\d+)\]', instruction_str)
            if match:
                instr_name, rd, field_name, high, low = match.groups()
                steps.append(ExpansionStep(
                    instruction=instr_name,
                    register=rd,
                    field=field_name,
                    bit_range=(int(high), int(low))
                ))
        
        return steps


class GenericRedistributor:
    """Handles generic bit redistribution for any instruction combination (not just AUIPC/ADDI)"""
    
    def redistribute_bits(self, target_value: int, expansion_steps: List[ExpansionStep], constraints: Dict[str, Dict]) -> List[int]:
        """Redistribute target value across any number of instruction fields (generic)"""
        
        # Calculate shift amounts for each step
        shifts = self._calculate_shifts(expansion_steps)
        
        # Start with optimal split
        values = self._optimal_split(target_value, shifts, expansion_steps, constraints)
        
        # Check for overflow and adjust
        for i, step in enumerate(expansion_steps):
            if self._field_overflows(values[i], step, constraints):
                values = self._adjust_for_overflow(target_value, values, shifts, expansion_steps, constraints, i)
        
        return values
    
    def _calculate_shifts(self, expansion_steps: List[ExpansionStep]) -> List[int]:
        """Calculate shift amounts for each step based on bit ranges"""
        shifts = []
        for i, step in enumerate(expansion_steps):
            if i == 0:
                # First step has no shift
                shifts.append(0)
            else:
                # Calculate shift based on previous step's bit range
                prev_high, prev_low = expansion_steps[i-1].bit_range
                shift = prev_high - prev_low + 1
                shifts.append(shift)
        return shifts
    
    def _optimal_split(self, target_value: int, shifts: List[int], expansion_steps: List[ExpansionStep], constraints: Dict) -> List[int]:
        """Calculate optimal initial split across all fields"""
        values = []
        remaining = target_value
        
        for i, step in enumerate(expansion_steps):
            if i == 0:
                # First step gets the lower bits
                high, low = step.bit_range
                bit_width = high - low + 1
                field_mask = (1 << bit_width) - 1
                field_value = remaining & field_mask
                values.append(field_value)
                remaining = remaining >> bit_width
            else:
                # Subsequent steps get bits based on their range
                high, low = step.bit_range
                bit_width = high - low + 1
                field_mask = (1 << bit_width) - 1
                field_value = remaining & field_mask
                values.append(field_value)
                remaining = remaining >> bit_width
        
        return values
    
    def _field_overflows(self, value: int, step: ExpansionStep, constraints: Dict) -> bool:
        """Check if a field value overflows its constraints"""
        if step.instruction not in constraints:
            return False
        
        field_constraints = constraints[step.instruction].get(step.field, {})
        if not field_constraints:
            return False
        
        max_signed = field_constraints.get('max_signed', float('inf'))
        min_signed = field_constraints.get('min_signed', float('-inf'))
        
        return value < min_signed or value > max_signed
    
    def _adjust_for_overflow(self, target_value: int, values: List[int], shifts: List[int], expansion_steps: List[ExpansionStep], constraints: Dict, overflow_index: int) -> List[int]:
        """Adjust values when a field overflows"""
        # For now, implement a simple adjustment strategy
        # This can be enhanced with more sophisticated algorithms
        
        step = expansion_steps[overflow_index]
        field_constraints = constraints[step.instruction].get(step.field, {})
        max_signed = field_constraints.get('max_signed', 0)
        min_signed = field_constraints.get('min_signed', 0)
        
        # Clamp the overflowing value
        if values[overflow_index] > max_signed:
            excess = values[overflow_index] - max_signed
            values[overflow_index] = max_signed
        elif values[overflow_index] < min_signed:
            excess = min_signed - values[overflow_index]
            values[overflow_index] = min_signed
        else:
            return values
        
        # Redistribute excess to higher-priority fields (earlier in the list)
        # This is a simplified approach - could be enhanced
        for i in range(overflow_index - 1, -1, -1):
            if excess <= 0:
                break
            
            step_i = expansion_steps[i]
            field_constraints_i = constraints[step_i.instruction].get(step_i.field, {})
            max_val_i = field_constraints_i.get('max_signed', float('inf'))
            
            if values[i] < max_val_i:
                increase = min(excess, max_val_i - values[i])
                values[i] += increase
                excess -= increase
        
        return values


class SmartExpansionHandler:
    """Handles intelligent expansion of pseudo-instructions with overflow detection (generic).
    Only falls back to LA/AUIPC+ADDI logic for legacy support."""
    
    def __init__(self, isa_definition):
        self.isa_definition = isa_definition
        self.parser = ExpansionParser()
        self.redistributor = GenericRedistributor()
    
    def should_use_smart_expansion(self, pseudo_instruction: Any) -> bool:
        """Check if a pseudo-instruction should use smart expansion"""
        if not hasattr(pseudo_instruction, 'smart_expansion'):
            return False
        
        config = pseudo_instruction.smart_expansion
        return config.get('enabled', False)
    
    def get_smart_expansion_config(self, pseudo_instruction: Any) -> Optional[SmartExpansionConfig]:
        """Get smart expansion configuration for a pseudo-instruction"""
        if not self.should_use_smart_expansion(pseudo_instruction):
            return None
        
        config = pseudo_instruction.smart_expansion
        return SmartExpansionConfig(
            enabled=config.get('enabled', False),
            strategy=config.get('strategy', 'overflow_redistribution'),
            max_addi_bits=config.get('max_addi_bits', 7),
            max_auipc_bits=config.get('max_auipc_bits', 9),
            overflow_threshold=config.get('overflow_threshold', 63)
        )
    
    def _get_instruction_bit_constraints(self, instruction_name: str) -> Dict[str, Any]:
        """Get bit constraints for a specific instruction from the ISA definition"""
        # Access instructions from the ISADefinition object
        instructions = self.isa_definition.instructions
        
        for instruction in instructions:
            if instruction.mnemonic == instruction_name:
                encoding = instruction.encoding
                fields = encoding.get('fields', [])
                
                constraints = {}
                for field in fields:
                    if field.get('type') == 'immediate':
                        field_name = field.get('name', '')
                        bits_spec = field.get('bits', '')
                        signed = field.get('signed', False)
                        
                        # Parse bit range (e.g., "15:9" or "14:9,5:3")
                        bit_ranges = self._parse_bit_ranges(bits_spec)
                        total_bits = sum(end - start + 1 for start, end in bit_ranges)
                        
                        constraints[field_name] = {
                            'bits': bits_spec,
                            'bit_ranges': bit_ranges,
                            'total_bits': total_bits,
                            'signed': signed,
                            'max_value': (1 << total_bits) - 1,
                            'min_signed': -(1 << (total_bits - 1)) if signed else 0,
                            'max_signed': (1 << (total_bits - 1)) - 1 if signed else (1 << total_bits) - 1
                        }
                
                return constraints
        
        return {}
    
    def _parse_bit_ranges(self, bits_spec: str) -> List[Tuple[int, int]]:
        """Parse bit specification like '15:9' or '14:9,5:3' into list of (low, high) tuples"""
        ranges = []
        for part in bits_spec.split(','):
            if ':' in part:
                a, b = map(int, part.strip().split(':'))
                low, high = min(a, b), max(a, b)
                ranges.append((low, high))
        return ranges
    
    def _extract_bits_from_value(self, value: int, bit_ranges: List[Tuple[int, int]]) -> int:
        """Extract bits from a value according to the specified bit ranges"""
        result = 0
        bit_pos = 0
        
        for start, end in bit_ranges:
            # Extract bits from the specified range
            mask = ((1 << (end - start + 1)) - 1) << start
            extracted = (value & mask) >> start
            
            # Place in result at current bit position
            result |= extracted << bit_pos
            bit_pos += end - start + 1
        
        return result
    
    def calculate_smart_expansion(self, pseudo_instruction: Any, target_value: int, instruction_address: int) -> Tuple[str, Dict[str, Any]]:
        """
        Calculate smart expansion for a pseudo-instruction when overflow is detected.
        
        Args:
            pseudo_instruction: The pseudo-instruction definition
            target_value: The target value (e.g., label address)
            instruction_address: The address of the instruction
            
        Returns:
            Tuple of (expanded_text, metadata)
        """
        config = self.get_smart_expansion_config(pseudo_instruction)
        if not config:
            return pseudo_instruction.expansion, {}
        
        if config.strategy == "overflow_redistribution":
            # Try generic expansion first
            generic_result = self._generic_overflow_redistribution_strategy(
                pseudo_instruction, target_value, instruction_address, config
            )
            if generic_result:
                return generic_result
            
            # FALLBACK LOGIC: Legacy hardcoded AUIPC+ADDI redistribution
            # This is NOT the generic system - it's hardcoded for backward compatibility
            return self._overflow_redistribution_strategy(
                pseudo_instruction, target_value, instruction_address, config
            )
        else:
            # Fallback to default expansion
            return pseudo_instruction.expansion, {}
    
    def _generic_overflow_redistribution_strategy(self, pseudo_instruction: Any, target_value: int, instruction_address: int, config: SmartExpansionConfig) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Generic overflow redistribution strategy that works with any instruction combination.
        Returns None if the expansion pattern is not supported or if it matches the legacy LA/AUIPC+ADDI pattern.
        """
        try:
            # Parse the expansion pattern generically
            expansion_steps = self.parser.parse_expansion(pseudo_instruction.expansion)
            if not expansion_steps:
                return None
            
            print(f"[GENERIC_SMART_EXPANSION] Parsed expansion steps: {expansion_steps}")
            
            # Extract constraints for all instructions generically
            constraints = {}
            for step in expansion_steps:
                constraints[step.instruction] = self._get_instruction_bit_constraints(step.instruction)
            
            print(f"[GENERIC_SMART_EXPANSION] Extracted constraints: {constraints}")
            
            # Calculate offset
            offset = target_value - instruction_address
            
            # FALLBACK LOGIC: Legacy hardcoded handling for AUIPC+ADDI combinations
            # This bypasses the generic system for backward compatibility
            # TODO: Remove this fallback and use generic logic for all cases
            if (len(expansion_steps) == 2 and 
                expansion_steps[0].instruction == 'AUIPC' and 
                expansion_steps[1].instruction == 'ADDI'):
                print(f"[GENERIC_SMART_EXPANSION] Detected LA-like (AUIPC+ADDI) expansion, using legacy fallback logic.")
                return None  # Fall back to LA-specific logic
            
            # Try standard expansion first (generic)
            standard_values = self._calculate_standard_values(offset, expansion_steps)
            if not self._has_overflow(standard_values, expansion_steps, constraints):
                print(f"[GENERIC_SMART_EXPANSION] No overflow detected, using standard expansion (generic)")
                return self._generate_expansion(expansion_steps, standard_values), {}
            
            # Use smart redistribution (generic)
            print(f"[GENERIC_SMART_EXPANSION] Overflow detected, using generic smart redistribution")
            redistributed_values = self.redistributor.redistribute_bits(
                offset, expansion_steps, constraints
            )
            
            # Generate new expansion string (generic)
            new_expansion = self._generate_expansion(expansion_steps, redistributed_values)
            
            return new_expansion, {
                'strategy_used': 'generic_overflow_redistribution',
                'overflow_detected': True,
                'expansion_steps': expansion_steps,
                'redistributed_values': redistributed_values
            }
            
        except Exception as e:
            print(f"[GENERIC_SMART_EXPANSION] Error in generic expansion: {e}")
            return None
    
    def _calculate_standard_values(self, offset: int, expansion_steps: List[ExpansionStep]) -> List[int]:
        """Calculate standard values for each step based on bit ranges"""
        values = []
        remaining = offset
        
        for step in expansion_steps:
            high, low = step.bit_range
            bit_width = high - low + 1
            field_mask = (1 << bit_width) - 1
            field_value = remaining & field_mask
            values.append(field_value)
            remaining = remaining >> bit_width
        
        return values
    
    def _has_overflow(self, values: List[int], expansion_steps: List[ExpansionStep], constraints: Dict) -> bool:
        """Check if any field overflows its constraints"""
        for i, step in enumerate(expansion_steps):
            if self.redistributor._field_overflows(values[i], step, constraints):
                return True
        return False
    
    def _generate_expansion(self, expansion_steps: List[ExpansionStep], values: List[int]) -> str:
        """Generate expansion string from steps and values"""
        parts = []
        for i, step in enumerate(expansion_steps):
            parts.append(f"{step.instruction} {step.register}, {values[i]}")
        return "; ".join(parts)
    
    def _overflow_redistribution_strategy(self, pseudo_instruction: Any, target_value: int, instruction_address: int, config: SmartExpansionConfig) -> Tuple[str, Dict[str, Any]]:
        """
        FALLBACK LOGIC: Legacy hardcoded overflow redistribution for AUIPC+ADDI combinations.
        
        This is NOT the generic system - it's hardcoded specifically for LA-like instructions
        for backward compatibility. The generic system above should handle all cases.
        
        This strategy:
        1. Gets bit constraints from ISA definition
        2. Calculates the offset from current PC to target
        3. Checks if ADDI immediate would overflow
        4. If overflow detected, redistributes bits between AUIPC and ADDI
        5. Ensures both instructions fit within their bit constraints
        """
        # Get bit constraints from ISA definition
        auipc_constraints = self._get_instruction_bit_constraints('AUIPC')
        addi_constraints = self._get_instruction_bit_constraints('ADDI')
        
        print(f"[DEBUG] AUIPC constraints: {auipc_constraints}")
        print(f"[DEBUG] ADDI constraints: {addi_constraints}")
        
        # Calculate offset from current PC to target
        offset = target_value - instruction_address
        
        # Extract AUIPC and ADDI bit constraints
        auipc_imm_constraint = auipc_constraints.get('imm', {})
        auipc_imm2_constraint = auipc_constraints.get('imm2', {})
        addi_imm_constraint = addi_constraints.get('imm', {})
        
        # Calculate total AUIPC bits (combining imm and imm2 if both exist)
        auipc_total_bits = 0
        if auipc_imm_constraint:
            auipc_total_bits += auipc_imm_constraint.get('total_bits', 0)
        if auipc_imm2_constraint:
            auipc_total_bits += auipc_imm2_constraint.get('total_bits', 0)
        
        addi_total_bits = addi_imm_constraint.get('total_bits', 7) if addi_imm_constraint else 7
        addi_signed = addi_imm_constraint.get('signed', True) if addi_imm_constraint else True
        
        print(f"[DEBUG] AUIPC total bits: {auipc_total_bits}, ADDI total bits: {addi_total_bits}, ADDI signed: {addi_signed}")
        
        # Calculate the shift amount for AUIPC (how many bits it shifts left)
        # This is typically the number of bits in the ADDI immediate
        auipc_shift = addi_total_bits
        
        # Extract bits according to original expansion pattern
        # Original LA expansion: AUIPC rd, label[15:7]; ADDI rd, label[6:0]
        # So AUIPC gets bits 15-7 (9 bits), ADDI gets bits 6-0 (7 bits)
        auipc_bits_original = (offset >> auipc_shift) & ((1 << auipc_total_bits) - 1)
        addi_bits_original = offset & ((1 << addi_total_bits) - 1)
        
        # Handle signed ADDI correctly
        auipc_final = auipc_bits_original
        addi_final = addi_bits_original
        
        if addi_signed and addi_final >= (1 << (addi_total_bits - 1)):
            # Convert to signed value
            addi_final = addi_final - (1 << addi_total_bits)
            # Adjust AUIPC if needed
            if addi_final < 0:
                auipc_final += 1
                addi_final = offset - (auipc_final << auipc_shift)
        
        print(f"[DEBUG] Offset: {offset} (0x{offset:04X})")
        print(f"[DEBUG] AUIPC bits: {auipc_final} (0x{auipc_final:02X})")
        print(f"[DEBUG] ADDI bits: {addi_final & ((1 << addi_total_bits) - 1):02X} (signed: {addi_final})")
        
        # Check if ADDI would overflow its signed range
        addi_signed_value = addi_final
        overflow_threshold = config.overflow_threshold
        
        # Use ISA-defined constraints if available
        if addi_imm_constraint:
            overflow_threshold = addi_imm_constraint.get('max_signed', overflow_threshold)
        
        print(f"[DEBUG] ADDI signed value: {addi_signed_value}, threshold: {overflow_threshold}")
        
        # Only use smart redistribution if overflow
        if abs(addi_signed_value) > overflow_threshold:
            print(f"[SMART_EXPANSION] ADDI overflow detected, using smart redistribution for offset {offset}")
            return self._redistribute_bits_for_overflow(
                offset, instruction_address, config, auipc_total_bits, addi_total_bits, 
                auipc_shift, addi_signed, overflow_threshold
            )
        else:
            print(f"[SMART_EXPANSION] No overflow detected, using standard expansion (with sign fix)")
            smart_expansion = f"AUIPC rd, {auipc_final}; ADDI rd, {addi_final}"
            return smart_expansion, {}
    
    def _redistribute_bits_for_overflow(self, offset: int, instruction_address: int, config: SmartExpansionConfig, auipc_total_bits: int, addi_total_bits: int, auipc_shift: int, addi_signed: bool, overflow_threshold: int) -> Tuple[str, Dict[str, Any]]:
        """
        FALLBACK LOGIC: Hardcoded bit redistribution between AUIPC and ADDI.
        
        This is NOT the generic system - it's hardcoded specifically for AUIPC+ADDI
        combinations for backward compatibility. The generic redistributor above
        should handle all instruction combinations.
        
        Strategy:
        1. Calculate the optimal split that ensures ADDI fits within its signed range
        2. AUIPC gets the upper bits, ADDI gets the lower bits
        3. Ensure the total equals the original offset
        """
        print(f"[SMART_EXPANSION] Redistributing bits for offset {offset}")
        print(f"[SMART_EXPANSION] AUIPC bits: {auipc_total_bits}, ADDI bits: {addi_total_bits}, shift: {auipc_shift}")
        
        # Start with the optimal split: AUIPC = offset >> shift, ADDI = offset & mask
        auipc_final = offset >> auipc_shift
        addi_final = offset & ((1 << addi_total_bits) - 1)
        
        print(f"[SMART_EXPANSION] Initial split: AUIPC={auipc_final}, ADDI={addi_final}")
        
        # Check if ADDI overflows its signed range
        addi_signed_val = addi_final
        if addi_signed and addi_final & (1 << (addi_total_bits - 1)):  # Sign bit set
            addi_signed_val = addi_final - (1 << addi_total_bits)
        
        print(f"[SMART_EXPANSION] ADDI signed value: {addi_signed_val}, threshold: {overflow_threshold}")
        
        # If ADDI overflows, adjust the split
        if abs(addi_signed_val) > overflow_threshold:
            print(f"[SMART_EXPANSION] ADDI overflows, adjusting split")
            
            # Calculate how many shift increments we need
            excess = abs(addi_signed_val) - overflow_threshold
            auipc_increase = (excess + (1 << auipc_shift) - 1) // (1 << auipc_shift)  # Round up
            
            if addi_signed_val > 0:
                auipc_final += auipc_increase
            else:
                auipc_final += auipc_increase
            
            # Recalculate ADDI
            addi_final = offset - (auipc_final << auipc_shift)
            
            print(f"[SMART_EXPANSION] After ADDI adjustment: AUIPC={auipc_final}, ADDI={addi_final}")
        
        # Check if AUIPC overflows after adjustment
        if auipc_final >= (1 << auipc_total_bits):
            print(f"[SMART_EXPANSION] AUIPC overflows: {auipc_final} >= {1 << auipc_total_bits}")
            # This is a case where we cannot represent the offset with the given bit constraints
            # Use the maximum possible AUIPC and accept some error
            auipc_max = (1 << auipc_total_bits) - 1
            auipc_final = auipc_max
            addi_final = offset - (auipc_final << auipc_shift)
            
            # Ensure ADDI fits in its bit range
            addi_final = addi_final & ((1 << addi_total_bits) - 1)
            
            print(f"[SMART_EXPANSION] Using maximum AUIPC={auipc_max}, ADDI={addi_final}")
            print(f"[SMART_EXPANSION] Warning: Cannot represent offset {offset} exactly with current bit constraints")
        
        # Final verification
        calculated_offset = (auipc_final << auipc_shift) + addi_final
        print(f"[SMART_EXPANSION] Final verification: AUIPC={auipc_final}, ADDI={addi_final}")
        print(f"[SMART_EXPANSION] Calculated offset: {calculated_offset}, Target offset: {offset}")
        if calculated_offset != offset:
            print(f"[SMART_EXPANSION] Warning: Calculated offset {calculated_offset} != target offset {offset}")
            print(f"[SMART_EXPANSION] Error: {offset - calculated_offset}")
        
        # Verify the final target address calculation
        final_target = instruction_address + calculated_offset
        print(f"[SMART_EXPANSION] Final target calculation: PC({instruction_address}) + offset({calculated_offset}) = {final_target}")
        
        # Create the smart expansion
        smart_expansion = f"AUIPC rd, {auipc_final}; ADDI rd, {addi_final}"
        
        print(f"[SMART_EXPANSION] Final values: AUIPC={auipc_final}, ADDI={addi_final}")
        print(f"[SMART_EXPANSION] Expansion: {smart_expansion}")
        
        metadata = {
            'strategy_used': 'overflow_redistribution',
            'overflow_detected': True,
            'original_auipc_bits': offset >> auipc_shift,
            'original_addi_bits': offset & ((1 << addi_total_bits) - 1),
            'redistributed_auipc_bits': auipc_final,
            'redistributed_addi_bits': addi_final,
            'total_offset': offset,
            'instruction_address': instruction_address,
            'auipc_total_bits': auipc_total_bits,
            'addi_total_bits': addi_total_bits,
            'auipc_shift': auipc_shift
        }
        
        return smart_expansion, metadata


def create_smart_expansion_handler(isa_definition) -> SmartExpansionHandler:
    """Factory function to create a smart expansion handler"""
    return SmartExpansionHandler(isa_definition) 