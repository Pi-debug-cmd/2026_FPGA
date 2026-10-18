import zipfile
wheel = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\dependency_source_audit\speechbrain-0.5.16-py3-none-any.whl"
with zipfile.ZipFile(wheel) as z:
    text = z.read('speechbrain/lobes/models/transformer/Transformer.py').decode()
import ast
tree = ast.parse(text)
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "PositionalEncoding":
        import ast
        print(ast.unparse(node))
