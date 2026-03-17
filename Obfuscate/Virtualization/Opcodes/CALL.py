# Format = ["CALL", Target_Register, Func_Register, Arg_Register_List]
# Arg_Register_List example = [1,2,7]
Args = [Registers[Reg] for Reg in C]
Registers[A] = Registers[B](*Args)