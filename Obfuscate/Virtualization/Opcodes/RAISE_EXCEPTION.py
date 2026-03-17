# Format = ["RAISE_EXCEPTION"]
# No register operands.
# Re-raises the active exception when no handler matched. The VM unwinds
# the BlockStack until it finds an enclosing except or finally frame, or
# propagates the exception to the caller if the stack is empty.
raise ActiveException
