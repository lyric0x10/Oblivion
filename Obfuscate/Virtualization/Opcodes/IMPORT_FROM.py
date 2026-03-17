# Format = ["IMPORT_FROM", DestReg, ModuleReg, AttrNameConstIdx]
# Reads a named attribute from an already-loaded module register.
# Used for `from foo import bar` and for drilling into dotted imports.
Registers[A] = getattr(Registers[B], Constants[C])
