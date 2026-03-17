# 🔒 PyObfuscate

A powerful Python source code obfuscator that applies multiple layers of protection to make reverse engineering significantly harder.

---

## Features

| Feature | Description |
|---|---|
| **Virtualization** | Compiles Python source into a custom register-based VM with randomized opcodes |
| **Control Flow Flattening** | Redirects all execution through a central dispatcher, eliminating readable flow |
| **Variable Renaming** | Replaces all variable and function names with randomized hex-style identifiers |
| **String Encryption** | Encrypts hardcoded strings with XOR + custom base encoding, decrypted only at runtime |
| **Global Hiding** | Wraps global variable and function references to prevent static name analysis |
| **Fracture** | Splits compound expressions into cascading temp-variable assignments |
| **Beautify / Minify** | Optionally formats or minifies the final output |

---

## How It Works

The obfuscation pipeline processes Python source code through a series of AST transformations:

```
Source Code
    │
    ▼
[Parse → AST]
    │
    ├─▶ Virtualization       — compiles to custom bytecode VM
    ├─▶ Encrypt Strings      — XOR + custom base encoding
    ├─▶ Hide Globals         — proxy/table wrapping of globals
    ├─▶ Fracture             — expression decomposition
    ├─▶ Control Flow         — binary-tree dispatcher loop
    ├─▶ Rename Variables     — hex identifier replacement
    │
    ▼
[AST → Code]
    │
    ▼
Obfuscated Output
```

### Virtualization (VM)

The VM subsystem compiles Python AST into a custom register-based bytecode format. Hardening options include:

- **Randomize Opcodes** — Opcodes are assigned random integer values per build, so no two outputs share the same instruction encoding
- **Polymorphic Instructions** — The four fields of each instruction `[Op, A, B, C]` are randomly permuted, e.g. `[C, A, Op, B]`
- **Encrypt Constants** — Strings and integers in the constants table are encrypted; strings use XOR + custom base encoding, integers use a deterministic PRNG mask

---

## Project Structure

```
├── main.py                         # Entry point and pipeline configuration
└── Obfuscate/
    ├── ControlFlow.py              # Control flow flattening via binary dispatch tree
    ├── VariableRenamer.py          # AST-based variable and function renaming
    ├── Mangle/
    │   ├── Fracture.py             # Expression decomposition into temp variables
    │   ├── EncryptStrings.py       # Runtime string encryption/decryption injection
    │   └── HideGlobals.py          # Global name obfuscation
    └── Virtualization/
        ├── VM.py                   # VM orchestration and code generation
        ├── Core/
        │   ├── Encryption.py       # XOR cipher and numeric encryption
        │   ├── Mapping.py          # Opcode mapping and polymorphic instruction transforms
        │   ├── Opnames.py          # Master opcode name list
        │   └── Templates.py        # VM stub and if-chain code generation
        └── Bytecode/
            └── Generator.py        # AST → custom bytecode compiler
```

---

## Usage

### Configuration

Edit the `Settings` dict in `main.py` to enable or disable each layer:

```python
Settings = {
    "VM": {
        "Enabled": True,
        "RandomizeOpcodes": True,
        "PolymorphicInstructions": True,
        "EncryptConstants": True,
    },
    "Fracture": True,
    "Control Flow": True,
    "Rename Variables": True,
    "Encrypt Strings": True,
    "Hide Globals": True,
    "Beautify": False,   # Set True to pretty-print, False to minify
}
```

### Running

1. Place your source file at `Input/Input.py`
2. Run the obfuscator:

```bash
python main.py
```

3. Collect obfuscated output from `Output/Output.py`

### Skipping Virtualization on Specific Functions

Decorate any function with `@OBF_NO_VIRTUALIZE` to exclude it from the VM and keep it as native Python. The function will still be accessible from within the virtualized code via an obfuscated key registered in the global function table.

```python
@OBF_NO_VIRTUALIZE
def my_native_function():
    ...
```

---

## Dependencies

- Python 3.10+
- No external pip packages required for core obfuscation

Optional (for CFG generation):

```bash
pip install python-ta
```

---

## Limitations & Known TODOs

- Built-in name hiding inside the VM is not yet implemented
- Register cleanup (overwriting dead registers) is not yet implemented  
- Variable reuse after a variable goes out of scope is not yet implemented in the renamer

---

## ⚠️ Disclaimer

This tool is intended for protecting your own code — for example, commercial software distribution, license enforcement, or CTF challenge creation. Do not use it to obfuscate malicious software. You are solely responsible for how you use this tool.
