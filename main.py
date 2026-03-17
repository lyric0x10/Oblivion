import Obfuscate.Utils.Utils as Utils_Module
import Obfuscate.Utils.AST2Code as AST2Code
import Obfuscate.Utils.Parser as Parser
import Obfuscate.Virtualization.VM as VM_Module
import Obfuscate.VariableRenamer as VR_Module
import Obfuscate.ControlFlow as CF_Module
import Obfuscate.Mangle.Fracture as F_Module
import Obfuscate.Mangle.EncryptStrings as ES_Module
import Obfuscate.Mangle.HideGlobals as HG_Module

def Notification(Message):
    print(f"[-] {Message}")


Parse = Parser.Parse

Input_Path = r"Input\Input.py"
Output_Path = r"Output\Output.py"
GenerateCFG = False



Code = open(Input_Path).read()

AST = Parser.Parse(Code)
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
    "Beautify": False,
}

    
if Settings["VM"]["Enabled"]:
    Notification("Virtualizing code")
    VM_Code = VM_Module.GenerateVM(AST, Settings["VM"])
    AST = Parse(VM_Code)

if Settings["Encrypt Strings"]:
    Notification("Encrypting Strings")
    AST = ES_Module.EncryptStrings(AST)
    
if Settings["Hide Globals"]:
    Notification("Hiding Globals")
    AST = HG_Module.HideGlobals(AST)

    
if Settings["Fracture"]:
    Notification("Fracturing code")
    AST = F_Module.Fracture(AST, True)

if Settings["Control Flow"]:
    Notification("Adding Control Flow")
    CF = CF_Module.ControlFlow()
    AST = CF.ControlFlow(AST)

if Settings["Rename Variables"]:
    Notification("Renaming Variables")
    VR = VR_Module.VariableRenamer(AST)
    AST = VR.RenameVariables()

Code = AST2Code.AST2Code(AST)
if Settings["Beautify"]:
    Code = Parser.Format(Code)
else:
    Code = Parser.Minify(Code)


open(Output_Path, "w").write(Code)

if GenerateCFG:
    import python_ta.cfg as cfg

    cfg.generate_cfg(Output_Path)
