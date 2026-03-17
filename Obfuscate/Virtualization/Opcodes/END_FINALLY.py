# Format = ["END_FINALLY"]
# No register operands.
# Signals the end of a finally block. If the VM entered the finally block
# due to a pending exception or return value, that state is restored and
# propagated now. Otherwise execution continues normally.
FinallyState = BlockStack.pop() if BlockStack and BlockStack[-1][0] == "finally_resume" else None
if FinallyState and FinallyState[1] is not None: raise FinallyState[1]
