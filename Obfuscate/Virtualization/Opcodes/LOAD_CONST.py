# Format = ['LOAD_CONST', Reg, Const]
Registers[A] = Constants[B]



#Const = Constants[B]
#if isinstance(Const, str):
#    SplitChar = Const[0][Const[1] - 1]
#    cleaned_str = Const[0][:Const[1]-1] + Const[0][Const[1]:]
#    
#    parts = cleaned_str.split(SplitChar)
#    EncodedData = parts[0]
#    xor_key = parts[1]
#    base_charset = parts[2]
#    
#    base = len(base_charset)
#    number = 0
#    
#    for char in EncodedData:
#        number = number * base + base_charset.index(char)
#    
#    byte_length = (number.bit_length() + 7) // 8
#    decoded_xor = number.to_bytes(byte_length, 'big').decode('utf-8')
#    result = []
#    key_length = len(xor_key)
#    for i in range(len(decoded_xor)):
#        char_code = ord(decoded_xor[i]) ^ ord(xor_key[i % key_length])
#        result.append(chr(char_code))
#    Registers[A] = "".join(result)
#else:
#    p = 2147483647
#    cipher = Const[0] ^ Const[1]
#    cipher = (cipher >> 3) | ((cipher << 28) & 0x7FFFFFFF)
#    
#    key_inv = pow(Const[1], p - 2, p)
#    
#    offset = (Const[1] ^ 0x5555) % p
#    Registers[A] = ((cipher - offset) * key_inv) % p