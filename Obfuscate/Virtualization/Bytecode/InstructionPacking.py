import struct

def Pack(Data):
    Buffer = bytearray()
    
    # Booleans must be checked before integers since `bool` is a subclass of `int` in Python
    if isinstance(Data, bool):
        # Tag 0x05: 1-byte Boolean
        Buffer.append(0x05)
        Buffer.append(1 if Data else 0)

    elif isinstance(Data, int):
        # Tag 0x01: 4-byte Length + Arbitrary Size Big-endian Signed Integer
        Buffer.append(0x01)
        ByteLength = (Data.bit_length() + 8) // 8
        if Data == 0: 
            ByteLength = 1
            
        Buffer.extend(ByteLength.to_bytes(4, byteorder='big'))
        Buffer.extend(Data.to_bytes(ByteLength, byteorder='big', signed=True))
        
    elif isinstance(Data, str):
        # Tag 0x02: 4-byte Length + UTF-8 Encoded String
        Buffer.append(0x02)
        Encoded = Data.encode('utf-8')
        Buffer.extend(len(Encoded).to_bytes(4, byteorder='big'))
        Buffer.extend(Encoded)
        
    elif isinstance(Data, list):
        # Tag 0x03: 4-byte Count + Recursive Items
        Buffer.append(0x03)
        Buffer.extend(len(Data).to_bytes(4, byteorder='big'))
        for Item in Data:
            Buffer.extend(Pack(Item))
            
    elif isinstance(Data, tuple):
        # Tag 0x04: 4-byte Count + Recursive Items
        Buffer.append(0x04)
        Buffer.extend(len(Data).to_bytes(4, byteorder='big'))
        for Item in Data:
            Buffer.extend(Pack(Item))

    elif Data is None:
        # Tag 0x06: NoneType (No payload required)
        Buffer.append(0x06)

    elif isinstance(Data, float):
        # Tag 0x07: 8-byte IEEE 754 Double Precision Float
        Buffer.append(0x07)
        Buffer.extend(struct.pack('>d', Data))

    elif isinstance(Data, bytes) or isinstance(Data, bytearray):
        # Tag 0x08: 4-byte Length + Raw Bytes
        Buffer.append(0x08)
        Buffer.extend(len(Data).to_bytes(4, byteorder='big'))
        Buffer.extend(Data)

    elif isinstance(Data, dict):
        # Tag 0x09: 4-byte Count + Recursive Key-Value Pairs
        Buffer.append(0x09)
        Buffer.extend(len(Data).to_bytes(4, byteorder='big'))
        for Key, Value in Data.items():
            Buffer.extend(Pack(Key))
            Buffer.extend(Pack(Value))

    else:
        raise TypeError(f"Unsupported data type for packing: {type(Data)}")
        
    return Buffer

def Unpack(Buffer, Offset=0):
    if Offset >= len(Buffer):
        raise ValueError("Unexpected end of buffer")
        
    Tag = Buffer[Offset]
    Offset += 1
    
    if Tag == 0x01:  # Integer
        if Offset + 4 > len(Buffer): raise ValueError("Buffer underflow reading Int Length")
        Length = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        
        if Offset + Length > len(Buffer): raise ValueError("Buffer underflow reading Int Data")
        Val = int.from_bytes(Buffer[Offset:Offset+Length], byteorder='big', signed=True)
        return Val, Offset + Length
        
    elif Tag == 0x02:  # String
        if Offset + 4 > len(Buffer): raise ValueError("Buffer underflow reading String Length")
        Length = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        
        if Offset + Length > len(Buffer): raise ValueError("Buffer underflow reading String Data")
        Val = Buffer[Offset:Offset+Length].decode('utf-8')
        return Val, Offset + Length
        
    elif Tag == 0x03:  # List
        if Offset + 4 > len(Buffer): raise ValueError("Buffer underflow reading List Count")
        Count = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        Items = []
        for _ in range(Count):
            Val, Offset = Unpack(Buffer, Offset)
            Items.append(Val)
        return Items, Offset
        
    elif Tag == 0x04:  # Tuple
        if Offset + 4 > len(Buffer): raise ValueError("Buffer underflow reading Tuple Count")
        Count = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        Items = []
        for _ in range(Count):
            Val, Offset = Unpack(Buffer, Offset)
            Items.append(Val)
        return tuple(Items), Offset

    elif Tag == 0x05:  # Boolean
        if Offset + 1 > len(Buffer): raise ValueError("Buffer underflow reading Boolean")
        Val = bool(Buffer[Offset])
        return Val, Offset + 1

    elif Tag == 0x06:  # None
        return None, Offset

    elif Tag == 0x07:  # Float
        if Offset + 8 > len(Buffer): raise ValueError("Buffer underflow reading Float")
        Val = struct.unpack('>d', Buffer[Offset:Offset+8])[0]
        return Val, Offset + 8

    elif Tag == 0x08:  # Raw Bytes
        if Offset + 4 > len(Buffer): raise ValueError("Buffer underflow reading Bytes Length")
        Length = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        
        if Offset + Length > len(Buffer): raise ValueError("Buffer underflow reading Bytes Data")
        Val = bytes(Buffer[Offset:Offset+Length])
        return Val, Offset + Length

    elif Tag == 0x09:  # Dict
        if Offset + 4 > len(Buffer): raise ValueError("Buffer underflow reading Dict Count")
        Count = int.from_bytes(Buffer[Offset:Offset+4], byteorder='big')
        Offset += 4
        Items = {}
        for _ in range(Count):
            Key, Offset = Unpack(Buffer, Offset)
            Value, Offset = Unpack(Buffer, Offset)
            Items[Key] = Value
        return Items, Offset

    else:
        raise ValueError(f"Unknown unpacking tag: {hex(Tag)} at offset {Offset-1}")

Characters = {
    "Symbols": "!#$%&()*+,-.:;<=>?@[]^_{}~",
    "Letters": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "Digits": "0123456789",
}
PossibleChars = "".join(Characters.values())

def CustomBaseEncode(Data, Charset):
    if not Data:
        return ""
        
    # Count leading null bytes to preserve them
    ZeroCount = 0
    for Byte in Data:
        if Byte == 0:
            ZeroCount += 1
        else:
            break
            
    Number = int.from_bytes(Data, 'big')
    Base = len(Charset)
    
    if Number == 0:
        return Charset[0] * ZeroCount
        
    Res = []
    while Number > 0:
        Number, Rem = divmod(Number, Base)
        Res.append(Charset[Rem])
        
    # Prepend the zero-representing characters
    return (Charset[0] * ZeroCount) + ''.join(reversed(Res))

def CustomBaseDecode(EncodedText, Charset):
    if not EncodedText:
        return b""
        
    # Count leading zero-characters to preserve them
    ZeroCount = 0
    for Char in EncodedText:
        if Char == Charset[0]:
            ZeroCount += 1
        else:
            break
            
    Base = len(Charset)
    Number = 0
    # Decode only the non-leading-zero portion
    for Char in EncodedText[ZeroCount:]:
        Number = Number * Base + Charset.index(Char)
        
    if Number == 0:
        return b'\x00' * ZeroCount
        
    ByteLength = (Number.bit_length() + 7) // 8
    # Re-attach the leading null bytes
    return (b'\x00' * ZeroCount) + Number.to_bytes(ByteLength, 'big')