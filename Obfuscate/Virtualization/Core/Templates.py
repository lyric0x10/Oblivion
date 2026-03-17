import re
import os
import random
import struct
from Obfuscate.Virtualization.Bytecode import InstructionPacking

def Format(Code, IndentDepth=1, Indent="    "):
    IndentStr = Indent * IndentDepth
    FormattedCode = ""
    for Block in Code.split("\n"):
        if Block.strip():
            FormattedCode += IndentStr + Block + "\n"
        else:
            FormattedCode += "\n"
    return FormattedCode

def RenameVar(CodeString, Target, Replacement):
    Pattern = r"\b" + re.escape(Target) + r"\b"
    return re.sub(Pattern, Replacement, CodeString)

def ApplyPolyLogic(Content, Settings, Opcodes, PolymorphismMap, OpName):
    if not Settings["PolymorphicInstructions"] or not PolymorphismMap:
        return Content, "Op"

    Old = ["Op", "A", "B", "C"]
    for i in range(4):
        Content = RenameVar(Content, Old[i], f"__TEMP_{i}__")

    op_code = Opcodes[OpName]
    for Index, Mapped in enumerate(PolymorphismMap[op_code]):
        Content = RenameVar(Content, f"__TEMP_{Mapped}__", Old[Index])

    Variable = Old[PolymorphismMap[op_code].index(0)]
    return Content, Variable

def BuilIfChain(Settings, UsedOps, Opcodes, PolymorphismMap=None, EncryptIdentifiers=None, Indent=0):
    BasePath = r"Obfuscate\Virtualization\Opcodes"
    IfMap = []

    for Op in UsedOps:
        IsEncrypted = (Op == "LOAD_CONST" and Settings.get("EncryptConstants"))
        FileName = "ENCRYPTED_LOAD_CONST.py" if IsEncrypted else f"{Op}.py"
        Path = os.path.join(BasePath, FileName)

        if not os.path.exists(Path):
            raise FileNotFoundError(f"TODO: implement '{FileName}' in '{BasePath}'")

        with open(Path, "r", encoding="utf8") as F:
            Content = F.read()

        if IsEncrypted:
            Content = Content.replace("__ENC_STR__", str(EncryptIdentifiers[0])).replace("__ENC_INT__", str(EncryptIdentifiers[1]))

        Content, Variable = ApplyPolyLogic(Content, Settings, Opcodes, PolymorphismMap, Op)

        IfMap.append([Variable, Opcodes[Op], Content])

    Code = ""
    for I, Op in enumerate(IfMap):
        If = "if" if I == 0 else "elif"
        Code += f"{If} {Op[0]} == {Op[1]}:\n{Format(Op[2])}"

    return Format(Code, Indent)


def SerializeNestedCode(Constants, Charset):
    """
    Recursively convert raw CodeObj dicts in a constants list into the
    encoded tuples the VM expects at runtime.

    By the time this function is called, every CodeObj dict's "Bytecode"
    field must already contain integer opcodes (produced by
    Mapping.MapBytecode / ProcessConstants).  SerializeNestedCode only
    handles serialisation — it does not apply opcode mapping itself.

    Both MAKE_FUNCTION and MAKE_CLASS constants are stored as a uniform
    (encoded_string, num_args) tuple so there is no ambiguity at the call
    site:

      - MAKE_FUNCTION (Op 66): SerializedCode, NumArgs = Constants[B]
      - MAKE_CLASS    (Op 20): CodeObj, _ = Constants[B]

    The "_bytecode_mapped" and "_is_function" keys are internal compiler
    markers; they are not packed into the serialised payload.
    """
    Result = []
    for Constant in Constants:
        if isinstance(Constant, dict) and "Bytecode" in Constant:
            NestedConstants = SerializeNestedCode(Constant["Constants"], Charset)
            VM_Data = [Constant["Bytecode"], NestedConstants, Constant["RegCount"]]
            Packed = InstructionPacking.Pack(VM_Data)
            Encoded = InstructionPacking.CustomBaseEncode(Packed, Charset)
            NumArgs = len(Constant.get("ArgNames", []))
            Result.append((Encoded, NumArgs))
        else:
            Result.append(Constant)
    return Result


