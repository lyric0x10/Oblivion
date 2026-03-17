RetValue = Registers[A]
if CallStack:
    Bytecode, Constants, Registers, Index, TargetReg, Len = CallStack.pop()
    Registers[TargetReg] = RetValue
else:
    return RetValue