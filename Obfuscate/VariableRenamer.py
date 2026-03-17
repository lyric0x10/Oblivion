import random
import string
from Obfuscate.Utils import Utils as UtilsModule

NOT_ALLOWED = {
    "if", "or", "in", "is", "and", "for", "while", "try", "except", "with",
    "as", "def", "class", "return", "import", "from", "pass", "break",
    "continue", "global", "nonlocal", "lambda", "yield", "raise", "assert",
    "del", "async", "await", "None", "True", "False", "self"
}
CHARS = string.ascii_letters
ALPHANUM = string.ascii_letters + string.digits

def GenerateVariable(Type = "Default", Length=6):
    if Type == "Default":
        return random.choice(CHARS) + "".join(random.choices(ALPHANUM, k=Length-1))
    elif Type == "Hexadecimal":
        return "_0x" + "".join(random.choices("0123456789abcdefABCDEF", k=Length-3))
    
class VariableRenamer:
    def __init__(self, Ast):
        self.Ast = Ast
        self.UsedNames = {}
        self.Utils = UtilsModule.Utils()
        self.Registry = {}

    def BuildRegistry(self, Tree, Path=None):
        if Path is None: 
            Path = []
        
        if isinstance(Tree, dict):
            for Key, Value in Tree.items():
                CurrentPath = Path + [Key]
                if isinstance(Value, str):
                    if Key not in self.Registry:
                        self.Registry[Key] = {}
                    if Value not in self.Registry[Key]:
                        self.Registry[Key][Value] = []
                    self.Registry[Key][Value].append(CurrentPath)
                else:
                    self.BuildRegistry(Value, CurrentPath)
        elif isinstance(Tree, list):
            for Index, Item in enumerate(Tree):
                self.BuildRegistry(Item, Path + [Index])

    def FindDefined(self):
        def SearchNode(Tree, CurrentPath=None):
            if CurrentPath is None: 
                CurrentPath = []
            Blocks = []

            if isinstance(Tree, dict) and "_type" in Tree:
                NodeType = Tree["_type"]

                def ExtractTargets(Node, Path):
                    Found = []
                    NodeKind = Node.get("_type")
                    if NodeKind == "Name":
                        Found.append(("variable", Path + ["id"], Node["id"]))
                    elif NodeKind == "Attribute":
                        ValueNode = Node.get("value")
                        if ValueNode and ValueNode.get("_type") == "Name" and ValueNode.get("id") == "self":
                            Found.append(("class_attr", Path + ["attr"], Node["attr"]))
                    elif NodeKind in ("Tuple", "List"):
                        for Index, Element in enumerate(Node.get("elts", [])):
                            Found.extend(ExtractTargets(Element, Path + ["elts", Index]))
                    return Found

                if NodeType == "Assign":
                    for Index, Target in enumerate(Tree.get("targets", [])):
                        Blocks.extend(ExtractTargets(Target, CurrentPath + ["targets", Index]))
                elif NodeType == "AnnAssign":
                    Blocks.extend(ExtractTargets(Tree["target"], CurrentPath + ["target"]))
                elif NodeType in ("FunctionDef", "AsyncFunctionDef"):
                    Blocks.append(("function", CurrentPath + ["name"], Tree["name"]))
                    ArgsObject = Tree.get("args", {})
                    for ArgType in ("args", "kwonlyargs", "posonlyargs"):
                        for Index, Arg in enumerate(ArgsObject.get(ArgType, [])):
                            Blocks.append(("parameter", CurrentPath + ["args", ArgType, Index, "arg"], Arg["arg"]))
                elif NodeType == "ClassDef":
                    Blocks.append(("class", CurrentPath + ["name"], Tree["name"]))
                elif NodeType in ("Global", "Nonlocal"):
                    for Index, Name in enumerate(Tree.get("names", [])):
                        Blocks.append((NodeType.lower(), CurrentPath + ["names", Index], Name))
                elif NodeType in ("For", "AsyncFor", "comprehension"):
                    Blocks.extend(ExtractTargets(Tree["target"], CurrentPath + ["target"]))
                elif NodeType == "ExceptHandler" and Tree.get("name"):
                    Blocks.append(("exception_var", CurrentPath + ["name"], Tree["name"]))
                elif NodeType == "withitem" and Tree.get("optional_vars"):
                    Blocks.extend(ExtractTargets(Tree["optional_vars"], CurrentPath + ["optional_vars"]))
                elif NodeType == "NamedExpr":
                    TargetNode = Tree["target"]
                    if TargetNode.get("_type") == "Name":
                        Blocks.append(("walrus_var", CurrentPath + ["target", "id"], TargetNode["id"]))

                for Key, Value in Tree.items():
                    if Key != "_type":
                        Blocks.extend(SearchNode(Value, CurrentPath + [Key]))
            elif isinstance(Tree, list):
                for Index, Item in enumerate(Tree):
                    Blocks.extend(SearchNode(Item, CurrentPath + [Index]))
            return Blocks

        return SearchNode(self.Ast)

    def GenerateName(self, ScopeId, Depth):
        if ScopeId not in self.UsedNames:
            self.UsedNames[ScopeId] = set()

        while True:
            Length = 7 if Depth >= 3 else random.randint(7, 9)
            NewName = GenerateVariable("Hexadecimal", Length)
            
            if NewName not in self.UsedNames[ScopeId] and NewName not in NOT_ALLOWED:
                self.UsedNames[ScopeId].add(NewName)
                return NewName

    def RenameVariables(self):
        self.BuildRegistry(self.Ast)
        DefinedVariables = self.FindDefined()

        TypeToField = {
            "function": "name", "class": "name", "parameter": "arg",
            "variable": "id", "comprehension_var": "id", "walrus_var": "id",
            "global": "id", "nonlocal": "id", "exception_var": "name",
            "class_attr": "attr"
        }

        for Type, Path, Name in DefinedVariables:
            if (Name.startswith("__") and Name.endswith("__")) or Name == "self":
                continue

            ScopeId = tuple(Path[: Path.index("body") + 1]) if "body" in Path else ()
            NewName = self.GenerateName(ScopeId, len(Path))
            
            TargetFields = ["attr", "value"] if Type == "class_attr" else ["name", "id", "arg"]
            
            for Field in TargetFields:
                PathsToUpdate = self.Registry.get(Field, {}).get(Name, [])
                for TargetPath in PathsToUpdate:
                    TargetNode = self.Ast
                    for Step in TargetPath[:-1]:
                        TargetNode = TargetNode[Step]
                    TargetNode[TargetPath[-1]] = NewName

        return self.Ast
    
    
# TODO
# Impliment variable reuse after determined to be dead/out of use.