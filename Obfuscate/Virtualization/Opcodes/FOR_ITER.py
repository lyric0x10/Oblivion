# Format = ["FOR_ITER", TargetReg, IteratorReg, JumpOffset]
Val = next(Registers[B], STOP_ITER)
if Val is STOP_ITER:
    Index = C - 1
else:
    Registers[A] = Val