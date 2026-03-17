# Format = ["POP_EXCEPT"]
# No register operands.
# Clears the active exception state and pops the except-block frame after
# a handler body has finished executing successfully.
ActiveException = None
BlockStack.pop()
