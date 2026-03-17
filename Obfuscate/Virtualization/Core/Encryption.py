import random

Characters = {
    "Symbols": "!#$%&()*+,-.:;<=>?@[]^_{}~",
    "Letters": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "Digits": "0123456789",
}
PossibleChars = "".join(Characters.values())

def XorCipher(Text, Key):
    Result = "".join(chr(ord(Text[I]) ^ ord(Key[I % len(Key)])) for I in range(len(Text)))
    return Result

def CustomBaseEncode(Text, Charset):
    Base = len(Charset)
    Number = int.from_bytes(Text.encode('utf-8'), 'big')
    if Number == 0: return Charset[0]
    Res = []
    while Number > 0:
        Number, Rem = divmod(Number, Base)
        Res.append(Charset[Rem])
    return ''.join(reversed(Res))

def CustomBaseDecode(EncodedText, Charset):
    Base = len(Charset)
    Number = 0
    for Char in EncodedText:
        Number = Number * Base + Charset.index(Char)
    ByteLength = (Number.bit_length() + 7) // 8
    return Number.to_bytes(ByteLength, 'big').decode('utf-8')

def Encode(String):
    XorKey = "".join(random.sample(PossibleChars, random.randint(6, 12)))
    BaseCharset = "".join(random.sample(PossibleChars, random.randint(6, 24)))
    AvailableSplitters = list(set(PossibleChars) - (set(XorKey) | set(BaseCharset)))
    SplitChar = random.choice(AvailableSplitters)
    EncodedData = CustomBaseEncode(XorCipher(String, XorKey), BaseCharset)
    Combined = EncodedData + SplitChar + XorKey + SplitChar + BaseCharset
    InsertIndex = random.randint(0, len(Combined) - 1)
    FinalStr = Combined[:InsertIndex] + SplitChar + Combined[InsertIndex:]
    return (FinalStr, InsertIndex + 1)

def Decode(Str, Index):
    SplitChar = Str[Index - 1]
    CleanedStr = Str[:Index - 1] + Str[Index:]
    Parts = CleanedStr.split(SplitChar)
    DecodedXor = CustomBaseDecode(Parts[0], Parts[2])
    return XorCipher(DecodedXor, Parts[1])

def TransformToPos(Num):
    """ZigZag encoding to map negative infinity...infinity to 0...infinity."""
    return (Num << 1) ^ (Num >> 256) if Num < 0 else Num << 1

def GetMask(Key, SeedOffset):
    """Deterministic PRNG mask for a specific chunk."""
    A = 6364136223846793005
    C = 1442695040888963407
    M = 2**64
    Seed = (Key + SeedOffset) ^ 0x5555555555555555
    return (A * Seed + C) % M

def NumEncrypt(Num, Key):
    """Lossless integer encryption for any size."""
    Val = TransformToPos(Num)
    Result = 0
    Shift = 0
    Temp = Val
    # Process in 64-bit blocks to handle arbitrary sizes
    while Temp > 0 or Shift == 0:
        Mask = GetMask(Key, Shift)
        Chunk = Temp & 0xFFFFFFFFFFFFFFFF
        Result |= ((Chunk ^ Mask) << Shift)
        Temp >>= 64
        Shift += 64
        if Temp == 0: break
    return Result