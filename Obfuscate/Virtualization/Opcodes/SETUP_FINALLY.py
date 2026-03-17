# Format = ["SETUP_FINALLY", FinallyOffset]
# A = FinallyOffset (bytecode index of the finally block).
# Pushes a finally-block frame onto the BlockStack so the VM knows where to
# jump on any exit (normal, exception, break, continue, or return).
BlockStack.append(("finally", A))
