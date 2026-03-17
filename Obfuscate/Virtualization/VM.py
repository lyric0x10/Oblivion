from Obfuscate.Utils import Parser, Utils, AST2Code
from Obfuscate.Virtualization.Bytecode import Generator, Optimizer, InstructionPacking
from Obfuscate.Virtualization.Core import Encryption, Mapping, Opnames, Templates
import random

Utils_Module = Utils.Utils()
AST2Code_Module = AST2Code.AST2Code_Module()


def SetupMapping(Settings):
    return Mapping.BuildOpcodeMap(
        Opnames.Opnames,
        Settings["RandomizeOpcodes"],
        Settings["PolymorphicInstructions"]
    )

def ProcessBytecode(VMModule, Opcodes, Settings, PolymorphismMap, EncryptIdentifiers):
    RawBytecode = VMModule.Decompile_AST()
    RawConstants = VMModule.Constants

    return Mapping.MapBytecode(
        RawBytecode,
        RawConstants,
        Opcodes,
        (Settings["PolymorphicInstructions"], PolymorphismMap),
        (Settings["EncryptConstants"], EncryptIdentifiers)
    )

def BuildDataPayload(VMModule, UsedOps, IfChain, MappedBytecode, MappedConstants):
    return {
        "RegCount": VMModule.RegCount,
        "UsedOps": UsedOps,
        "IfChain": IfChain,
        "Bytecode": MappedBytecode,
        "Constants": MappedConstants
    }

def SerializeCodeObject(CodeObj, Charset, Opcodes, PolymorphismMap, Settings, EncryptIdentifiers):
    MappedBytecode, MappedConstants = Mapping.MapBytecode(
        CodeObj["Bytecode"],
        CodeObj["Constants"],
        Opcodes,
        (Settings["PolymorphicInstructions"], PolymorphismMap),
        (Settings["EncryptConstants"], EncryptIdentifiers)
    )

    SerializedConstants = SerializeNestedFunctions(
        MappedConstants, Charset, Opcodes, PolymorphismMap, Settings, EncryptIdentifiers
    )

    Payload = [MappedBytecode, SerializedConstants, CodeObj["RegCount"]]
    Packed = InstructionPacking.Pack(Payload)
    Encoded = InstructionPacking.CustomBaseEncode(Packed, Charset)

    NumArgs = len(CodeObj["ArgNames"])
    return (Encoded, NumArgs)

def SerializeNestedFunctions(Constants, Charset, Opcodes, PolymorphismMap, Settings, EncryptIdentifiers):
    Result = []
    for Constant in Constants:
        if isinstance(Constant, dict) and "Bytecode" in Constant:
            Result.append(SerializeCodeObject(
                Constant, Charset, Opcodes, PolymorphismMap, Settings, EncryptIdentifiers
            ))
        else:
            Result.append(Constant)
    return Result


def No_Virtualize_Macro(AST):
    Function_Paths = Utils_Module.FindAllInstances(AST, "_type", "FunctionDef")
    No_Virtualize_Functions = []
    
    for Func_Path in reversed(Function_Paths):
        Block = AST
        
        for Key in Func_Path[:-2]:
            Block = Block[Key]
        
        Target_Node = Block[Func_Path[-2]]
        
        if Target_Node.get("name") == "OBF_NO_VIRTUALIZE":
            Block.pop(Func_Path[-2])
            
        Has_Macro = False
        for Index, Decorator in enumerate(Target_Node.get("decorator_list")):
            if Decorator.get("id") == "OBF_NO_VIRTUALIZE":
                Block[Func_Path[-2]]["decorator_list"].pop(Index)
                Has_Macro = True
                
        if Has_Macro:
            Block.pop(Func_Path[-2])
            No_Virtualize_Functions.append(Target_Node)
            
    return AST, No_Virtualize_Functions


def GenerateNameKeyMap(SkippedFunctions, Charset):
    Map = {}
    for Func in SkippedFunctions:
        Name = Func.get("name")
        if Name and Name != "OBF_NO_VIRTUALIZE":
            RandomBytes = bytes(
                random.randint(0, 255)
                for _ in range(random.randint(24, 48))
            )
            Map[Name] = InstructionPacking.CustomBaseEncode(RandomBytes, Charset)
    return Map


