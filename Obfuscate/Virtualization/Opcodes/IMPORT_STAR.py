# Format = ["IMPORT_STAR", ModuleReg]
# Copies every public name from the module into the current scope.
# Mirrors `from foo import *`: names not starting with '_' are published
# via SET_BUILTIN so subsequent GET_BUILTIN lookups can resolve them.
for _name in (getattr(Registers[A], "__all__", None) or
              [n for n in dir(Registers[A]) if not n.startswith("_")]):
    Builtins[_name] = getattr(Registers[A], _name)
