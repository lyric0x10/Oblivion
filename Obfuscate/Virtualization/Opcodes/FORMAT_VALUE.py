# Format = ["FORMAT_VALUE", DestReg, ValueReg, [Conversion, Format_Spec]]
Value = Registers[B]
Conversion = C[0]
Format_Spec = C[1]

if Conversion == 115:
    Value = str(Value)
elif Conversion == 114:
    Value = repr(Value)
elif Conversion == 97:
    Value = ascii(Value)
Registers[A] = format(Value, Format_Spec or "")