C = Constants[B]
if isinstance(C, tuple) and len(C) >= 3:
    Tag = C[0]
    if Tag == __ENC_STR__:  # Decrypt String
        Data, CharIndex = C[1], C[2]
        S_Char = Data[CharIndex - 1]
        Clean = Data[:CharIndex - 1] + Data[CharIndex:]
        Parts = Clean.split(S_Char)
        # Parts[0]=Encoded, Parts[1]=XorKey, Parts[2]=Charset
        Num = 0
        Base = len(Parts[2])
        for Char in Parts[0]:
            Num = (Num * Base) + Parts[2].index(Char)
        Dec = Num.to_bytes(((Num.bit_length() + 7) // 8), "big").decode("utf-8")
        Registers[A] = "".join(chr(ord(Dec[i]) ^ ord(Parts[1][i % len(Parts[1])])) for i in range(len(Dec)))
    elif Tag == __ENC_INT__:  # Decrypt Integer (Lossless)
        Encoded, Key = C[1], C[2] # Pulling values from the constant tuple
        
        Result = 0
        Shift = 0
        while True:
            # Internalized GetMask Logic
            _A, C_Val, M = 6364136223846793005, 1442695040888963407, 2**64
            Seed = (Key + Shift) ^ 0x5555555555555555
            Mask = (_A * Seed + C_Val) % M
            
            # Process 64-bit chunk from 'Encoded'
            Chunk = (Encoded >> Shift) & 0xFFFFFFFFFFFFFFFF
            Result |= ((Chunk ^ Mask) << Shift)
            
            # Exit if no bits remain to process
            if (Encoded >> (Shift + 64)) in (0, -1):
                break
            Shift += 64
            
        # Reverse ZigZag encoding to handle -inf to inf range
        if Result % 2 == 0:
            Registers[A] = Result >> 1
        else:
            Registers[A] = ~(Result >> 1)
    else:
        Registers[A] = C
else:
    Registers[A] = C