def BuildVMStub(Data, Charset):
    # RegCount is now baked into the serialized payload so nested Run() calls
    # can read it dynamically rather than relying on a hardcoded literal.
    ProcessedConstants = SerializeNestedCode(Data["Constants"], Charset)
    VM_Data = [Data["Bytecode"], ProcessedConstants, Data["RegCount"]]

    Packed = InstructionPacking.Pack(VM_Data)
    Encoded_VM_Data = InstructionPacking.CustomBaseEncode(Packed, Charset)

    StubBody = f"""import struct

# Globals is the *function registry* only.
# It maps obfuscated string keys -> non-virtualized function references so
# GET_BUILTIN can resolve cross-boundary calls regardless of any renaming:
#     Globals['x$Qz1...'] = <possibly_renamed_func_ref>
#
# Regular VM variables are stored in / read from the module globals() dict
# so native (@OBF_NO_VIRTUALIZE) functions see them without any extra work:
#   STORE_GLOBAL : globals()[name] = value
#   GET_BUILTIN  : Globals -> globals() -> __builtins__  (layered lookup)
Globals = {{}}
_VMCache = {{}}

def CustomBaseDecode(EncodedText, Charset):
    if not EncodedText: return b""
    ZeroCount = 0
    for Char in EncodedText:
        if Char == Charset[0]: ZeroCount += 1
        else: break
    Base = len(Charset)
    Number = 0
    for Char in EncodedText[ZeroCount:]:
        Number = Number * Base + Charset.index(Char)
    if Number == 0: return b'\\x00' * ZeroCount
    ByteLength = (Number.bit_length() + 7) // 8
    return (b'\\x00' * ZeroCount) + Number.to_bytes(ByteLength, 'big')

def Unpack(Buffer, Offset=0):
    if Offset >= len(Buffer):
        raise ValueError("Unexpected end of buffer")

    Tag = Buffer[Offset]
    Offset += 1

    if Tag == 0x01:  # Integer
        if Offset + 4 > len(Buffer): return
        Length = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        if Offset + Length > len(Buffer): return
        Val = int.from_bytes(Buffer[Offset:Offset+Length], byteorder='big', signed=True)
        return Val, Offset + Length

    elif Tag == 0x02:  # String
        if Offset + 4 > len(Buffer): return
        Length = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        if Offset + Length > len(Buffer): return
        Val = Buffer[Offset:Offset+Length].decode('utf-8')
        return Val, Offset + Length

    elif Tag == 0x03:  # List
        if Offset + 4 > len(Buffer): return
        Count = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        Items = []
        for _ in range(Count):
            Val, Offset = Unpack(Buffer, Offset)
            Items.append(Val)
        return Items, Offset

    elif Tag == 0x04:  # Tuple
        if Offset + 4 > len(Buffer): return
        Count = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        Items = []
        for _ in range(Count):
            Val, Offset = Unpack(Buffer, Offset)
            Items.append(Val)
        return tuple(Items), Offset

    elif Tag == 0x05:  # Boolean
        if Offset + 1 > len(Buffer): return
        Val = bool(Buffer[Offset])
        return Val, Offset + 1

    elif Tag == 0x06:  # None
        return None, Offset

    elif Tag == 0x07:  # Float
        if Offset + 8 > len(Buffer): return
        Val = struct.unpack('>d', Buffer[Offset:Offset+8])[0]
        return Val, Offset + 8

    elif Tag == 0x08:  # Raw Bytes
        if Offset + 4 > len(Buffer): return
        Length = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        if Offset + Length > len(Buffer): return
        Val = bytes(Buffer[Offset:Offset+Length])
        return Val, Offset + Length

    elif Tag == 0x09:  # Dict
        if Offset + 4 > len(Buffer): return
        Count = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        Items = {{}}
        for _ in range(Count):
            Key, Offset = Unpack(Buffer, Offset)
            Value, Offset = Unpack(Buffer, Offset)
            Items[Key] = Value
        return Items, Offset


def Run(VM_Serialized, Args=None):
    _VM_CHARSET = "{Charset}"
    if VM_Serialized not in _VMCache:
        DecodedData = CustomBaseDecode(VM_Serialized, _VM_CHARSET)
        _VMCache[VM_Serialized] = Unpack(DecodedData)[0]

    Bytecode, Constants, RegCount = _VMCache[VM_Serialized]
    BuiltinDict = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__

    Registers = [None] * RegCount
    if Args:
        for I, Val in enumerate(Args):
            Registers[I] = Val

    CallStack = []
    Index = 0
    Len = len(Bytecode)
    ReturnValue = None

    while Index < Len:
        Op, A, B, C = Bytecode[Index]
{Data["IfChain"]}
        Index += 1

    return ReturnValue
"""

    RunCall = f'Run("{Encoded_VM_Data}")'
    return StubBody, RunCall