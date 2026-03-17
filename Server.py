from flask import Flask, request, jsonify
import base64

# Importing your custom modules
import Obfuscate.Utils.AST2Code as AST2Code
import Obfuscate.Utils.Parser as Parser
import Obfuscate.Virtualization.VM as VM_Module
import Obfuscate.VariableRenamer as VR_Module
import Obfuscate.ControlFlow as CF_Module
import Obfuscate.Mangle.Fracture as F_Module
import Obfuscate.Mangle.EncryptStrings as ES_Module
import Obfuscate.Mangle.HideGlobals as HG_Module

App = Flask(__name__)

@App.route('/Obfuscate', methods=['POST'])
def ObfuscateCode():
    Data = request.json
    
    # 1. Extract and Decode Input
    try:
        EncodedScript = Data.get("Script", "")
        # Decode b64 string to bytes, then to a python string
        RawCode = base64.b64decode(EncodedScript).decode('utf-8')
        
        # Extract UserSettings or use empty dict
        UserSettings = Data.get("Settings", {})
        
        # Build Settings Dictionary using PascalCase keys
        Settings = {
            "VM": UserSettings.get("VM", {"Enabled": True, "RandomizeOpcodes": True, "PolymorphicInstructions": True, "EncryptConstants": True}),
            "Fracture": UserSettings.get("Fracture", True),
            "ControlFlow": UserSettings.get("ControlFlow", True),
            "RenameVariables": UserSettings.get("RenameVariables", True),
            "EncryptStrings": UserSettings.get("EncryptStrings", True),
            "HideGlobals": UserSettings.get("HideGlobals", True),
            "Beautify": UserSettings.get("Beautify", False),
        }
    except Exception as Error:
        return jsonify({"Error": f"Invalid input: {str(Error)}"}), 400

    # 2. Processing Logic
    try:
        CurrentAST = Parser.Parse(RawCode)

        if Settings["VM"]["Enabled"]:
            VmCode = VM_Module.GenerateVM(CurrentAST, Settings["VM"])
            CurrentAST = Parser.Parse(VmCode)

        if Settings["EncryptStrings"]:
            CurrentAST = ES_Module.EncryptStrings(CurrentAST)
            
        if Settings["HideGlobals"]:
            CurrentAST = HG_Module.HideGlobals(CurrentAST)
            
        if Settings["Fracture"]:
            CurrentAST = F_Module.Fracture(CurrentAST, True)

        if Settings["ControlFlow"]:
            ControlFlowHandler = CF_Module.ControlFlow()
            CurrentAST = ControlFlowHandler.ControlFlow(CurrentAST)

        if Settings["RenameVariables"]:
            VariableRenamerHandler = VR_Module.VariableRenamer(CurrentAST)
            CurrentAST = VariableRenamerHandler.RenameVariables()

        # Final conversion
        OutputCode = AST2Code.AST2Code(CurrentAST)
        
        if Settings["Beautify"]:
            OutputCode = Parser.Format(OutputCode)
        else:
            OutputCode = Parser.Minify(OutputCode)

        # 3. Encode and Return Result
        ResultB64 = base64.b64encode(OutputCode.encode('utf-8')).decode('utf-8')
        return jsonify({"ObfuscatedScript": ResultB64})

    except Exception as Error:
        return jsonify({"Error": f"Obfuscation failed: {str(Error)}"}), 500

if __name__ == '__main__':
    App.run(debug=True, port=5000)