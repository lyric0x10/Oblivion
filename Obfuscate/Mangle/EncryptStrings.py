import random
from Obfuscate.Utils import Parser, AST2Code, Utils

A2C_Module = AST2Code.AST2Code_Module()
Utils = Utils.Utils()

# Character sets for generating random keys and encoding
Characters = {
    "Symbols": "!#$%&()*+,-.:;<=>?@[]^_{}~",
    "Letters": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "Digits": "0123456789",
}
PossibleChars = "".join(Characters.values())

def xor_cipher(text, key):
    """Encrypts/Decrypts text using a XOR cipher with a keyword."""
    result = []
    key_length = len(key)
    for i in range(len(text)):
        char_code = ord(text[i]) ^ ord(key[i % key_length])
        result.append(chr(char_code))
    return "".join(result)

def CustomBaseEncode(text, charset):
    """Converts string bytes to a custom base string."""
    base = len(charset)
    data_bytes = text.encode('utf-8')
    number = int.from_bytes(data_bytes, 'big')
    
    if number == 0:
        return charset[0]
    
    res = []
    while number > 0:
        number, rem = divmod(number, base)
        res.append(charset[rem])
    
    return ''.join(reversed(res))

def CustomBaseDecode(encoded_text, charset):
    """Converts custom base string back to bytes."""
    base = len(charset)
    number = 0
    
    for char in encoded_text:
        # This is where the error occurred: char not in charset
        number = number * base + charset.index(char)
    
    byte_length = (number.bit_length() + 7) // 8
    return number.to_bytes(byte_length, 'big').decode('utf-8')

# --- Updated Workflow ---

def Encode(String):
    # 1. Generate random KEY for XOR
    xor_key = "".join(random.sample(PossibleChars, random.randint(6,12)))
    
    # 2. Generate random CHARSET for Base Encoding
    base_charset = "".join(random.sample(PossibleChars, random.randint(12, 24))) # 60 chars for base-60
    
    # 3. Create a unique splitter not in XOR key or Base charset
    unavailable = set(xor_key) | set(base_charset)
    available_splitters = list(set(PossibleChars) - unavailable)
    SplitChar = random.choice(available_splitters)
    
    # 4. XOR -> Base Encode
    xor_result = xor_cipher(String, xor_key)
    EncodedData = CustomBaseEncode(xor_result, base_charset)
    
    # 5. Assemble: Data + Splitter + Key + Splitter + Charset
    combined = EncodedData + SplitChar + xor_key + SplitChar + base_charset
    
    # 6. Insert splitter again at a random position to confuse direct decoding
    # Note: Index needs to be adjusted based on the initial structure
    InsertIndex = random.randint(0, len(combined) - 1)
    final_str = combined[:InsertIndex] + SplitChar + combined[InsertIndex:]

    return (final_str, InsertIndex + 1, SplitChar)
    
def Decode(Str, Index):
    # 1. Identify the SplitChar using the provided Index
    # Since Index is 1-based, Str[Index-1] is the extra splitter we inserted.
    SplitChar = Str[Index - 1]

    # 2. Remove the extra splitter at the specific index
    cleaned_str = Str[:Index-1] + Str[Index:]
    
    # 3. Split into Data, Key, and Charset using the identified SplitChar
    parts = cleaned_str.split(SplitChar)
    EncodedData = parts[0]
    xor_key = parts[1]
    base_charset = parts[2]
    
    # 4. Base Decode -> XOR
    decoded_xor = CustomBaseDecode(EncodedData, base_charset)
    original_text = xor_cipher(decoded_xor, xor_key)
    
    return original_text
    
## --- Testing ---
#message = "hello world"
#EStr, I, SChar = Encode(message)
#print(f"Encoded: {EStr}")
#print(f"Split Index: {I}")
#print(f"Split Char: {SChar}")
#print(f"Decoded: {Decode(EStr, I)}")

