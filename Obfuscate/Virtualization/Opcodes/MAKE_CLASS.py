# Format = ["MAKE_CLASS", ClassReg, CodeIndex, BaseRegs]
CodeObj, _ = Constants[B]          # unwrap (encoded_string, num_args) tuple
Bases = tuple((Registers[Reg] for Reg in C))
Namespace = {}
Run(CodeObj, [], Namespace)
Registers[A] = type("", Bases, Namespace)