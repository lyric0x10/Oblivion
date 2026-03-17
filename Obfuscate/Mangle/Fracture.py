import random
import string
from Obfuscate.Utils import Parser, AST2Code

A2CModule = AST2Code.AST2Code_Module()

OpMap = {
    "UAdd": "+",
    "USub": "-",
    "Not": "not ",
    "Invert": "~"
}

class FractureTransformer:
    def __init__(self):
        self.TempVars = set()
        self.BufferStack = [[]]

    def GenVar(self):
        while True:
            Prefix = random.choice(string.ascii_uppercase)
            Suffix = "".join(random.choices(string.ascii_letters, k=19))
            Var = Prefix + Suffix
            if Var not in self.TempVars:
                self.TempVars.add(Var)
                return Var

    def TempVar(self, ValStr):
        if isinstance(ValStr, str) and ValStr in self.TempVars:
            return ValStr
            
        VarName = self.GenVar()
        AssignStr = f"{VarName} = {ValStr}"
        self.BufferStack[-1].append(AssignStr)
        
        return VarName

    def FractureBody(self, BodyNodes):
        OutputLines = []
        for Node in BodyNodes:
            self.BufferStack.append([])
            
            Res = self.HandleNode(Node)
            
            CurrentBuffer = self.BufferStack.pop()
            OutputLines.extend(CurrentBuffer)
            
            if Res:
                OutputLines.append(Res)
                
        return "\n".join(OutputLines)

    def HandleNode(self, Node):
        if isinstance(Node, list):
            return "\n".join(filter(None, [self.HandleNode(N) for N in Node]))
            
        if not isinstance(Node, dict):
            return str(Node) if Node is not None else ""

        Type = Node.get("_type")
        
        if Type in ("GeneratorExp", "ListComp", "SetComp", "DictComp"):
            return A2CModule.handle(Node)

        elif Type == "Module":
            return self.FractureBody(Node.get("body", []))
            
        elif Type == "Expr":
            return self.HandleNode(Node.get("value"))
            
        elif Type == "Call":
            FuncVar = self.TempVar(self.HandleNode(Node.get("func")))
            Args = Node.get("args", [])
            ArgList = [self.HandleNode(Arg) for Arg in Args]
            ArgStr = f"[{', '.join(ArgList)}]"
            ArgsVar = self.TempVar(ArgStr)
            
            Keywords = Node.get("keywords", [])
            KWList = [self.HandleNode(KW) for KW in Keywords]
            if KWList:
                return f"{FuncVar}(*{ArgsVar}, {', '.join(KWList)})"
            return f"{FuncVar}(*{ArgsVar})"
            
        elif Type == "Assign":
            TargetsStr = ", ".join(self.HandleNode(T) for T in Node.get("targets", []))
            ValueVar = self.TempVar(self.HandleNode(Node.get("value")))
            return f"{TargetsStr} = {ValueVar}"
            
        elif Type == "BinOp":
            OpNode = Node.get("op", {})
            OpChar = A2CModule.handle(OpNode) if isinstance(OpNode, dict) else str(OpNode)
            LeftVar = self.TempVar(self.HandleNode(Node.get("left")))
            RightVar = self.TempVar(self.HandleNode(Node.get("right")))
            return self.TempVar(f"({LeftVar} {OpChar} {RightVar})")
            
        elif Type == "UnaryOp":
            Operand = self.TempVar(self.HandleNode(Node.get("operand")))
            OpType = Node.get("op", {}).get("_type")
            OpChar = OpMap.get(OpType, "")
            return f"{OpChar}{Operand}"

        elif Type == "FunctionDef":
            Name = Node.get("name")
            Args = A2CModule.handle(Node.get("args"))
            Body = self.FractureBody(Node.get("body", []))
            IndentedBody = "\n".join(f"    {L}" for L in Body.splitlines())
            return f"def {Name}({Args}):\n{IndentedBody}"

        #elif Type == "If":
        #    TestVar = self.TempVar(self.HandleNode(Node.get("test")))
        #    Body = self.FractureBody(Node.get("body", []))
        #    IndentedBody = "\n".join(f"    {L}" for L in Body.splitlines())
        #    IfStr = f"if {TestVar}:\n{IndentedBody}"
        #    
        #    OrElse = Node.get("orelse", [])
        #    if OrElse:
        #        ElseBody = self.FractureBody(OrElse)
        #        IndentedElse = "\n".join(f"    {L}" for L in ElseBody.splitlines())
        #        IfStr += f"\nelse:\n{IndentedElse}"
        #    return IfStr

        elif Type == "While":
            Test = self.HandleNode(Node.get("test"))
            TestVar = self.TempVar(Test)
            Body = self.FractureBody(Node.get("body", []))
            IndentedBody = "\n".join(f"    {L}" for L in Body.splitlines())
            return f"while {TestVar}:\n{IndentedBody}\n    {TestVar}={Test}\n"

        elif Type == "For":
            IterVar = self.TempVar(self.HandleNode(Node.get("iter")))
            Target = self.HandleNode(Node.get("target"))
            Body = self.FractureBody(Node.get("body", []))
            IndentedBody = "\n".join(f"    {L}" for L in Body.splitlines())
            return f"for {Target} in {IterVar}:\n{IndentedBody}"

        elif Type == "Return":
            Val = Node.get("value")
            if Val:
                RetVar = self.TempVar(self.HandleNode(Val))
                return f"return {RetVar}"
            return "return"
            
        else:
            return A2CModule.handle(Node)

def Fracture(AST, ReturnAST=True):
    Transformer = FractureTransformer()
    
    if isinstance(AST, dict) and AST.get("_type") == "Module":
        FracturedCode = Transformer.HandleNode(AST)
    else:
        FracturedCode = Transformer.FractureBody(AST)
        
    if ReturnAST:
        return Parser.Parse(FracturedCode)
    return FracturedCode