def EncryptStrings(AST):
    DecryptFunction = Utils.RandomString(20)
    DecryptFunctionAST = {'name': DecryptFunction, 'args': {'posonlyargs': [], 'args': [{'arg': 'Data', 'annotation': None, 'type_comment': None, '_type': 'arg'}, {'arg': 'Index', 'annotation': None, 'type_comment': None, '_type': 'arg'}], 'vararg': None, 'kwonlyargs': [], 'kw_defaults': [], 'kwarg': None, 'defaults': [], '_type': 'arguments'}, 'body': [{'targets': [{'id': 'S_Char', 'ctx': {'_type': 'Store'}, '_type': 'Name'}], 'value': {'value': {'id': 'Data', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'left': {'id': 'Index', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'op': {'_type': 'Sub'}, 'right': {'value': 1, 'kind': None, '_type': 'Constant'}, '_type': 'BinOp'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}, 'type_comment': None, '_type': 'Assign'}, {'targets': [{'id': 'Clean', 'ctx': {'_type': 'Store'}, '_type': 'Name'}], 'value': {'left': {'value': {'id': 'Data', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'lower': None, 'upper': {'left': {'id': 'Index', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'op': {'_type': 'Sub'}, 'right': {'value': 1, 'kind': None, '_type': 'Constant'}, '_type': 'BinOp'}, 'step': None, '_type': 'Slice'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}, 'op': {'_type': 'Add'}, 'right': {'value': {'id': 'Data', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'lower': {'id': 'Index', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'upper': None, 'step': None, '_type': 'Slice'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}, '_type': 'BinOp'}, 'type_comment': None, '_type': 'Assign'}, {'targets': [{'id': 'Parts', 'ctx': {'_type': 'Store'}, '_type': 'Name'}], 'value': {'func': {'value': {'id': 'Clean', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'attr': 'split', 'ctx': {'_type': 'Load'}, '_type': 'Attribute'}, 'args': [{'id': 'S_Char', 'ctx': {'_type': 'Load'}, '_type': 'Name'}], 'keywords': [], '_type': 'Call'}, 'type_comment': None, '_type': 'Assign'}, {'targets': [{'id': 'Num', 'ctx': {'_type': 'Store'}, '_type': 'Name'}], 'value': {'value': 0, 'kind': None, '_type': 'Constant'}, 'type_comment': None, '_type': 'Assign'}, {'targets': [{'id': 'Base', 'ctx': {'_type': 'Store'}, '_type': 'Name'}], 'value': {'func': {'id': 'len', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'value': {'id': 'Parts', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'value': 2, 'kind': None, '_type': 'Constant'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}], 'keywords': [], '_type': 'Call'}, 'type_comment': None, '_type': 'Assign'}, {'target': {'id': 'Char', 'ctx': {'_type': 'Store'}, '_type': 'Name'}, 'iter': {'value': {'id': 'Parts', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'value': 0, 'kind': None, '_type': 'Constant'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}, 'body': [{'targets': [{'id': 'Num', 'ctx': {'_type': 'Store'}, '_type': 'Name'}], 'value': {'left': {'left': {'id': 'Num', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'op': {'_type': 'Mult'}, 'right': {'id': 'Base', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, '_type': 'BinOp'}, 'op': {'_type': 'Add'}, 'right': {'func': {'value': {'value': {'id': 'Parts', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'value': 2, 'kind': None, '_type': 'Constant'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}, 'attr': 'index', 'ctx': {'_type': 'Load'}, '_type': 'Attribute'}, 'args': [{'id': 'Char', 'ctx': {'_type': 'Load'}, '_type': 'Name'}], 'keywords': [], '_type': 'Call'}, '_type': 'BinOp'}, 'type_comment': None, '_type': 'Assign'}], 'orelse': [], 'type_comment': None, '_type': 'For'}, {'targets': [{'id': 'Dec', 'ctx': {'_type': 'Store'}, '_type': 'Name'}], 'value': {'func': {'value': {'func': {'value': {'id': 'Num', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'attr': 'to_bytes', 'ctx': {'_type': 'Load'}, '_type': 'Attribute'}, 'args': [{'left': {'left': {'func': {'value': {'id': 'Num', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'attr': 'bit_length', 'ctx': {'_type': 'Load'}, '_type': 'Attribute'}, 'args': [], 'keywords': [], '_type': 'Call'}, 'op': {'_type': 'Add'}, 'right': {'value': 7, 'kind': None, '_type': 'Constant'}, '_type': 'BinOp'}, 'op': {'_type': 'FloorDiv'}, 'right': {'value': 8, 'kind': None, '_type': 'Constant'}, '_type': 'BinOp'}, {'value': 'big', 'kind': None, '_type': 'Constant'}], 'keywords': [], '_type': 'Call'}, 'attr': 'decode', 'ctx': {'_type': 'Load'}, '_type': 'Attribute'}, 'args': [{'value': 'utf-8', 'kind': None, '_type': 'Constant'}], 'keywords': [], '_type': 'Call'}, 'type_comment': None, '_type': 'Assign'}, {'value': {'func': {'value': {'value': '', 'kind': None, '_type': 'Constant'}, 'attr': 'join', 'ctx': {'_type': 'Load'}, '_type': 'Attribute'}, 'args': [{'elt': {'func': {'id': 'chr', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'left': {'func': {'id': 'ord', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'value': {'id': 'Dec', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'id': 'i', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}], 'keywords': [], '_type': 'Call'}, 'op': {'_type': 'BitXor'}, 'right': {'func': {'id': 'ord', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'value': {'value': {'id': 'Parts', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'value': 1, 'kind': None, '_type': 'Constant'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}, 'slice': {'left': {'id': 'i', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'op': {'_type': 'Mod'}, 'right': {'func': {'id': 'len', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'value': {'id': 'Parts', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'slice': {'value': 1, 'kind': None, '_type': 'Constant'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}], 'keywords': [], '_type': 'Call'}, '_type': 'BinOp'}, 'ctx': {'_type': 'Load'}, '_type': 'Subscript'}], 'keywords': [], '_type': 'Call'}, '_type': 'BinOp'}], 'keywords': [], '_type': 'Call'}, 'generators': [{'target': {'id': 'i', 'ctx': {'_type': 'Store'}, '_type': 'Name'}, 'iter': {'func': {'id': 'range', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'func': {'id': 'len', 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'id': 'Dec', 'ctx': {'_type': 'Load'}, '_type': 'Name'}], 'keywords': [], '_type': 'Call'}], 'keywords': [], '_type': 'Call'}, 'ifs': [], 'is_async': 0, '_type': 'comprehension'}], '_type': 'GeneratorExp'}], 'keywords': [], '_type': 'Call'}, '_type': 'Return'}], 'decorator_list': [], 'returns': None, 'type_comment': None, 'type_params': [], '_type': 'FunctionDef'}
    Constants_Paths = Utils.FindAllInstances(AST, "_type", "Constant")
    for Path in Constants_Paths:
        Block = AST
        for Index in Path[:-2]:
            Block = Block[Index]
        Value = Block[Path[-2]]["value"]
        if type(Value) is str:
            Encrypted_Str, Split_Index, Split_Char = Encode(Value)
            Block[Path[-2]] = {'value': {'func': {'id': DecryptFunction, 'ctx': {'_type': 'Load'}, '_type': 'Name'}, 'args': [{'value': Encrypted_Str, 'kind': None, '_type': 'Constant'}, {'value': Split_Index, 'kind': None, '_type': 'Constant'}], 'keywords': [], '_type': 'Call'}, '_type': 'Expr'}
    return [DecryptFunctionAST]+AST