import random
from Obfuscate.Utils import Parser, AST2Code, Utils

A2C_Module = AST2Code.AST2Code_Module()
Utils = Utils.Utils()


def GenerateKeys(Str, Key):
    Passwords, Hash = [], 0

    K = Key
    for i in range(10):
        hash_value = 5381

        hash_value ^= K + i

        for char in Str:
            hash_value = ((hash_value << 5) + hash_value) ^ ord(char)
            hash_value &= 0xFFFFFFFFFFFFFFFF

        if i == 0:
            Hash = hash_value
        else:
            Passwords.append(hash_value)
    return Passwords, Hash


def HideGlobals(AST):
    GlobalsDictName = Utils.RandomString(20)
    Key = random.randint(-9000000000, 9000000000)
    BuiltInList = [str(I) for I in __builtins__.keys()]
    ExcludeList = [
        "__name__",
        "__file__",
        "__doc__",
        "__package__",
        "__loader__",
        "__spec__",
    ]
    Names = Utils.FindAllInstances(AST, "_type", "Name")
    for Name_Path in Names:
        Block = AST
        for Index in Name_Path[:-2]:
            Block = Block[Index]
        Name = Block[Name_Path[-2]]["id"]
        if Name in BuiltInList and Name not in ExcludeList:
            Passwords, Hash = GenerateKeys(Name, Key)
            Block[Name_Path[-2]] = {
                "value": {
                    "func": {
                        "value": {
                            "id": GlobalsDictName,
                            "ctx": {"_type": "Load"},
                            "_type": "Name",
                        },
                        "slice": {"value": Hash, "kind": None, "_type": "Constant"},
                        "ctx": {"_type": "Load"},
                        "_type": "Subscript",
                    },
                    "args": [
                        {
                            "value": random.choice(Passwords),
                            "kind": None,
                            "_type": "Constant",
                        }
                    ],
                    "keywords": [],
                    "_type": "Call",
                },
                "_type": "Expr",
            }

    # Returning the modified AST with the function closure bug patched
    return [
        {
            "targets": [
                {"id": GlobalsDictName, "ctx": {"_type": "Store"}, "_type": "Name"}
            ],
            "value": {"keys": [], "values": [], "_type": "Dict"},
            "type_comment": None,
            "_type": "Assign",
        },
        {
            "targets": [{"id": "F", "ctx": {"_type": "Store"}, "_type": "Name"}],
            "value": {
                "test": {
                    "func": {
                        "id": "isinstance",
                        "ctx": {"_type": "Load"},
                        "_type": "Name",
                    },
                    "args": [
                        {"id": "__builtins__", "ctx": {"_type": "Load"}, "_type": "Name"},
                        {"id": "dict", "ctx": {"_type": "Load"}, "_type": "Name"},
                    ],
                    "keywords": [],
                    "_type": "Call",
                },
                "body": {"id": "__builtins__", "ctx": {"_type": "Load"}, "_type": "Name"},
                "orelse": {
                    "func": {
                        "id": "getattr",
                        "ctx": {"_type": "Load"},
                        "_type": "Name",
                    },
                    "args": [
                        {"id": "__builtins__", "ctx": {"_type": "Load"}, "_type": "Name"},
                        {"value": "__dict__", "kind": None, "_type": "Constant"},
                    ],
                    "keywords": [],
                    "_type": "Call",
                },
                "_type": "IfExp",
            },
            "type_comment": None,
            "_type": "Assign",
        },
        {
            "target": {
                "elts": [
                    {"id": "G", "ctx": {"_type": "Store"}, "_type": "Name"},
                    {"id": "H", "ctx": {"_type": "Store"}, "_type": "Name"},
                ],
                "ctx": {"_type": "Store"},
                "_type": "Tuple",
            },
            "iter": {
                "func": {
                    "value": {"id": "F", "ctx": {"_type": "Load"}, "_type": "Name"},
                    "attr": "items",
                    "ctx": {"_type": "Load"},
                    "_type": "Attribute",
                },
                "args": [],
                "keywords": [],
                "_type": "Call",
            },
            "body": [
                {
                    "targets": [{"id": "I", "ctx": {"_type": "Store"}, "_type": "Name"}],
                    "value": {"value": Key, "kind": None, "_type": "Constant"},
                    "type_comment": None,
                    "_type": "Assign",
                },
                {
                    "targets": [{"id": "C", "ctx": {"_type": "Store"}, "_type": "Name"}],
                    "value": {"elts": [], "ctx": {"_type": "Load"}, "_type": "List"},
                    "type_comment": None,
                    "_type": "Assign",
                },
                {
                    "targets": [{"id": "B", "ctx": {"_type": "Store"}, "_type": "Name"}],
                    "value": {"value": 0, "kind": None, "_type": "Constant"},
                    "type_comment": None,
                    "_type": "Assign",
                },
                {
                    "target": {"id": "D", "ctx": {"_type": "Store"}, "_type": "Name"},
                    "iter": {
                        "func": {
                            "id": "range",
                            "ctx": {"_type": "Load"},
                            "_type": "Name",
                        },
                        "args": [{"value": 10, "kind": None, "_type": "Constant"}],
                        "keywords": [],
                        "_type": "Call",
                    },
                    "body": [
                        {
                            "targets": [
                                {"id": "A", "ctx": {"_type": "Store"}, "_type": "Name"}
                            ],
                            "value": {"value": 5381, "kind": None, "_type": "Constant"},
                            "type_comment": None,
                            "_type": "Assign",
                        },
                        {
                            "target": {
                                "id": "A",
                                "ctx": {"_type": "Store"},
                                "_type": "Name",
                            },
                            "op": {"_type": "BitXor"},
                            "value": {
                                "left": {
                                    "id": "I",
                                    "ctx": {"_type": "Load"},
                                    "_type": "Name",
                                },
                                "op": {"_type": "Add"},
                                "right": {
                                    "id": "D",
                                    "ctx": {"_type": "Load"},
                                    "_type": "Name",
                                },
                                "_type": "BinOp",
                            },
                            "_type": "AugAssign",
                        },
                        {
                            "target": {
                                "id": "J",
                                "ctx": {"_type": "Store"},
                                "_type": "Name",
                            },
                            "iter": {"id": "G", "ctx": {"_type": "Load"}, "_type": "Name"},
                            "body": [
                                {
                                    "targets": [
                                        {
                                            "id": "A",
                                            "ctx": {"_type": "Store"},
                                            "_type": "Name",
                                        }
                                    ],
                                    "value": {
                                        "left": {
                                            "left": {
                                                "left": {
                                                    "id": "A",
                                                    "ctx": {"_type": "Load"},
                                                    "_type": "Name",
                                                },
                                                "op": {"_type": "LShift"},
                                                "right": {
                                                    "value": 5,
                                                    "kind": None,
                                                    "_type": "Constant",
                                                },
                                                "_type": "BinOp",
                                            },
                                            "op": {"_type": "Add"},
                                            "right": {
                                                "id": "A",
                                                "ctx": {"_type": "Load"},
                                                "_type": "Name",
                                            },
                                            "_type": "BinOp",
                                        },
                                        "op": {"_type": "BitXor"},
                                        "right": {
                                            "func": {
                                                "id": "ord",
                                                "ctx": {"_type": "Load"},
                                                "_type": "Name",
                                            },
                                            "args": [
                                                {
                                                    "id": "J",
                                                    "ctx": {"_type": "Load"},
                                                    "_type": "Name",
                                                }
                                            ],
                                            "keywords": [],
                                            "_type": "Call",
                                        },
                                        "_type": "BinOp",
                                    },
                                    "type_comment": None,
                                    "_type": "Assign",
                                },
                                {
                                    "target": {
                                        "id": "A",
                                        "ctx": {"_type": "Store"},
                                        "_type": "Name",
                                    },
                                    "op": {"_type": "BitAnd"},
                                    "value": {
                                        "value": 18446744073709551615,
                                        "kind": None,
                                        "_type": "Constant",
                                    },
                                    "_type": "AugAssign",
                                },
                            ],
                            "orelse": [],
                            "type_comment": None,
                            "_type": "For",
                        },
                        {
                            "test": {
                                "left": {
                                    "id": "D",
                                    "ctx": {"_type": "Load"},
                                    "_type": "Name",
                                },
                                "ops": [{"_type": "Eq"}],
                                "comparators": [
                                    {"id": "B", "ctx": {"_type": "Load"}, "_type": "Name"}
                                ],
                                "_type": "Compare",
                            },
                            "body": [
                                {
                                    "targets": [
                                        {
                                            "id": "B",
                                            "ctx": {"_type": "Store"},
                                            "_type": "Name",
                                        }
                                    ],
                                    "value": {
                                        "id": "A",
                                        "ctx": {"_type": "Load"},
                                        "_type": "Name",
                                    },
                                    "type_comment": None,
                                    "_type": "Assign",
                                }
                            ],
                            "orelse": [
                                {
                                    "value": {
                                        "func": {
                                            "value": {
                                                "id": "C",
                                                "ctx": {"_type": "Load"},
                                                "_type": "Name",
                                            },
                                            "attr": "append",
                                            "ctx": {"_type": "Load"},
                                            "_type": "Attribute",
                                        },
                                        "args": [
                                            {
                                                "id": "A",
                                                "ctx": {"_type": "Load"},
                                                "_type": "Name",
                                            }
                                        ],
                                        "keywords": [],
                                        "_type": "Call",
                                    },
                                    "_type": "Expr",
                                }
                            ],
                            "_type": "If",
                        },
                    ],
                    "orelse": [],
                    "type_comment": None,
                    "_type": "For",
                },
                {
                    "name": "K",
                    "args": {
                        "posonlyargs": [],
                        "args": [
                            {
                                "arg": "x",
                                "annotation": None,
                                "type_comment": None,
                                "_type": "arg",
                            },
                            {
                                "arg": "C",
                                "annotation": None,
                                "type_comment": None,
                                "_type": "arg",
                            },
                            {
                                "arg": "H",
                                "annotation": None,
                                "type_comment": None,
                                "_type": "arg",
                            },
                        ],
                        "vararg": None,
                        "kwonlyargs": [],
                        "kw_defaults": [],
                        "kwarg": None,
                        "defaults": [
                            {"id": "C", "ctx": {"_type": "Load"}, "_type": "Name"},
                            {"id": "H", "ctx": {"_type": "Load"}, "_type": "Name"},
                        ],
                        "_type": "arguments",
                    },
                    "body": [
                        {
                            "test": {
                                "left": {
                                    "id": "x",
                                    "ctx": {"_type": "Load"},
                                    "_type": "Name",
                                },
                                "ops": [{"_type": "In"}],
                                "comparators": [
                                    {"id": "C", "ctx": {"_type": "Load"}, "_type": "Name"}
                                ],
                                "_type": "Compare",
                            },
                            "body": [
                                {
                                    "value": {
                                        "id": "H",
                                        "ctx": {"_type": "Load"},
                                        "_type": "Name",
                                    },
                                    "_type": "Return",
                                }
                            ],
                            "orelse": [],
                            "_type": "If",
                        }
                    ],
                    "decorator_list": [],
                    "returns": None,
                    "type_comment": None,
                    "type_params": [],
                    "_type": "FunctionDef",
                },
                {
                    "targets": [
                        {
                            "value": {
                                "id": GlobalsDictName,
                                "ctx": {"_type": "Load"},
                                "_type": "Name",
                            },
                            "slice": {
                                "id": "B",
                                "ctx": {"_type": "Load"},
                                "_type": "Name",
                            },
                            "ctx": {"_type": "Store"},
                            "_type": "Subscript",
                        }
                    ],
                    "value": {"id": "K", "ctx": {"_type": "Load"}, "_type": "Name"},
                    "type_comment": None,
                    "_type": "Assign",
                },
            ],
            "orelse": [],
            "type_comment": None,
            "_type": "For",
        }
    ] + AST