from ..Utils import Parser

class AST2Code_Module:
    def __init__(self):
        pass

    def is_number(self, value):
        if isinstance(value, bool):
            return False
        
        if isinstance(value, (int, float, complex)):
            return True

        return False

    def _format(self, code, indent_depth=1, indent="    "):
        indent = indent * indent_depth

        _code = ""
        for block in code.split("\n"):
            _code += indent + block + "\n"

        return _code

    def handle(self, ast):
        code = ""
        try:
            _type = ast["_type"]
        except Exception as E:
            print("Exception",E)
            return ast
        if _type == "Module":
            code = self.run(ast["body"])
            return code
        elif _type == "Expr":
            expr = self.handle(ast["value"])
            return f"{expr}"
        elif _type == "Call":
            func = ast["func"]
            args = ast["args"]
            keywords = ast["keywords"]

            f = self.handle(func)
            parts = []

            for arg in args:
                parts.append(str(self.handle(arg)))

            for kw in keywords:
                parts.append(str(self.handle(kw)))

            a = ", ".join(parts)
            code = f"{f}({a})"
        elif _type == "Name":
            Code = ast["id"]
            return Code
        elif _type == "Constant":
            value = ast["value"]
            if self.is_number(value):
                return str(value)

            if isinstance(value, bool):
                return "True" if value else "False"

            if value is None:
                return "None"

            if value is Ellipsis:
                return "..."

            if ast["kind"] == "NotString":
                return value
            return repr(value)

        elif _type == "keyword":
            arg = ast["arg"]
            value = self.handle(ast["value"])
            if arg is None:
                return f"**{value}"
            else:
                return f"{arg}={value}"

        elif _type == "Import":
            names, _n = "", ast["names"]
            for index, name in enumerate(_n):
                if index == len(_n) - 1:
                    names += str(self.handle(name))
                else:
                    names += str(self.handle(name)) + ", "
            return f"import {names}"
        elif _type == "alias":
            name = ast["name"]
            asname = ast.get("asname")
            if asname:
                return f"{name} as {asname}"
            return name
        elif _type == "ImportFrom":
            module = ast["module"]
            level = ast["level"]
            level_s = "." * level
            names, _n = "", ast["names"]
            for index, name in enumerate(_n):
                if index == len(_n) - 1:
                    names += str(self.handle(name))
                else:
                    names += str(self.handle(name)) + ", "

            return f"from {level_s}{module} import {names}"
        elif _type == "Assign":
            targets, _t = "", ast["targets"]
            value = self.handle(ast["value"])

            for index, target in enumerate(_t):
                if index == len(_t) - 1:
                    targets += str(self.handle(target))
                else:
                    targets += str(self.handle(target)) + ", "

            return f"{targets} = {value}"
        elif _type == "Tuple":
            ctx = ast["ctx"]["_type"]
            names, _n = "", ast["elts"]
            for index, name in enumerate(_n):
                if index == len(_n) - 1:
                    names += str(self.handle(name))
                else:
                    names += str(self.handle(name)) + ", "
            if ctx == "Store":
                return names
            else:
                return f"({names})"
        elif _type == "BinOp":
            left, right = self.handle(ast["left"]), self.handle(ast["right"])
            op = self.handle(ast["op"])
            return f"({left} {op} {right})"
        elif _type == "Add":
            return "+"
        elif _type == "List":
            data, _d = "", ast["elts"]
            for index, d in enumerate(_d):
                if index == len(_d) - 1:
                    data += str(self.handle(d))
                else:
                    data += str(self.handle(d)) + ", "
            return f"[{data}]"
        elif _type == "Attribute":
            value = self.handle(ast["value"])
            attr = ast["attr"]

            return f"{value}.{attr}"
        elif _type == "ListComp":
            elt = self.handle(ast["elt"])
            generators, _g = "", ast["generators"]
            for index, g in enumerate(_g):
                if index == len(_g) - 1:
                    generators += str(self.handle(g))
                else:
                    generators += str(self.handle(g)) + ", "

            return f"[{elt} {generators}]"
        elif _type == "Pow":
            return "**"

        elif _type == "comprehension":
            target = self.handle(ast["target"])
            _iter = self.handle(ast["iter"])
            ifs, _i = "", ast["ifs"]
            for index, i in enumerate(_i):
                if index == len(_i) - 1:
                    ifs += str(self.handle(i))
                else:
                    ifs += str(self.handle(i)) + ", "
            if ifs != "":
                return f"for {target} in {_iter} if {ifs}"
            else: 
                return f"for {target} in {_iter}"
        elif _type == "BoolOp":
            op = self.handle(ast["op"])
            values, _v = "", ast["values"]
            for index, v in enumerate(_v):
                if index == len(_v) - 1:
                    values += str(self.handle(v))
                else:
                    values += str(self.handle(v)) + f" {op} "

            return values
        elif _type == "Or":
            return "or"
        elif _type == "Compare":
            left = self.handle(ast["left"])
            ops, _o = "", ast["ops"]
            for index, v in enumerate(_o):
                if index == len(_o) - 1:
                    ops += str(self.handle(v))
                else:
                    ops += str(self.handle(v)) + " "

            comparators, _c = "", ast["comparators"]
            for index, c in enumerate(_c):
                if index == len(_c) - 1:
                    comparators += str(self.handle(c))
                else:
                    comparators += str(self.handle(c)) + " "

            return f"{left} {ops} {comparators}"
        elif _type == "Eq":
            return "=="
        elif _type == "Set":
            elts, _i = "", ast["elts"]
            for index, i in enumerate(_i):
                if index == len(_i) - 1:
                    elts += str(self.handle(i))
                else:
                    elts += str(self.handle(i)) + ", "
            return f"({elts})"
        elif _type == "Dict":
            dict_code = ""
            keys, values = ast["keys"], ast["values"]
            for index in range(len(keys)):
                k, v = keys[index], values[index]
                if index == len(keys) - 1:
                    dict_code += f"{self.handle(k)}:{self.handle(v)}"
                else:
                    dict_code += f"{self.handle(k)}:{self.handle(v)}, "

            return "{" + dict_code + "}"
        elif _type == "UnaryOp":
            Op = ast["op"]
            Operand = self.handle(ast["operand"])
            op_type = Op["_type"]
            
            if op_type == "USub":
                return f"-{Operand}"
            elif op_type == "UAdd":
                return f"+{Operand}"
            elif op_type == "Not":
                return f"not {Operand}"
            elif op_type == "Invert":
                return f"~{Operand}"
            
            return f":{Operand}"
        elif _type == "AugAssign":
            target = self.handle(ast["target"])
            op = self.handle(ast["op"])
            value = self.handle(ast["value"])
            return target + op + "=" + str(value)
        elif _type == "Subscript":
            value = self.handle(ast["value"])
            slice_ast = ast["slice"]
            
            if slice_ast["_type"] == "Tuple":
                elts = [str(self.handle(e)) for e in slice_ast["elts"]]
                _slice = ", ".join(elts)
            else:
                _slice = self.handle(slice_ast)
            return f"{value}[{_slice}]"
        elif _type == "If":
            test = self.handle(ast["test"])
            body, _b = "", ast["body"]
            orelse, _o = "", ast["orelse"]
            for index, i in enumerate(_b):
                if index == len(_b) - 1:
                    body += str(self.handle(i))
                else:
                    body += str(self.handle(i)) + "\n"
            for index, i in enumerate(_o):
                if index == len(_o) - 1:
                    orelse += str(self.handle(i))
                else:
                    orelse += str(self.handle(i)) + "\n"
                    
            if len(_o) == 1 and _o[0]["_type"] == "If":
                return (
                    f"if {test}:\n{self._format(body)}\nel{orelse}"
                )  
            elif len(_o) > 0:
                return (
                    f"if {test}:\n{self._format(body)}\nelse:\n{self._format(orelse)}"
                )
            else:
                return f"if {test}:\n{self._format(body)}"
        elif _type == "Gt":
            return ">"
        elif _type == "For":
            target = self.handle(ast["target"])
            _iter = self.handle(ast["iter"])
            body, _b = "", ast["body"]
            orelse, _o = "", ast["orelse"]
            for index, i in enumerate(_b):
                if index == len(_b) - 1:
                    body += str(self.handle(i))
                else:
                    body += str(self.handle(i)) + "\n"
            for index, i in enumerate(_o):
                if index == len(_o) - 1:
                    orelse += str(self.handle(i))
                else:
                    orelse += str(self.handle(i)) + "\n"

            if orelse != "":
                return f"for {target} in {_iter}:\n{self._format(body)}\nelse:\n{self._format(orelse)}"
            else:
                return f"for {target} in {_iter}:\n{self._format(body)}"

        elif _type == "Break":
            return "break"
        elif _type == "Continue":
            return "continue"
        elif _type == "While":
            test = self.handle(ast["test"])
            body, _b = "", ast["body"]
            for index, i in enumerate(_b):
                if index == len(_b) - 1:
                    body += str(self.handle(i))
                else:
                    body += str(self.handle(i)) + "\n"
            return f"while {test}:\n{self._format(body)}"
        elif _type == "FunctionDef":
            name = ast["name"]
            args = self.handle(ast["args"])
            body, _b = "", ast["body"]
            for index, i in enumerate(_b):
                if index == len(_b) - 1:
                    body += str(self.handle(i))
                else:
                    body += str(self.handle(i)) + "\n"
            return f"def {name}({args}):\n{self._format(body)}"
        elif _type == "arguments":
            posonlyargs, _pa = "", ast["posonlyargs"]
            args, _a = "", ast["args"]
            vararg = ast["vararg"]
            kwonlyargs, _ka = "", ast["kwonlyargs"]
            kw_defaults = ast["kw_defaults"]
            defaults = ast["defaults"]
            kwarg = ast["kwarg"]
            
            output = ""
            
            for index, i in enumerate(_a):
                _args = str(self.handle(i))
                if len(defaults) != 0:
                    if index >= len(_a)-len(defaults):
                        val = self.handle(defaults[(len(_a)-index)-len(defaults)])
                        _args+= f"={val}"
                args += _args+", "
                

            if _pa:
                for index, i in enumerate(_pa):
                    if index == len(_pa) - 1:
                        posonlyargs += str(self.handle(i))
                    else:
                        posonlyargs += str(self.handle(i)) + ", "
                output += posonlyargs + args
            else:
                output += args
          
            if vararg:
                output += f"*{self.handle(vararg)}, "
                
            if _ka:
                for index, i in enumerate(_ka):
                    _args = str(self.handle(i))
                    if len(kw_defaults) != 0:
                        if index >= len(_ka)-len(kw_defaults):
                            val = self.handle(kw_defaults[(len(_ka)-index)-len(kw_defaults)])
                            if val:
                                _args+= f"={val}"
                    kwonlyargs += _args+", "
                output += kwonlyargs
                    
            if kwarg:
                output+= "**"+self.handle(kwarg)+", "  

            output = output[:-2]
            return output
            
        elif _type == "arg":
            output = ast["arg"]
            annotation = ast["annotation"]
            if annotation:
                output+=": "+self.handle(annotation)
            return output
            # TODO: handle type_comment
        elif _type == "Return":
            value = ast["value"]
            if value:
                value = self.handle(value)
                return f"return {value}"
            return "return"
        elif _type == "Lambda":
            args = self.handle(ast["args"])
            body = self.handle(ast["body"])
            return "lambda " + args + ": " + body
        elif _type == "Mult":
            return "*"
        elif _type == "Try":
            body, _b = "", ast["body"]
            handlers, _h = "", ast["handlers"]
            orelse, _oe = "", ast["orelse"]
            finalbody, _fb = "", ast["finalbody"]

            for index, i in enumerate(_b):
                if index == len(_b) - 1:
                    body += str(self.handle(i))
                else:
                    body += str(self.handle(i)) + "\n"

            for index, i in enumerate(_h):
                if index == len(_h) - 1:
                    handlers += str(self.handle(i))
                else:
                    handlers += str(self.handle(i)) + "\n"

            for index, i in enumerate(_oe):
                if index == len(_oe) - 1:
                    orelse += str(self.handle(i))
                else:
                    orelse += str(self.handle(i)) + "\n"

            for index, i in enumerate(_fb):
                if index == len(_fb) - 1:
                    finalbody += str(self.handle(i))
                else:
                    finalbody += str(self.handle(i)) + "\n"

            output = f"try:\n{self._format(body)}\n{handlers}"
            if orelse != "":
                output += "else:\n" + self._format(orelse)
            if finalbody != "":
                output += "finally:\n" + self._format(finalbody)
            return output

        elif _type == "Div":
            return "/"
        elif _type == "ExceptHandler":
            _t = self.handle(ast["type"])
            name = ast["name"]
            body, _b = "", ast["body"]
            for index, i in enumerate(_b):
                if index == len(_b) - 1:
                    body += str(self.handle(i))
                else:
                    body += str(self.handle(i)) + "\n"

            if name != None:
                return f"except {_t} as {name}:\n{self._format(body)}"
            else:
                return f"except {_t}:\n{self._format(body)}"
        elif _type == "Pass":
            return "pass"
        elif _type == "ClassDef":
            name = ast["name"]
            bases_list = ast["bases"]
            keywords_list = ast["keywords"]
            body_list = ast["body"]
            decorator_list = ast["decorator_list"]

            decorators = ""
            for decorator in decorator_list:
                decorators += "@" + str(self.handle(decorator)) + "\n"

            bases = ""
            if bases_list:
                base_strings = []
                for base in bases_list:
                    base_strings.append(str(self.handle(base)))
                bases = "(" + ", ".join(base_strings) + ")"

            keywords = ""
            if keywords_list:
                keyword_strings = []
                for keyword in keywords_list:
                    keyword_strings.append(str(self.handle(keyword)))
                keywords = ", " + ", ".join(keyword_strings)

            body_lines = []
            for item in body_list:
                handled_item = str(self.handle(item))
                body_lines.append(handled_item)

            body_code = "\n".join(body_lines)
            formatted_body = self._format(body_code, indent_depth=1)

            if bases or keywords:
                class_def = f"class {name}{bases}{keywords}:"
            else:
                class_def = f"class {name}:"

            return decorators + class_def + "\n" + formatted_body
        elif _type == "Mod":
            return "%"
        elif _type == "Sub":
            return "-"
        elif _type == "DictComp":
            key = self.handle(ast["key"])
            value = self.handle(ast["value"])
            generators, _g = "", ast["generators"]
            for index, g in enumerate(_g):
                if index == len(_g) - 1:
                    generators += str(self.handle(g))
                else:
                    generators += str(self.handle(g)) + ", "
                    
            return "{"+f"{key}:{value} {generators}"+"}"
        elif _type == "SetComp":
            elt = self.handle(ast["elt"])
            generators, _g = "", ast["generators"]
            for index, g in enumerate(_g):
                if index == len(_g) - 1:
                    generators += str(self.handle(g))
                else:
                    generators += str(self.handle(g)) + ", "
                    
            return "{"+f"{elt} {generators}"+"}"
        elif _type == "Yield":
            value = self.handle(ast["value"])
            return f"yield {value}"
        elif _type == "With":
            items, _i = "", ast["items"]
            body, _b = "", ast["body"]
            type_comment = ast["type_comment"]
            
            for index, i in enumerate(_i):
                if index == len(_i) - 1:
                    items += str(self.handle(i))
                else:
                    items += str(self.handle(i)) + ", "
            for index, i in enumerate(_b):
                if index == len(_b) - 1:
                    body += str(self.handle(i))
                else:
                    body += str(self.handle(i)) + "\n"
                    
            if type_comment != None:
                type_comment = self.handle(type_comment)
                return f"{items}    # type: {type_comment}\n{self._format(body)}"
            return f"{items}\n{self._format(body)}"
        elif _type == "withitem":
            context_expr = self.handle(ast["context_expr"])
            optional_vars = self.handle(ast["optional_vars"])
            if optional_vars != "":
                return f"with {context_expr} as {optional_vars}:"
            else: 
                return f"with {context_expr}:"
        elif _type == "Assert":
            test = self.handle(ast["test"])
            msg = ast["msg"]
            
            if msg != None:
                msg = self.handle(msg)
                return f"assert {test}, {msg}"
            return f"assert {test}"
        elif _type == "JoinedStr":
            parts = []
            for v in ast["values"]:
                data = self.handle(v)
                if isinstance(data, str) and len(data) >= 2 and data[0] == data[-1] and data[0] in ("'", '"'):
                    data = data[1:-1]
                parts.append(str(data))

            joined = "".join(parts)
            safe = joined.replace("'", "\\'")
            return f"f'{safe}'"

        elif _type == "FormattedValue":
            return "{"+self.handle(ast["value"])+"}"
        elif _type == "Match":
            subject = self.handle(ast["subject"])
            cases, _c = "", ast["cases"]
            for index, i in enumerate(_c):
                data = str(self.handle(i))
                if index == len(_c) - 1:
                    cases += data
                else:
                    cases += data + "\n"

            return f"match {subject}:\n{self._format(cases)}"
        elif _type == "match_case":
            pattern = self.handle(ast["pattern"])
            guard = self.handle(ast["guard"]) if ast.get("guard") is not None else None
            body, _b = "", ast["body"]
            
            for index, i in enumerate(_b):
                data = str(self.handle(i))
                if index == len(_b) - 1:
                    body += data
                else:
                    body += data + "\n"
                
            return f"case {pattern} if {guard}:\n{self._format(body)}"
        elif _type == "MatchClass":
            _cls = self.handle(ast["cls"])
            return f"{_cls}()"
        elif _type == "MatchSequence":
            patterns, _p = "", ast["patterns"]
            for index, i in enumerate(_p):
                data = str(self.handle(i))
                if index == len(_p) - 1:
                    patterns += data
                else:
                    patterns += data + ", "
            return f"[{patterns}]"
        elif _type == "MatchAs":
            pattern = ast["pattern"]
            name = ast["name"]
            if pattern != None:
                pattern = self.handle(pattern)
                return f"{pattern} as {name}"
            return name
        elif _type == "IfExp":
            test = self.handle(ast["test"])
            body = self.handle(ast["body"])
            orelse = self.handle(ast["orelse"])
            
            return f"{body} if {test} else {orelse}"
        elif _type == "Starred":
            value = self.handle(ast["value"])
            return f"*{value}"
        elif _type == "AsyncFunctionDef":
            name = ast["name"]
            args = self.handle(ast["args"])
            body, _b = "", ast["body"]
            
            for index, i in enumerate(_b):
                data = str(self.handle(i))
                if index == len(_b) - 1:
                    body += data
                else:
                    body += data + "\n"
            return f"async def {name}({args}):\n{self._format(body)}"
        elif _type == "Await":
            value = self.handle(ast["value"])
            return f"await {value}"
        elif _type == "Slice":
            lower = self.handle(ast["lower"]) if ast["lower"] else ""
            upper = self.handle(ast["upper"]) if ast["upper"] else ""
            step = self.handle(ast["step"]) if ast["step"] else ""
            return f"{lower}:{upper}:{step}" if step != "" else f"{lower}:{upper}"
        elif _type == "MatchSingleton":
            return f"{ast['value']}:\n"
        elif _type == "And":
            return "and"
        elif _type == "BitXor":
            return "^"
        elif _type == "LShift":
            return "<<"
        elif _type == "Lt":
            return "<"
        elif _type == "NotEq":
            return "!="
        elif _type == "Global":
            names = ",".join(ast["names"])
            return f"global {names}"
        elif _type == "GtE":
            return ">="
        elif _type == "BitAnd":
            return "&"
        elif _type == "RShift":
            return ">>"
        elif _type == "BitOr":
            return "|"
        elif _type == "GeneratorExp":
            elt = self.handle(ast["elt"])
            generators = self.run(ast["generators"])
            
            return f"({elt} {generators})"
        elif _type == "IsNot":
            return "is not"
        elif _type == "FloorDiv":
            return "//"
        elif _type == "NotIn":
            return "not in"
        elif _type == "In":
            return "in"
        elif _type == "Is":
            return "is"
        elif _type == "LtE":
            return "<="
        elif _type == "Raise":
            exc = self.handle(ast["exc"]) if ast["exc"] else None
            cause = self.handle(ast["cause"]) if ast["cause"] else None

            if exc and cause:
                return f"raise {exc} from {cause}"
            elif exc:
                return f"raise {exc}"
            else:
                return "raise"
        elif _type == "YieldFrom":
            value = self.handle(ast["value"])
            return f"yield from {value}"
        else:
            print("AST2CODE ERROR | unknown:", _type)

        return code

    def run(self, ast):
        Code = ""
        for a in ast:
            Code += self.handle(a) + "\n"
        return Code
    
    
    
Module = AST2Code_Module()
def AST2Code(AST):
    return Module.run(AST)