def PatchSkippedNames(RawBytecode, NameKeyMap):
    if not NameKeyMap:
        return RawBytecode

    Patched = []
    NameOpcodes = {"GET_BUILTIN", "STORE_GLOBAL"}
    for Instr in RawBytecode:
        if Instr[0] in NameOpcodes and len(Instr) > 2 and Instr[2] in NameKeyMap:
            Instr = list(Instr)
            Instr[2] = NameKeyMap[Instr[2]]
        Patched.append(Instr)
    return Patched


def GenerateRegistrationLines(SkippedFunctions, NameKeyMap):
    Lines = []
    for Func in SkippedFunctions:
        Name = Func.get("name")
        if Name and Name != "OBF_NO_VIRTUALIZE":
            Key = NameKeyMap[Name]
            Lines.append(f"Globals['{Key}'] = {Name}")
    return "\n".join(Lines)


def GenerateVM(AST, Settings):
    AST, SkippedFunctions = No_Virtualize_Macro(AST)

    Opcodes, PolymorphismMap = SetupMapping(Settings)
    EncryptIdentifiers = [random.randint(-90000000, 90000000) for i in range(2)]

    PossibleChars = InstructionPacking.PossibleChars
    Charset = "".join(random.sample(PossibleChars, random.randint(32, len(PossibleChars))))

    # Build the name→key map first so it can be applied during bytecode
    # generation (PatchSkippedNames) and again when emitting source
    # (GenerateRegistrationLines).  Both sites must use the exact same key.
    NameKeyMap = GenerateNameKeyMap(SkippedFunctions, Charset)

    VMModule = Generator.Virtualization(AST)

    # Patch raw bytecode BEFORE the opcode-mapping / polymorphism pass so
    # the obfuscated key ends up serialized into the payload.
    RawBytecode = VMModule.Decompile_AST()
    RawBytecode = PatchSkippedNames(RawBytecode, NameKeyMap)
    VMModule._patched_bytecode = RawBytecode   # hand back to ProcessBytecode below

    MappedBytecode, MappedConstants = Mapping.MapBytecode(
        RawBytecode,
        VMModule.Constants,
        Opcodes,
        (Settings["PolymorphicInstructions"], PolymorphismMap),
        (Settings["EncryptConstants"], EncryptIdentifiers),
    )

    MappedConstants = SerializeNestedFunctions(
        MappedConstants, Charset, Opcodes, PolymorphismMap, Settings, EncryptIdentifiers
    )

    UsedOps = list(VMModule.Get_All_Used_Opcodes())
    IfChain = Templates.BuilIfChain(
        Settings, UsedOps, Opcodes, PolymorphismMap, EncryptIdentifiers, 2
    )

    Data = BuildDataPayload(
        VMModule, UsedOps, IfChain, MappedBytecode, MappedConstants
    )

    VMStub, RunCall = Templates.BuildVMStub(Data, Charset)

    # Layout of the generated output:
    #
    #   <VM stub: CustomBaseDecode / Unpack / Run>
    #
    #   def algorithm(a): ...              ← skipped function definitions
    #   Globals['x$Qz1...'] = algorithm   ← obfuscated registration
    #
    #   Run("...")                          ← entry-point
    #
    # The variable renamer may rename `algorithm` → `a1` on the RHS;
    # the string key stays fixed and matches what is in the bytecode payload.
    if SkippedFunctions:
        SkippedSource = AST2Code_Module.run(SkippedFunctions)
        RegistrationLines = GenerateRegistrationLines(SkippedFunctions, NameKeyMap)
        return (
            VMStub
            + "\n\n"
            + SkippedSource
            + "\n"
            + RegistrationLines
            + "\n\n"
            + RunCall
        )

    return VMStub + "\n\n" + RunCall


# TODO
# 1. Built-in Hiding - ["GET_BUILTIN", DestReg, "print"] -> ["GET_BUILTIN", DestReg, "-O%A4-A%Oc"]
#       - Never convert encrypted built-in name back to original.
# 2. Register cleanup
#       - Overwrite registers that are detected to be no longer in use