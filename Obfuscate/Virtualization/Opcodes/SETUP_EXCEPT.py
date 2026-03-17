# Format = ["SETUP_EXCEPT", HandlerOffset]
# A = HandlerOffset (bytecode index of the first ExceptHandler block).
# Pushes an except-block frame onto the BlockStack. On exception the VM
# sets ActiveException and jumps to HandlerOffset for matching.
BlockStack.append(("except", A))
