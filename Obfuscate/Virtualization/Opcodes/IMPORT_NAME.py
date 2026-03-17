# Format = ["IMPORT_NAME", DestReg, ModuleNameConstIdx, LevelConstIdx]
# Constants[B] = fully-qualified module name string (e.g. "os.path")
# Constants[C] = relative import level (0 for absolute imports)
Registers[A] = __import__(Constants[B], level=Constants[C])
