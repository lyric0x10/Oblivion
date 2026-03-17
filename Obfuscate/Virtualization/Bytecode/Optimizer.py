import random

class OptimizerModule:
    def __init__(self, Bytecode, Constants):
        #print(f"Input bytecode length: {len(Bytecode)} instructions")
        self.Bytecode = Bytecode
        self.Constants = Constants

        #    https://www.slideshare.net/slideshow/ch9c/2756109
        #
        #    Classic Examples of Local and Global Code Optimizations
        #    ------- Local -------                   ------- Global -------
        #    - Constant folding                      - Dead code elimination
        #    - Constant combining                    - Constant propagation
        #    - Strength reduction                    - Forward copy propagation
        #    - Constant propagation                  - Common subexpression elimination
        #    - Common subexpression elimination      - Code motion
        #    - Backward copy propagation             - Loop strength reduction
        #                                            - Induction variable elimination

    def Print_Bytecode(self):
        for I, Instr in enumerate(self.Bytecode):
            print(I, Instr)
            
        print("\n")

    def Optimize(self):
        self.Print_Bytecode()
        Jumps = self.Build_Jump_Map()
        
        self.Dead_Registers()
        
        self.Update_Jumps(Jumps)
        self.Print_Bytecode()
        
        return self.Bytecode

    def Build_Jump_Map(self):
        Jumps = []
        for Instr in self.Bytecode:
            Op = Instr[0]
            JumpToIndex, JumpId = None, random.randint(-900000000, 900000000)
            
            if Op == "JUMP":
                JumpToIndex = Instr[1]
                Instr[1] = JumpId
                
            elif Op in ("JUMP_IF_FALSE", "JUMP_IF_TRUE"):
                JumpToIndex = Instr[2] - 1
                Instr[2] = JumpId
            
            if JumpToIndex != None:
                self.Bytecode[JumpToIndex].append(JumpId)
                Jumps.append(JumpId)
        return Jumps
    
    def Update_Jumps(self, JumpIds):
        Jump_Map = {}
        for JumpId in JumpIds:
            for I, Instr in enumerate(self.Bytecode):
                # Use the index I to directly reference the bytecode list
                if Instr[-1] == JumpId:
                    if Instr[-2] == JumpId:
                        # Modify the list in-place
                        self.Bytecode[I] = Instr[:-2] + [I]
                
                    elif JumpId in list(Jump_Map.keys()):
                        # Modify the list in-place
                        self.Bytecode[I] = Instr[:-1] + [Jump_Map[JumpId]]
                    else:
                        # Modify the list in-place
                        self.Bytecode[I] = Instr[:-1]
                        Jump_Map[JumpId] = I
        
                        
            
    
    def Find_Used_Registers(self, Instr):
        Used = []
        for Reg in Instr:
            if isinstance(Reg, int):
                Used.append(Reg)
            elif isinstance(Reg, (tuple, list)):
                Used.extend(self.Find_Used_Registers(Reg))
    
        return Used
    
    def FindSourceRegisters(self, Instr):
        OpCodesNotAssigningToRegA = [
            "FOR_ITER",
            "JUMP",
            "JUMP_IF_FALSE",
            "JUMP_IF_TRUE",
            "RETURN_VALUE",
            "SET_BUILTIN",
            "STORE_SUBSCR"
        ]
        Op, A, B, C = (Instr + [None] * 4)[:4]
        if Op == "JUMP_IF_FALSE":
            return self.Find_Used_Registers([A])
        elif Op == "JUMP_IF_TRUE":
            return self.Find_Used_Registers([A])
        elif Op == "RETURN_VALUE":
            return self.Find_Used_Registers([A])
        elif Op == "SET_BUILTIN":
            return self.Find_Used_Registers([B])
        elif Op == "STORE_SUBSCR":
            return self.Find_Used_Registers([A, B, C])
        elif not Op in OpCodesNotAssigningToRegA:
            if Op == "LOAD_CONST":
                pass #   B is a const index, not register
            else:
                return self.Find_Used_Registers([B, C])

        return []                
            

    def Dead_Registers(self):
        LastReadMap = {}
        for I, Instr in enumerate(self.Bytecode):
            Op = Instr[0]
            
            Sources = self.FindSourceRegisters(Instr)
            for Reg in Sources:
                LastReadMap[Reg] = I

        B = self.Bytecode
        for I, R in enumerate(LastReadMap.keys()):
            B.insert(LastReadMap[R]+I+1, ["RESET_REGISTER", R])