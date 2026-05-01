import ast
import tarfile
import os
import shutil
from pathlib import Path
from typing import Optional

from app.core.logging import setup_logger

logger = setup_logger(__name__)

class MaliciousPayloadRemover(ast.NodeTransformer):
    def __init__(self, target_nodes=None):
        self.target_nodes = target_nodes or []
        self.modified = False

    def visit_Call(self, node):
        self.generic_visit(node)
        
        # Simple heuristic to identify eval(base64...)
        if isinstance(node.func, ast.Name) and node.func.id == 'eval':
            if len(node.args) > 0 and isinstance(node.args[0], ast.Call):
                b64_call = node.args[0]
                if isinstance(b64_call.func, ast.Attribute) and b64_call.func.attr == 'b64decode':
                    self.modified = True
                    # Replace with a safe no-op or pass
                    return ast.Pass()
        return node
        
    def visit_Assign(self, node):
        self.generic_visit(node)
        return node


class NeutralizerService:
    def __init__(self, temp_dir: str = "/tmp/obelisk_neutralizer"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def neutralize_python_package(self, package_path: str, output_path: str) -> bool:
        """
        Extracts a tar.gz package, parses python files, removes malicious AST nodes,
        re-packs it into output_path.
        """
        pkg_name = Path(package_path).stem.replace('.tar', '')
        extract_dir = self.temp_dir / pkg_name
        
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir()

        try:
            with tarfile.open(package_path, "r:gz") as tar:
                # Basic protection against path traversal
                def is_within_directory(directory, target):
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    return prefix == abs_directory

                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                    tar.extractall(path, members, numeric_owner=numeric_owner)

                safe_extract(tar, str(extract_dir))
                
            modified_any = False
            for py_file in extract_dir.rglob("*.py"):
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                try:
                    tree = ast.parse(source)
                    remover = MaliciousPayloadRemover()
                    new_tree = remover.visit(tree)
                    
                    if remover.modified:
                        ast.fix_missing_locations(new_tree)
                        clean_source = ast.unparse(new_tree)
                        
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(clean_source)
                        modified_any = True
                        logger.info(f"Neutralized malicious payload in {py_file}")
                except SyntaxError:
                    logger.warning(f"Could not parse AST for {py_file}")

            # Re-tar the sanitized directory
            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(str(extract_dir), arcname=os.path.basename(str(extract_dir)))
                
            return modified_any

        except Exception as e:
            logger.error(f"Failed to neutralize package {package_path}: {e}")
            return False
        finally:
            if extract_dir.exists():
                shutil.rmtree(extract_dir)

neutralizer_service = NeutralizerService()
