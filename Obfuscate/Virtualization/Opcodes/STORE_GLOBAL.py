if Namespace is not None:
    Namespace[B] = Registers[A]
else:
    globals()[B] = Registers[A]
