# Format = ["EXCEPT_MATCH", MatchReg, TypeReg]
# A = MatchReg  (destination: True if the active exception matches the type)
# B = TypeReg   (the exception type to test against)
Registers[A] = isinstance(ActiveException, Registers[B])
