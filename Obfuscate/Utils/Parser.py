import ast
import python_minifier
import subprocess

def Node_To_Dict(node):
    if isinstance(node, ast.AST):
        return {field: Node_To_Dict(value) for field, value in ast.iter_fields(node)} | {"_type": type(node).__name__}
    elif isinstance(node, list):
        return [Node_To_Dict(item) for item in node]
    return node

def Minify(Code):
    return python_minifier.minify(
        Code,
        remove_annotations=True,
        remove_literal_statements=True,
        remove_pass=True,
        preserve_shebang=False,
        combine_imports=True,
        hoist_literals=True,
        rename_locals=False,
        rename_globals=False,
        remove_object_base=True,
        convert_posargs_to_args=True,
        remove_asserts=True,
        remove_debug=True,
        remove_explicit_return_none=True,
        remove_builtin_exception_brackets=True,
        constant_folding=True,
    )

def Format(Code):
    try:
        result = subprocess.run(
            ["ruff", "format", "-"],
            input=Code,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return Code

def Parse(Code):
    return [Node_To_Dict(node) for node in ast.parse(Code).body]