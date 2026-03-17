# Format = ["POP_BLOCK"]
# No register operands.
# Pops the innermost block frame from the BlockStack once the protected
# region (try-body or finally-body) has been exited cleanly.
BlockStack.pop()
