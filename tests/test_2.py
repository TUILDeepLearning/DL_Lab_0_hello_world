import os
import nbformat
from nbconvert import PythonExporter

def test_hello_world_message():
    # load the notebook
    nb_path = "notebooks/hello_world.ipynb"
    assert os.path.exists(nb_path), "Notebook not found!"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # export to python code
    exporter = PythonExporter()
    source, _ = exporter.from_notebook_node(nb)

    # execute the code and capture the namespace
    namespace = {}
    exec(source, namespace)

    assert "message" in namespace, "Variable 'message' not found in the notebook."
    assert namespace["message"].strip().lower() == "hello world 2", (
        f"Your variable is: {namespace['message']!r} – it should be 'Hello World'."
    )