import random
from Obfuscate.Utils import Parser, AST2Code, Utils

A2C_Module = AST2Code.AST2Code_Module()
Utils = Utils.Utils()

def Find_All_Instances(Dict, Key, Target):
    def SearchNode(Tree, Key, Target, CurrentPath=None):
        if CurrentPath is None:
            CurrentPath = []
        Blocks = []
        if type(Tree) == dict:
            Keys = Tree.keys()
            if Key in Keys:
                if Tree[Key] == Target:
                    Blocks.append(CurrentPath.copy() + [Key])
            for k in Keys:
                _Block = Tree[k]
                new_path = CurrentPath + [k]
                Blocks.extend(SearchNode(_Block, Key, Target, new_path))
        elif type(Tree) == list:
            for i, item in enumerate(Tree):
                new_path = CurrentPath + [i]
                Blocks.extend(SearchNode(item, Key, Target, new_path))
        return Blocks
    _ = SearchNode(Dict, Key, Target)
    return _

def FindAllBodies(AST):
    def SearchNode(Tree, CurrentPath=None, Depth=0):
        if CurrentPath is None: CurrentPath = []
        if Depth > 30: return []
        Blocks = []
        
        if isinstance(Tree, dict):
            if "body" in Tree and isinstance(Tree["body"], list):
                Blocks.append(CurrentPath + ["body"])
            
            for key in ["orelse", "finalbody"]:
                if key in Tree and isinstance(Tree[key], list) and Tree[key]:
                    Blocks.append(CurrentPath + [key])

            for k, v in Tree.items():
                Blocks.extend(SearchNode(v, CurrentPath + [k], Depth + 1))
        elif isinstance(Tree, list):
            for i, item in enumerate(Tree):
                Blocks.extend(SearchNode(item, CurrentPath + [i], Depth + 1))
        return Blocks
    return SearchNode(AST)

def Clamp(Num, Min, Max):
    return max(Min, min(Num, Max))


class ControlFlow:
    def _format(self, code, indent_depth=1, indent="    "):
        indent_str = indent * indent_depth

        _code = ""
        for block in code.split("\n"):
            _code += indent_str + block + "\n"

        return _code
    def Get_Vars(self):
        Assignments = Find_All_Instances(self.AST, "_type", "Assign")
        Found_Vars = [] 
        for Path in Assignments:
            Node = self.AST
            for Step in Path[:-1]:
                Node = Node[Step]
            for Target in Node.get("targets", []):
                if "id" in Target:
                    Found_Vars.append(str(Target["id"]))
        self.Defined_Vars = Found_Vars

    def Generate_Tree(self, Blocks, Variable_Name="State", StopValue="None"):
        Count = len(Blocks)
        Numbers = random.sample(range(int(-9000000000), int(9000000000)), Count)
        
        Processed_Blocks = []
        for Index in range(Count):
            Next_Val = Numbers[Index + 1] if Index + 1 < Count else StopValue
            Update_Str = f"\n{Variable_Name} = {Next_Val}"
            Processed_Blocks.append(Blocks[Index] + Update_Str)

        Sorted_Pairs = sorted([(Value, Original_Index) for Original_Index, Value in enumerate(Numbers)])

        def Build_Branch(Pairs, Indent_Level):
            Indent = "    " * Indent_Level
            
            if len(Pairs) == 1:
                _, Original_Index = Pairs[0]
                Current_Code = Processed_Blocks[Original_Index]
                return "\n".join([f"{Indent}{Line}" for Line in Current_Code.strip().split('\n')])

            Mid_Point = len(Pairs) // 2
            Left_Half = Pairs[:Mid_Point]
            Right_Half = Pairs[Mid_Point:]
            Pivot_Value = Right_Half[0][0]

            Tree_Lines = [
                f"{Indent}if {Variable_Name} < {Pivot_Value}:",
                Build_Branch(Left_Half, Indent_Level + 1),
                f"{Indent}else:",
                Build_Branch(Right_Half, Indent_Level + 1)
            ]
            return "\n".join(Tree_Lines)

        return Build_Branch(Sorted_Pairs, 0), Numbers[0]
    
    def Process_Block_List(self, BlockList):
        if not BlockList:
            return None

        StrBlocks = []
        for Node in BlockList:
            Type = Node["_type"]
            if Type == "For" or Type == "While":
                BreakVar = Utils.RandomString(20)
                BreakPaths = Find_All_Instances(Node, "_type", "Break")
                for Path in BreakPaths:
                    ChangeBreak = True
                    Block = Node
                    for Index in Path[:-2]:
                        Block = Block[Index]
                        
                        if type(Block) != dict:
                            continue
                            
                        b_type = Block.get("_type")
                        
                        if b_type == "For":
                            ChangeBreak = False
                            break
                        elif b_type == "While":
                            Loop = False
                            try:
                                if Block["test"]["left"]["id"] in self.ValueVariables:
                                    Loop = True
                            except:
                                pass
                            
                            if not Loop:
                                ChangeBreak = False
                                break

                    if ChangeBreak:
                        Block.insert(Block.index({'_type': 'Break'}), {'_type': 'Assign', 'targets': [{'_type': 'Name', 'id': BreakVar, 'ctx': {'_type': 'Store'}}], 'value': {'_type': 'Constant', 'value': True, 'kind': None}, 'type_comment': None})
                
                Node["body"].insert(0, {'_type': 'If', 'test': {'_type': 'Name', 'id': BreakVar, 'ctx': {'_type': 'Load'}}, 'body': [{'_type': 'Break'}], 'orelse': []})
                StrBlocks.append(f"\n{BreakVar} = False\n" + A2C_Module.handle(Node).strip())
            
            else:
                StrBlocks.append(A2C_Module.handle(Node).strip())

        FinalCode = ""
        if len(StrBlocks) > 0:
            ValueVariable, StopValue = Utils.RandomString(6), random.randint(-9000000000, 9000000000)
            self.ValueVariables.append(ValueVariable)
            TreeCode, FirstID = self.Generate_Tree(StrBlocks, ValueVariable, StopValue)
            FinalCode = f"{ValueVariable} = {FirstID}\n"
            FinalCode += f"while {ValueVariable} != {str(StopValue)}:\n"
            FinalCode += self._format(TreeCode, 1)

        try:
            return Parser.Parse(FinalCode)
        except Exception as e:
            print(f"Error parsing generated tree code: {e}")
            return None

    def ControlFlow(self, AST, ReturnAST=True):
        self.ValueVariables = []
        self.AST = AST
        self.Get_Vars()

        PBodies = sorted(FindAllBodies(AST), key=len, reverse=True)
        for PB in PBodies:
            AST_Block = AST
            for Key in PB[:-1]:
                AST_Block = AST_Block[Key]

            BlockList = AST_Block[PB[-1]]
            NewAST = self.Process_Block_List(BlockList)
            if NewAST:
                AST_Block[PB[-1]] = NewAST["body"] if isinstance(NewAST, dict) else NewAST

        if isinstance(AST, dict) and "body" in AST:
            NewAST = self.Process_Block_List(AST["body"])
            if NewAST: AST = NewAST
        elif isinstance(AST, list):
            NewAST = self.Process_Block_List(AST)
            if NewAST: AST = NewAST

        return AST if ReturnAST else A2C_Module.handle(AST)