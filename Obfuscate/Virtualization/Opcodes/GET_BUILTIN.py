# Format = ["GET_BUILTIN", TargetReg, VarName]
_ModuleGlobals = globals()
if B in Globals:
    Registers[A] = Globals[B]
elif B in _ModuleGlobals:
    Registers[A] = _ModuleGlobals[B]
else:
    Registers[A] = BuiltinDict.get(B)