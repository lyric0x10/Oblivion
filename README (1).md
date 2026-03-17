# Obfuscate

A Python source-code obfuscation engine exposed as a Flask REST API. It transforms Python scripts through a configurable multi-stage pipeline — from a custom bytecode VM to control-flow flattening, string encryption, and variable renaming — making reverse engineering significantly harder.

---

## Features

| Pass | Description |
|---|---|
| **Virtualization (VM)** | Compiles the entire script into a custom register-based bytecode VM with randomized opcodes, polymorphic instruction encoding, and encrypted constants. |
| **String Encryption** | Replaces every string literal with a runtime XOR + custom-base decryption call. |
| **Hide Globals** | Obfuscates global variable and built-in references through a hashed key indirection layer. |
| **Fracture** | Splits compound expressions into chains of single-operation temporary-variable assignments. |
| **Control Flow** | Flattens straight-line statement blocks into `while`-loop dispatch trees (binary-search over random state values). |
| **Variable Renaming** | Renames all local variables, function names, parameters, and class attributes to random hexadecimal-style identifiers. |
| **Output Formatting** | Final code is either minified (default) or pretty-printed via `ruff`. |

---

## Project Structure

```
Obfuscate/
├── Server.py                        # Flask API entry-point
├── VariableRenamer.py               # Rename variables / functions / parameters
├── ControlFlow.py                   # Control-flow flattening
│
├── Mangle/
│   ├── EncryptStrings.py            # String literal encryption
│   ├── Fracture.py                  # Expression fracturing
│   └── HideGlobals.py               # Global/built-in hiding
│
├── Utils/
│   ├── AST2Code.py                  # AST → source-code serialiser
│   ├── Parser.py                    # source → AST parser + minify/format helpers
│   └── Utils.py                     # Shared utilities (random strings, AST search)
│
└── Virtualization/
    ├── VM.py                        # VM code-generation orchestrator
    ├── Bytecode/
    │   ├── Generator.py             # AST → bytecode compiler
    │   ├── Optimizer.py             # Bytecode optimiser (dead-register elimination)
    │   └── InstructionPacking.py    # Binary pack/unpack + custom-base encoding
    └── Core/
        ├── Encryption.py            # XOR cipher + numeric encryption primitives
        ├── Mapping.py               # Opcode mapping + polymorphic instruction layout
        ├── Opnames.py               # Master list of VM opcode names
        └── Templates.py             # VM stub + if-chain code generation
```

---

## Requirements

See [`requirements.txt`](requirements.txt).

Install all dependencies with:

```bash
pip install -r requirements.txt
```

`ruff` is used for optional pretty-printing and must also be available on `PATH`:

```bash
pip install ruff
```

---

## Running the Server

```bash
python Server.py
```

The API starts on `http://127.0.0.1:5000` by default.

---

## API Reference

### `POST /Obfuscate`

**Request body (JSON):**

```json
{
  "Script": "<base64-encoded Python source>",
  "Settings": {
    "VM": {
      "Enabled": true,
      "RandomizeOpcodes": true,
      "PolymorphicInstructions": true,
      "EncryptConstants": true
    },
    "Fracture": true,
    "ControlFlow": true,
    "RenameVariables": true,
    "EncryptStrings": true,
    "HideGlobals": true,
    "Beautify": false
  }
}
```

All `Settings` fields are optional — the defaults shown above are used when omitted.

**Success response (200):**

```json
{
  "ObfuscatedScript": "<base64-encoded obfuscated Python source>"
}
```

**Error responses:**

```json
{ "Error": "Invalid input: <detail>" }      // 400
{ "Error": "Obfuscation failed: <detail>" } // 500
```

### Example (Python client)

```python
import base64, requests

code = open("my_script.py", "rb").read()

response = requests.post("http://127.0.0.1:5000/Obfuscate", json={
    "Script": base64.b64encode(code).decode(),
    "Settings": {
        "VM": {"Enabled": True, "RandomizeOpcodes": True,
               "PolymorphicInstructions": True, "EncryptConstants": True},
        "Fracture": True,
        "ControlFlow": True,
        "RenameVariables": True,
        "EncryptStrings": True,
        "HideGlobals": True,
        "Beautify": False
    }
})

result = response.json()
obfuscated = base64.b64decode(result["ObfuscatedScript"]).decode()
print(obfuscated)
```

---

## `@OBF_NO_VIRTUALIZE` Macro

Functions decorated with `@OBF_NO_VIRTUALIZE` (or named `OBF_NO_VIRTUALIZE`) are excluded from VM compilation and emitted as plain Python. They are registered in the VM's `Globals` dictionary under an obfuscated key so virtualized code can still call them cross-boundary.

```python
@OBF_NO_VIRTUALIZE
def my_native_function(x):
    return x * 2
```

---

## Pass Ordering

When multiple passes are enabled, they run in this fixed order:

1. **VM** — virtualize the AST first, then re-parse the emitted stub
2. **EncryptStrings** — encrypt remaining string literals
3. **HideGlobals** — hide global/built-in references
4. **Fracture** — split compound expressions
5. **ControlFlow** — flatten control flow
6. **RenameVariables** — rename all identifiers
7. **Minify / Beautify** — final formatting

---

## License

This project is unlicensed. Use at your own risk.
