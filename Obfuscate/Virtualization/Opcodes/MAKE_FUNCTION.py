# Format = ["MAKE_FUNCTION", DestReg, CodeIndex, DefaultRegs]
SerializedCode, NumArgs = Constants[B]
Defaults = [Registers[R] for R in C]
NumRequired = NumArgs - len(Defaults)

def MakeCallable(*CallArgs):
    NumProvided = len(CallArgs)
    if NumProvided < NumRequired:
        raise TypeError("Missing required positional arguments")

    DefaultsNeeded = NumArgs - NumProvided
    if DefaultsNeeded > 0:
        FillFrom = len(Defaults) - DefaultsNeeded
        FullArgs = list(CallArgs) + Defaults[FillFrom:]
    else:
        FullArgs = list(CallArgs)

    return Run(SerializedCode, FullArgs)

MakeCallable.__is_virtual__ = True
MakeCallable.__code_data__ = (SerializedCode, NumArgs, Defaults)
Registers[A] = MakeCallable