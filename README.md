# 🌑 Oblivion Obfuscator

> **Python source code obfuscation that actually means business.**  
> Most obfuscators slap Base64 on your code and call it a day. Oblivion doesn't.

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![License](https://img.shields.io/github/license/yourusername/oblivion-obfuscator) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

---

## What Makes Oblivion Different

Most Python obfuscators available today rely on the same tired tricks — Base64 encoding, `marshal`/`eval` chains, and simple variable renaming. Strip those away and the logic is fully readable in minutes.

Oblivion goes further. It compiles your Python source into a **custom register-based virtual machine** with randomized opcodes, meaning an attacker has to reverse-engineer an entirely custom architecture before they can even begin to understand your code. Stack that on top of control flow flattening, string encryption, global hiding, and expression decomposition — and you have layers that compound on each other.

No external pip packages required. Works on all platforms.

---

## Features

| Feature | Description |
|---|---|
| **Custom Register-Based VM** | Compiles Python source into a bespoke bytecode VM with randomized opcodes per build — no two outputs share the same instruction encoding |
| **Polymorphic Instructions** | The four fields of each VM instruction `[Op, A, B, C]` are randomly permuted, making static analysis of the bytecode format itself non-trivial |
| **Encrypted Constants** | Strings and integers in the VM constants table are encrypted — strings use XOR + custom base encoding, integers use a deterministic PRNG mask |
| **Control Flow Flattening** | All execution is routed through a central binary-tree dispatcher loop, eliminating any readable branching structure |
| **Variable Renaming** | Every variable and function name is replaced with randomized hex-style identifiers |
| **String Encryption** | Hardcoded strings are XOR-encrypted with custom base encoding and decrypted only at runtime |
| **Global Hiding** | Global variable and function references are wrapped in proxy tables to prevent static name analysis |
| **Fracture** | Compound expressions are decomposed into cascading temporary variable assignments, fragmenting readable logic |
| **Beautify / Minify** | Optionally pretty-print or minify the final output |

---

## How It Works

```
Source Code
    │
    ▼
[Parse → AST]
    │
    ├─▶ Virtualization       — compiles to custom register-based VM bytecode
    ├─▶ Encrypt Strings      — XOR + custom base encoding, runtime decryption
    ├─▶ Hide Globals         — proxy/table wrapping of all global references
    ├─▶ Fracture             — expression decomposition into temp variables
    ├─▶ Control Flow         — binary-tree dispatcher loop
    ├─▶ Rename Variables     — hex identifier replacement
    │
    ▼
[AST → Code]
    │
    ▼
Obfuscated Output
```

The pipeline is fully configurable — each layer can be toggled independently.

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
    "Beautify": False,   # True to pretty-print, False to minify
}
```

### Running

1. Place your source file at `Input/Input.py`
2. Run:

```bash
python main.py
```

3. Collect the obfuscated output from `Output/Output.py`

### Skipping Virtualization on Specific Functions

Decorate any function with `@OBF_NO_VIRTUALIZE` to exclude it from the VM and keep it as native Python. It will still be accessible from within virtualized code via an obfuscated key registered in the global function table.

```python
@OBF_NO_VIRTUALIZE
def my_native_function():
    ...
```

---

## Planned Features

- **Mixed Boolean Arithmetic (MBA) expressions** — obfuscate integer constants and arithmetic into polynomial MBA expressions that resist simplification
- **Function splitting** — split individual functions into multiple fragments linked by obfuscated dispatch
- **Custom register VM enhancements** — built-in name hiding inside the VM, register cleanup (dead register overwriting), improved variable reuse tracking

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
