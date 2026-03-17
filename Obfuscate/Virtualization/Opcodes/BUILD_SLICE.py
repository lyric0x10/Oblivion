# Format = ["BUILD_SLICE", DestReg, LowerReg, UpperReg, StepReg]
# Constructs a slice object from three pre-evaluated bound registers.
# Any absent bound is represented at runtime as None (via LOAD_NONE),
# so the VM always receives exactly four operands regardless of which
# bounds were omitted in the source (e.g. a[::2], a[1:], a[::-1]).
Registers[A] = slice(*[Registers[Reg] for Reg in B])