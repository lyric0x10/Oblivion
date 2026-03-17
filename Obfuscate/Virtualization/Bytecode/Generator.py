from Obfuscate.Virtualization.Bytecode import Optimizer

class Virtualization:
    def __init__(self, AST):
        self.AST = AST
        self.Constants = []
        self.Variables = {}
        self.RegCount = 0
        self.Bytecode = []
        self.LoopStack = []
        self.Locals = self.Collect_Locals(AST)

    def Get_Register(self, Name):
        if Name not in self.Variables:
            self.Variables[Name] = self.RegCount
            self.RegCount += 1
        return self.Variables[Name]

    def New_Temp_Register(self):
        Reg = self.RegCount
        self.RegCount += 1
        return Reg

    def Collect_Locals(self, Body):
        Locals = set()
        for Node in Body:
            self._Walk_For_Assignments(Node, Locals)
        return Locals

    def _Extract_Names_Recursive(self, Target, Locals):
        T = Target["_type"]
        if T == "Name":
            Locals.add(Target["id"])
        elif T in ("Tuple", "List"):
            for Elt in Target["elts"]:
                self._Extract_Names_Recursive(Elt, Locals)
        elif T == "Starred":
            self._Extract_Names_Recursive(Target["value"], Locals)

    def _Walk_For_Assignments(self, Node, Locals):
        T = Node["_type"]
        if T == "Assign":
            for Target in Node["targets"]:
                self._Extract_Names_Recursive(Target, Locals)
        elif T == "AugAssign":
            self._Extract_Names_Recursive(Node["target"], Locals)
        elif T in ("For", "While", "If"):
            if T == "For":
                self._Extract_Names_Recursive(Node["target"], Locals)
            for SubNode in Node.get("body", []) + Node.get("orelse", []):
                self._Walk_For_Assignments(SubNode, Locals)
        elif T == "FunctionDef":
            Locals.add(Node["name"])
        elif T == "Try":
            for SubNode in Node.get("body", []) + Node.get("orelse", []) + Node.get("finalbody", []):
                self._Walk_For_Assignments(SubNode, Locals)
            for Handler in Node.get("handlers", []):
                if Handler.get("name"):
                    Locals.add(Handler["name"])
                for SubNode in Handler.get("body", []):
                    self._Walk_For_Assignments(SubNode, Locals)

    def Handle_Store_Target(self, Target, ValueReg):
        T = Target["_type"]

        if T == "Name":
            Name = Target["id"]
            if Name in self.Locals:
                DestReg = self.Get_Register(Name)
                self.Bytecode.append(["MOVE", DestReg, ValueReg])
            else:
                self.Bytecode.append(["SET_BUILTIN", Name, ValueReg])

        elif T == "Subscript":
            ObjReg = self.New_Temp_Register()
            self.Handle_Node(Target["value"], ObjReg)

            Slice_AST = Target["slice"]
            if Slice_AST["_type"] == "Tuple":
                KeyRegs = []
                for Elt in Slice_AST["elts"]:
                    EltReg = self.New_Temp_Register()
                    self.Handle_Node(Elt, EltReg)
                    KeyRegs.append(EltReg)
                KeyReg = KeyRegs
            else:
                KeyReg = self.New_Temp_Register()
                self.Handle_Node(Slice_AST, KeyReg)

            self.Bytecode.append(["STORE_SUBSCR", ObjReg, KeyReg, ValueReg])

        elif T == "Attribute":
            ObjReg = self.New_Temp_Register()
            self.Handle_Node(Target["value"], ObjReg)
            AttrName = Target["attr"]
            self.Bytecode.append(["STORE_ATTR", ObjReg, AttrName, ValueReg])

        elif T in ("Tuple", "List"):
            Elts = Target["elts"]

            StarredIndex = None
            for I, Elt in enumerate(Elts):
                if Elt["_type"] == "Starred":
                    StarredIndex = I
                    break

            if StarredIndex is None:
                for I, Elt in enumerate(Elts):
                    if I not in self.Constants:
                        self.Constants.append(I)
                    IdxConstIndex = self.Constants.index(I)

                    IdxReg = self.New_Temp_Register()
                    self.Bytecode.append(["LOAD_CONST", IdxReg, IdxConstIndex])

                    EltReg = self.New_Temp_Register()
                    self.Bytecode.append(["BINARY_SUBSCR", EltReg, ValueReg, IdxReg])

                    self.Handle_Store_Target(Elt, EltReg)
            else:
                NumBefore = StarredIndex
                NumAfter = len(Elts) - StarredIndex - 1

                for I in range(NumBefore):
                    if I not in self.Constants:
                        self.Constants.append(I)
                    IdxReg = self.New_Temp_Register()
                    self.Bytecode.append(["LOAD_CONST", IdxReg, self.Constants.index(I)])
                    EltReg = self.New_Temp_Register()
                    self.Bytecode.append(["BINARY_SUBSCR", EltReg, ValueReg, IdxReg])
                    self.Handle_Store_Target(Elts[I], EltReg)

                SliceStartReg = self.New_Temp_Register()
                if NumBefore not in self.Constants:
                    self.Constants.append(NumBefore)
                self.Bytecode.append(["LOAD_CONST", SliceStartReg, self.Constants.index(NumBefore)])

                SliceStopReg = self.New_Temp_Register()
                SliceStop = -NumAfter if NumAfter > 0 else None
                if SliceStop not in self.Constants:
                    self.Constants.append(SliceStop)
                self.Bytecode.append(["LOAD_CONST", SliceStopReg, self.Constants.index(SliceStop)])

                SliceReg = self.New_Temp_Register()
                self.Bytecode.append(["BUILD_SLICE", SliceReg, SliceStartReg, SliceStopReg])

                StarredValReg = self.New_Temp_Register()
                self.Bytecode.append(["BINARY_SUBSCR", StarredValReg, ValueReg, SliceReg])
                self.Handle_Store_Target(Elts[StarredIndex]["value"], StarredValReg)

                for I in range(NumAfter):
                    NegIdx = -(NumAfter - I)
                    if NegIdx not in self.Constants:
                        self.Constants.append(NegIdx)
                    IdxReg = self.New_Temp_Register()
                    self.Bytecode.append(["LOAD_CONST", IdxReg, self.Constants.index(NegIdx)])
                    EltReg = self.New_Temp_Register()
                    self.Bytecode.append(["BINARY_SUBSCR", EltReg, ValueReg, IdxReg])
                    self.Handle_Store_Target(Elts[StarredIndex + 1 + I], EltReg)

        else:
            raise NotImplementedError(f"Unsupported assignment target type: {T}")

    def Handle_Node(self, Node, TargetReg=None):
        Type = Node["_type"]

        if TargetReg is None and Type != "Module":
            TargetReg = self.New_Temp_Register()

        if Type == "Module":
            for Statement in Node["body"]:
                self.Handle_Node(Statement)

        elif Type == "Expr":
            self.Handle_Node(Node["value"])

        elif Type == "Constant":
            if Node["value"] not in self.Constants:
                self.Constants.append(Node["value"])
            ConstIndex = self.Constants.index(Node["value"])
            self.Bytecode.append(["LOAD_CONST", TargetReg, ConstIndex])

        elif Type == "Assign":
            ValueReg = self.New_Temp_Register()
            self.Handle_Node(Node["value"], ValueReg)
            for Target in Node["targets"]:
                self.Handle_Store_Target(Target, ValueReg)

        elif Type == "AugAssign":
            ValueReg = self.New_Temp_Register()
            self.Handle_Node(
                {
                    "_type": "BinOp",
                    "left": Node["target"],
                    "op": Node["op"],
                    "right": Node["value"],
                },
                ValueReg,
            )
            self.Handle_Store_Target(Node["target"], ValueReg)

        elif Type == "Name":
            VarName = Node["id"]
            if VarName in self.Locals:
                SourceReg = self.Get_Register(VarName)
                self.Bytecode.append(["MOVE", TargetReg, SourceReg])
            else:
                self.Bytecode.append(["GET_BUILTIN", TargetReg, VarName])

        elif Type == "BinOp":
            LeftReg = self.New_Temp_Register()
            RightReg = self.New_Temp_Register()
            self.Handle_Node(Node["left"], LeftReg)
            self.Handle_Node(Node["right"], RightReg)

            OpMap = {
                "Add": "ADD",
                "Sub": "SUB",
                "Mult": "MUL",
                "Div": "DIV",
                "Mod": "MOD",
                "Pow": "POW",
                "FloorDiv": "FLOORDIV",
                "LShift": "LSHIFT",
                "RShift": "RSHIFT",
                "BitOr": "OR",
                "BitXor": "XOR",
                "BitAnd": "AND"
            }
            OpName = "BINARY_" + OpMap[Node["op"]["_type"]]
            self.Bytecode.append([OpName, TargetReg, LeftReg, RightReg])

        elif Type == "Call":
            FuncReg = self.New_Temp_Register()
            self.Handle_Node(Node["func"], FuncReg)
            ArgRegisters = []
            for ArgNode in Node["args"]:
                ArgReg = self.New_Temp_Register()
                self.Handle_Node(ArgNode, ArgReg)
                ArgRegisters.append(ArgReg)
            self.Bytecode.append(["CALL", TargetReg, FuncReg, ArgRegisters])

        elif Type == "For":
            IterObjReg = self.New_Temp_Register()
            self.Handle_Node(Node["iter"], IterObjReg)

            IterReg = self.New_Temp_Register()
            self.Bytecode.append(["GET_ITER", IterReg, IterObjReg])

            LoopStart = len(self.Bytecode)

            ForIterInstr = ["FOR_ITER", TargetReg, IterReg, None]
            self.Bytecode.append(ForIterInstr)

            TargetName = Node["target"]["id"]
            VarReg = self.Get_Register(TargetName)
            self.Bytecode.append(["MOVE", VarReg, TargetReg])

            BreakJumps = []
            self.LoopStack.append((LoopStart, BreakJumps))

            for Statement in Node["body"]:
                self.Handle_Node(Statement)

            self.LoopStack.pop()

            self.Bytecode.append(["JUMP", LoopStart])

            LoopEnd = len(self.Bytecode)
            ForIterInstr[3] = LoopEnd

            for BreakJump in BreakJumps:
                BreakJump[1] = LoopEnd

        elif Type in ("List", "Tuple"):
            Elts = []
            for Elt in Node["elts"]:
                EltReg = self.New_Temp_Register()
                self.Handle_Node(Elt, EltReg)
                Elts.append(EltReg)

            self.Bytecode.append(["BUILD_LIST", TargetReg, Elts])

        elif Type == "Return":
            if Node["value"] is not None:
                ValueReg = self.New_Temp_Register()
                self.Handle_Node(Node["value"], ValueReg)
                self.Bytecode.append(["RETURN_VALUE", ValueReg])
            else:
                ValueReg = self.New_Temp_Register()
                self.Bytecode.append(["LOAD_NONE", ValueReg])
                self.Bytecode.append(["RETURN_VALUE", ValueReg])

        elif Type == "If":
            Test = Node["test"]
            Body = Node["body"]
            OrElse = Node.get("orelse", [])

            CondReg = self.New_Temp_Register()
            self.Handle_Node(Test, CondReg)

            JumpIfFalseInstr = ["JUMP_IF_FALSE", CondReg, None]
            self.Bytecode.append(JumpIfFalseInstr)

            for Statement in Body:
                self.Handle_Node(Statement)

            if OrElse:
                JumpOverElseInstr = ["JUMP", None]
                self.Bytecode.append(JumpOverElseInstr)

                JumpIfFalseInstr[2] = len(self.Bytecode)

                for Statement in OrElse:
                    self.Handle_Node(Statement)

                JumpOverElseInstr[1] = len(self.Bytecode)
            else:
                JumpIfFalseInstr[2] = len(self.Bytecode)

        elif Type == "IfExp":
            Test   = Node["test"]
            Body   = Node["body"]
            OrElse = Node["orelse"]

            CondReg = self.New_Temp_Register()
            self.Handle_Node(Test, CondReg)

            JumpIfFalseInstr = ["JUMP_IF_FALSE", CondReg, None]
            self.Bytecode.append(JumpIfFalseInstr)

            self.Handle_Node(Body, TargetReg)

            JumpOverElseInstr = ["JUMP", None]
            self.Bytecode.append(JumpOverElseInstr)
            JumpIfFalseInstr[2] = len(self.Bytecode)

            self.Handle_Node(OrElse, TargetReg)
            JumpOverElseInstr[1] = len(self.Bytecode)

        elif Type == "Compare":
            OpMap = {
                "Eq": "EQ",
                "NotEq": "NE",
                "Lt": "LT",
                "LtE": "LTE",
                "Gt": "GT",
                "GtE": "GTE",
                "Is": "IS",
                "IsNot": "ISNOT",
                "In": "IN",
                "NotIn": "NOTIN",
            }

            LeftReg = self.New_Temp_Register()
            self.Handle_Node(Node["left"], LeftReg)

            if len(Node["ops"]) == 1:
                RightReg = self.New_Temp_Register()
                self.Handle_Node(Node["comparators"][0], RightReg)

                OpType = Node["ops"][0]["_type"]
                OpName = "COMPARE_" + OpMap[OpType]
                self.Bytecode.append([OpName, TargetReg, LeftReg, RightReg])

            else:
                raise NotImplementedError("Chained comparisons not yet supported")

        elif Type == "While":
            Test = Node["test"]
            Body = Node["body"]

            LoopStart = len(self.Bytecode)

            CondReg = self.New_Temp_Register()
            self.Handle_Node(Test, CondReg)

            JumpIfFalseInstr = ["JUMP_IF_FALSE", CondReg, None]
            self.Bytecode.append(JumpIfFalseInstr)

            BreakJumps = []
            self.LoopStack.append((LoopStart, BreakJumps))

            for Statement in Body:
                self.Handle_Node(Statement)

            self.LoopStack.pop()

            self.Bytecode.append(["JUMP", LoopStart])

            LoopEnd = len(self.Bytecode)
            JumpIfFalseInstr[2] = LoopEnd

            for BreakJump in BreakJumps:
                BreakJump[1] = LoopEnd

        elif Type == "BoolOp":
            OpType = Node["op"]["_type"]
            Values = Node["values"]
            ExitJumps = []

            for I, ValNode in enumerate(Values):
                self.Handle_Node(ValNode, TargetReg)

                if I < len(Values) - 1:
                    if OpType == "Or":
                        Jump = ["JUMP_IF_TRUE", TargetReg, None]
                    else:
                        Jump = ["JUMP_IF_FALSE", TargetReg, None]

                    self.Bytecode.append(Jump)
                    ExitJumps.append(Jump)

            EndIndex = len(self.Bytecode)
            for JumpInstr in ExitJumps:
                JumpInstr[2] = EndIndex

        elif Type == "UnaryOp":
            OpMap = {"UAdd": "ADD", "USub": "SUB", "Invert": "INV", "Not": "NOT"}
            Op = Node["op"]["_type"]
            Operand = Node["operand"]

            ValueReg = self.New_Temp_Register()
            self.Handle_Node(Operand, ValueReg)

            self.Bytecode.append(["UNARY_" + OpMap[Op], TargetReg, ValueReg])

        elif Type == "Subscript":
            Value = Node["value"]
            Slice_AST, Slice = Node["slice"], None

            ValueReg = self.New_Temp_Register()
            self.Handle_Node(Value, ValueReg)

            if Slice_AST["_type"] == "Tuple":
                Slice = []
                for Elt in Node["elts"]:
                    EltReg = self.New_Temp_Register()
                    self.Handle_Node(Elt, EltReg)
                    Slice.append(EltReg)
            else:
                SliceReg = self.New_Temp_Register()
                self.Handle_Node(Slice_AST, SliceReg)
                Slice = SliceReg

            self.Bytecode.append(["BINARY_SUBSCR", TargetReg, ValueReg, Slice])

        elif Type == "Attribute":
            Value = Node["value"]
            Attr = Node["attr"]

            ValueReg = self.New_Temp_Register()
            self.Handle_Node(Value, ValueReg)

            self.Bytecode.append(["LOAD_ATTR", TargetReg, ValueReg, Attr])

        elif Type == "Pass":
            pass

        elif Type == "Dict":
            Keys = Node["keys"]
            Values = Node["values"]
            KeyValueRegs = []

            for I in range(len(Keys)):
                if Keys[I] is None:
                    UnpackReg = self.New_Temp_Register()
                    self.Handle_Node(Values[I], UnpackReg)
                    KeyValueRegs.append((None, UnpackReg))
                else:
                    KeyReg = self.New_Temp_Register()
                    ValReg = self.New_Temp_Register()
                    self.Handle_Node(Keys[I], KeyReg)
                    self.Handle_Node(Values[I], ValReg)
                    KeyValueRegs.append((KeyReg, ValReg))

            self.Bytecode.append(["BUILD_MAP", TargetReg, KeyValueRegs])

        elif Type == "Break":
            if not self.LoopStack:
                raise SyntaxError("Break outside of loop")
            BreakJump = ["JUMP", None]
            self.Bytecode.append(BreakJump)
            self.LoopStack[-1][1].append(BreakJump)

        elif Type == "Continue":
            if not self.LoopStack:
                raise SyntaxError("Continue outside of loop")
            ContinueTarget = self.LoopStack[-1][0]
            self.Bytecode.append(["JUMP", ContinueTarget])

        elif Type == "Try":
            Body = Node["body"]
            Handlers = Node["handlers"]
            OrElse = Node.get("orelse", [])
            FinalBody = Node.get("finalbody", [])

            SetupFinallyInstr = None
            if FinalBody:
                SetupFinallyInstr = ["SETUP_FINALLY", None]
                self.Bytecode.append(SetupFinallyInstr)

            SetupExceptInstr = ["SETUP_EXCEPT", None]
            self.Bytecode.append(SetupExceptInstr)

            for Stmt in Body:
                self.Handle_Node(Stmt)

            self.Bytecode.append(["POP_BLOCK"])

            for Stmt in OrElse:
                self.Handle_Node(Stmt)

            JumpPastHandlers = ["JUMP", None]
            self.Bytecode.append(JumpPastHandlers)

            SetupExceptInstr[1] = len(self.Bytecode)

            HandlerEndJumps = []
            for Handler in Handlers:
                ExcType = Handler["type"]
                ExcName = Handler["name"]
                HandlerBody = Handler["body"]

                SkipHandlerJump = None
                if ExcType is not None:
                    TypeReg = self.New_Temp_Register()
                    self.Handle_Node(ExcType, TypeReg)
                    MatchReg = self.New_Temp_Register()
                    self.Bytecode.append(["EXCEPT_MATCH", MatchReg, TypeReg])
                    SkipHandlerJump = ["JUMP_IF_FALSE", MatchReg, None]
                    self.Bytecode.append(SkipHandlerJump)

                if ExcName is not None:
                    self.Locals.add(ExcName)
                    NameReg = self.Get_Register(ExcName)
                    self.Bytecode.append(["STORE_EXCEPTION_AS", NameReg])

                for Stmt in HandlerBody:
                    self.Handle_Node(Stmt)

                self.Bytecode.append(["POP_EXCEPT"])

                EndJump = ["JUMP", None]
                self.Bytecode.append(EndJump)
                HandlerEndJumps.append(EndJump)

                if SkipHandlerJump is not None:
                    SkipHandlerJump[2] = len(self.Bytecode)

            self.Bytecode.append(["RAISE_EXCEPTION"])

            AfterHandlers = len(self.Bytecode)
            JumpPastHandlers[1] = AfterHandlers
            for J in HandlerEndJumps:
                J[1] = AfterHandlers

            if SetupFinallyInstr is not None:
                self.Bytecode.append(["POP_BLOCK"])
                SetupFinallyInstr[1] = len(self.Bytecode)
                for Stmt in FinalBody:
                    self.Handle_Node(Stmt)
                self.Bytecode.append(["END_FINALLY"])

        elif Type == "Lambda":
            ArgsNode = Node["args"]
            BodyNode = Node["body"]

            AllArgNodes = (
                ArgsNode.get("posonlyargs", []) +
                ArgsNode.get("args", [])
            )
            ArgNames = [A["arg"] for A in AllArgNodes]

            if ArgsNode.get("vararg"):
                ArgNames.append(ArgsNode["vararg"]["arg"])

            ArgNames += [A["arg"] for A in ArgsNode.get("kwonlyargs", [])]

            if ArgsNode.get("kwarg"):
                ArgNames.append(ArgsNode["kwarg"]["arg"])

            LambdaBodyStmt = [{"_type": "Return", "value": BodyNode}]

            SubGen = Virtualization(LambdaBodyStmt)
            for ArgName in ArgNames:
                SubGen.Locals.add(ArgName)
                SubGen.Get_Register(ArgName)
            SubGen.Decompile_AST()

            DefaultRegs = []
            for DefaultNode in ArgsNode.get("defaults", []):
                DefaultReg = self.New_Temp_Register()
                self.Handle_Node(DefaultNode, DefaultReg)
                DefaultRegs.append(DefaultReg)

            CodeObj = {
                "_is_function": True,
                "Bytecode": SubGen.Bytecode,
                "Constants": SubGen.Constants,
                "ArgNames": ArgNames,
                "RegCount": SubGen.RegCount,
            }
            CodeIndex = len(self.Constants)
            self.Constants.append(CodeObj)

            self.Bytecode.append(["MAKE_FUNCTION", TargetReg, CodeIndex, DefaultRegs])

        elif Type == "FunctionDef":
            FuncName = Node["name"]
            ArgsNode = Node["args"]
            Body = Node["body"]

            AllArgNodes = (
                ArgsNode.get("posonlyargs", []) +
                ArgsNode.get("args", [])
            )
            ArgNames = [A["arg"] for A in AllArgNodes]

            if ArgsNode.get("vararg"):
                ArgNames.append(ArgsNode["vararg"]["arg"])

            ArgNames += [A["arg"] for A in ArgsNode.get("kwonlyargs", [])]

            if ArgsNode.get("kwarg"):
                ArgNames.append(ArgsNode["kwarg"]["arg"])

            SubGen = Virtualization(Body)
            for ArgName in ArgNames:
                SubGen.Locals.add(ArgName)
                SubGen.Get_Register(ArgName)
            SubGen.Decompile_AST()

            DefaultRegs = []
            for DefaultNode in ArgsNode.get("defaults", []):
                DefaultReg = self.New_Temp_Register()
                self.Handle_Node(DefaultNode, DefaultReg)
                DefaultRegs.append(DefaultReg)

            CodeObj = {
                "_is_function": True,
                "Bytecode": SubGen.Bytecode,
                "Constants": SubGen.Constants,
                "ArgNames": ArgNames,
                "RegCount": SubGen.RegCount,
            }
            CodeIndex = len(self.Constants)
            self.Constants.append(CodeObj)

            FuncReg = self.New_Temp_Register()
            self.Bytecode.append(["MAKE_FUNCTION", FuncReg, CodeIndex, DefaultRegs])

            # Always publish the function to Globals by name so that recursive
            # calls inside the function body can resolve it via GET_BUILTIN.
            # Each new Run() frame has a fresh register file; without this the
            # recursive lookup returns None and the CALL opcode crashes.
            self.Bytecode.append(["STORE_GLOBAL", FuncReg, FuncName])

            if FuncName in self.Locals:
                DestReg = self.Get_Register(FuncName)
                self.Bytecode.append(["MOVE", DestReg, FuncReg])
            else:
                self.Bytecode.append(["SET_BUILTIN", FuncName, FuncReg])

        elif Type == "JoinedStr":
            Values = []
            for Value in Node["values"]:
                ValueReg = self.New_Temp_Register()
                self.Handle_Node(Value, ValueReg)
                Values.append(ValueReg)

            self.Bytecode.append(["BUILD_STRING", TargetReg, Values])

        elif Type == "FormattedValue":
            Value = Node["value"]
            Conversion = Node["conversion"]
            Format_Spec = Node["format_spec"]

            ValueReg = self.New_Temp_Register()
            self.Handle_Node(Value, ValueReg)

            self.Bytecode.append(["FORMAT_VALUE", TargetReg, ValueReg, [Conversion, Format_Spec]])

        elif Type == "Import":
            Names = Node["names"]
            for Name in Names:
                self.Bytecode.append(["IMPORT_NAME", Name["name"], Name["asname"]])

        elif Type == "Assert":
            TestReg = self.New_Temp_Register()
            self.Handle_Node(Node["test"], TestReg)

            MsgReg = None
            if Node["msg"] != None:
                MsgReg = self.New_Temp_Register()
                self.Handle_Node(Node["msg"], MsgReg)

            self.Bytecode.append(["ASSERT", TestReg, MsgReg])

        elif Type == "ClassDef":
            ClassName = Node["name"]
            Bases     = Node.get("bases", [])
            Body      = Node["body"]

            # ---------------------------------------------------------------
            # Class bodies are compiled into their own sub-generator.
            # _is_function=False signals Mapping.ProcessConstants to disable
            # polymorphic field reordering for every instruction in this scope
            # (and any scopes nested inside it that are also class bodies).
            #
            # Why this matters:
            #   STORE_GLOBAL and SET_BUILTIN handlers in Run() expect
            #       A = register index  (int)
            #       B = variable name   (str)
            #   in their canonical positions.  If the polymorphism pass
            #   permutes those positions, A becomes a str and Registers[A]
            #   raises  TypeError: list indices must be integers or slices,
            #   not str.
            #
            # Methods (FunctionDef) inside the class body set _is_function=True
            # in their own nested CodeObj, so they are handled correctly by the
            # same recursive logic in ProcessConstants.
            # ---------------------------------------------------------------
            SubGen = Virtualization(Body)
            SubGen.Decompile_AST()

            CodeObj = {
                "_is_function": False,   # ← tells the mapper: no poly reorder
                "Bytecode":  SubGen.Bytecode,
                "Constants": SubGen.Constants,
                "ArgNames":  [],
                "RegCount":  SubGen.RegCount,
            }
            CodeIndex = len(self.Constants)
            self.Constants.append(CodeObj)

            BaseRegs = []
            for BaseNode in Bases:
                BaseReg = self.New_Temp_Register()
                self.Handle_Node(BaseNode, BaseReg)
                BaseRegs.append(BaseReg)

            ClassReg = self.New_Temp_Register()
            self.Bytecode.append(["MAKE_CLASS", ClassReg, CodeIndex, BaseRegs])

            self.Bytecode.append(["STORE_GLOBAL", ClassReg, ClassName])

            if ClassName in self.Locals:
                DestReg = self.Get_Register(ClassName)
                self.Bytecode.append(["MOVE", DestReg, ClassReg])
            else:
                self.Bytecode.append(["SET_BUILTIN", ClassName, ClassReg])

        else:
            raise NotImplementedError(f"Unsupported AST node type: {Type}")

    def Decompile_AST(self):
        self.Bytecode = []
        self.Handle_Node({"_type": "Module", "body": self.AST})
        return self.Bytecode

    def Get_All_Used_Opcodes(self):
        Ops = set()
        self._Collect_Opcodes(self.Bytecode, self.Constants, Ops)
        return Ops

    def _Collect_Opcodes(self, Bytecode, Constants, Ops):
        for Instr in Bytecode:
            Ops.add(Instr[0])
        # Recurse into any nested code-object dicts stored in Constants
        for Constant in Constants:
            if isinstance(Constant, dict) and "Bytecode" in Constant:
                self._Collect_Opcodes(Constant["Bytecode"], Constant["Constants"], Ops)