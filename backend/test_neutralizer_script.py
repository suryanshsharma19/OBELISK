import ast
import sys
from app.services.neutralizer_service import MaliciousPayloadRemover

malicious_code = """
import os
import base64

def clean_function():
    print("Doing normal things")

# Malicious line below
eval(base64.b64decode(b'cGF5bG9hZA=='))

def another_clean_function():
    return 42
"""

tree = ast.parse(malicious_code)
remover = MaliciousPayloadRemover()
new_tree = remover.visit(tree)
ast.fix_missing_locations(new_tree)
clean_source = ast.unparse(new_tree)

if "print('Doing normal things')" in clean_source or 'print("Doing normal things")' in clean_source:
    pass
else:
    print("Failed to keep clean_function")
    sys.exit(1)

if "eval(base64" not in clean_source and remover.modified == True:
    print("SUCCESS: Malicious payload was successfully neutralized while keeping safe code intact.")
else:
    print("FAILED: Malicious payload was not removed.")
    sys.exit(1)
