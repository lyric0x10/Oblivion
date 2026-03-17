import random
from Obfuscate.Virtualization.Core import Encryption


def GenerateUniqueOpcode(Index, UsedValues):
    while True:
        NewId = Index + random.randint(-90000000, 90000000)
        if NewId not in UsedValues:
            UsedValues.add(NewId)
            return NewId

def CreatePolymorphicMapping():
    BaseLayout = [0, 1, 2, 3]
    return random.sample(BaseLayout, k=len(BaseLayout))

def ProcessOpcode(Name, Index, RandomizeOps, UsedValues):
    if RandomizeOps:
        return GenerateUniqueOpcode(Index, UsedValues)
    return Index

def BuildOpcodeMap(Opnames, RandomizeOps, Polymorphic):
    UsedValues = set()
    Opcodes = {}
    PolymorphismMap = {}

    for Index, Name in enumerate(Opnames):
        OpcodeValue = ProcessOpcode(Name, Index, RandomizeOps, UsedValues)
        Opcodes[Name] = OpcodeValue

        if Polymorphic:
            PolymorphismMap[OpcodeValue] = CreatePolymorphicMapping()

    return Opcodes, PolymorphismMap


def EncryptSingleConstant(Constant, EncryptConstants):
    if not EncryptConstants[0]:
        return Constant

    Identifiers = EncryptConstants[1]

    if type(Constant) is str:
        Encoded, Index = Encryption.Encode(Constant)
        return (Identifiers[0], Encoded, Index)

    if type(Constant) is int:
        Key = random.randint(1, 9000000)
        Encoded = Encryption.NumEncrypt(Constant, Key)
        return (Identifiers[1], Encoded, Key)

    return Constant


def TransformInstruction(Instruction, NewOp, InstructionPolymorphism, ForClassBody=False):
    """
    Convert a raw (string-op, …) instruction to its final integer-op form,
    optionally reordering fields via the polymorphism map.

    ForClassBody=True disables field reordering for the current instruction.
    This is mandatory for class-body scopes because the STORE_GLOBAL and
    SET_BUILTIN handlers rely on fixed field positions:
        A = register index  (integer)
        B = variable name   (string)
    Polymorphic reordering can swap those, producing a TypeError at runtime
    when the VM does  Registers[A]  with a string A, or  Namespace[B]  with
    an integer B.
    """
    UsePoly, PolyMap = InstructionPolymorphism
    NewInstruction = list(Instruction)
    NewInstruction[0] = NewOp
    for _ in range(4 - len(NewInstruction)):
        NewInstruction.append(random.randint(-90000000, 90000000))

    # Skip polymorphic field reordering for class-body instructions.
    if UsePoly and not ForClassBody:
        Mapping = PolyMap[NewOp]
        NewInstruction = [NewInstruction[Index] for Index in Mapping]

    return NewInstruction


def ProcessBytecode(Bytecode, OpMap, InstructionPolymorphism, ForClassBody=False):
    """
    Map every instruction in Bytecode from its string opcode name to the
    corresponding integer opcode value, applying the polymorphism permutation
    unless ForClassBody is True.

    If an instruction's opcode field is already an integer (i.e. it was
    mapped by a prior ProcessConstants / MapBytecode call) the instruction
    is returned as-is.  This makes the function idempotent and prevents the
    KeyError that occurs when VM.py's SerializeCodeObject calls MapBytecode
    on a nested code object that was already processed inline by
    ProcessConstants.
    """
    MappedBytecode = []
    for Instruction in Bytecode:
        OpName = Instruction[0]
        # Already mapped to an integer — do not re-process.
        if isinstance(OpName, int):
            MappedBytecode.append(Instruction)
            continue
        NewOp = OpMap[OpName]
        FinalInstruction = TransformInstruction(
            Instruction, NewOp, InstructionPolymorphism, ForClassBody
        )
        MappedBytecode.append(FinalInstruction)
    return MappedBytecode


def ProcessConstants(Constants, EncryptConstants, OpMap, InstructionPolymorphism):
    """
    Encrypt scalar constants and recursively map bytecode inside any nested
    CodeObj dicts (function and class bodies stored as constants).

    Class bodies are identified by  _is_function == False  and are compiled
    with ForClassBody=True so their STORE_GLOBAL / SET_BUILTIN instructions
    keep A and B in their canonical positions (register index, string name).

    A  _bytecode_mapped  guard prevents double-processing when the calling
    orchestrator already invokes MapBytecode on the same nested object.
    """
    MappedConstants = []
    for Constant in Constants:
        if isinstance(Constant, dict) and "Bytecode" in Constant:
            # Already processed by a parent MapBytecode call — skip.
            if Constant.get("_bytecode_mapped"):
                MappedConstants.append(Constant)
                continue

            IsClassBody = not Constant.get("_is_function", True)

            # Recurse: map nested bytecode, then map its own constants.
            NestedBytecode = ProcessBytecode(
                Constant["Bytecode"],
                OpMap,
                InstructionPolymorphism,
                ForClassBody=IsClassBody,
            )
            NestedConstants = ProcessConstants(
                Constant["Constants"],
                EncryptConstants,
                OpMap,
                InstructionPolymorphism,
            )

            MappedConstant = dict(Constant)
            MappedConstant["Bytecode"] = NestedBytecode
            MappedConstant["Constants"] = NestedConstants
            MappedConstant["_bytecode_mapped"] = True   # prevent double-processing
            MappedConstants.append(MappedConstant)

        else:
            MappedConstants.append(EncryptSingleConstant(Constant, EncryptConstants))

    return MappedConstants


def MapBytecode(Bytecode, Constants, OpMap, InstructionPolymorphism, EncryptConstants):
    """
    Top-level entry point.  Maps the outer bytecode (polymorphism enabled if
    configured) and recursively processes all nested code objects in Constants
    via ProcessConstants, which disables field reordering for class bodies.
    """
    MappedBytecode = ProcessBytecode(Bytecode, OpMap, InstructionPolymorphism)
    MappedConstants = ProcessConstants(Constants, EncryptConstants, OpMap, InstructionPolymorphism)
    return MappedBytecode, MappedConstants