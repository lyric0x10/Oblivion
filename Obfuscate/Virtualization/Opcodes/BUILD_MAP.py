# Format = ["BUILD_MAP", DestReg, PairsData]
# PairsData is a list of (KeyReg, ValReg) tuples.
# A KeyReg of None signals a **unpack (dict merge) instead of a key-value insert.
Registers[A] = {k: v for k, v in ((Registers[K], Registers[V]) for K, V in B if K is not None)} | {k: v for Src in (Registers[V] for K, V in B if K is None) for k, v in Src.items()}
