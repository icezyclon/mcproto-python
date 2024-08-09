from contextlib import contextmanager
from functools import partial
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.ext.autodoc import ClassDocumenter, MethodDocumenter

filename = Path(__file__).stem

print = partial(print, f"[{filename}]:")


@contextmanager
def patched(obj, name, new):
    try:
        old = getattr(obj, name)
        obj.name = new
        yield
    finally:
        obj.name = old


def process_docstring(app, what, name, obj, options, lines):
    """
    Event handler for autodoc-process-docstring.
    Modify the displayed name of the documented objects here.
    """
    # Check for a custom alias in the options
    if "alias" in options:
        print("ALIAS")
        # Insert the alias at the beginning of the docstring
        alias = options["alias"]
        lines.insert(0, f".. _{alias}:\n\n**{alias}**\n")


def process_signature(app, what, name, obj, options, signature, return_annotation):
    """
    Event handler for autodoc-process-signature.
    Modify the signature of the documented objects here.

    Parameters:
    - app: Sphinx application object
    - what: Type of the object ('module', 'class', 'exception', 'function', 'method', 'attribute')
    - name: Fully qualified name of the object
    - obj: The documented object
    - options: Options given to the directive
    - signature: The signature string (if any)
    - return_annotation: The return type annotation (if any)
    """
    # Modify the signature or return_annotation as needed
    if what == "class" and name:
        # print(obj)
        classname = (name.split(".")[-1] if "." in name else name).strip()
        args = signature.split(",")
        types = [sig.split(":")[1] for sig in args if ":" in sig]
        lasts = [t.split(".")[-1] if "." in t else t for t in types]
        lasts = [l.strip() for l in lasts]
        if classname.startswith("_") or any(l.startswith("_") for l in lasts):
            print(f"Delete signature of {classname}")
            signature = ""

    # signature = "(custom_arg1, custom_arg2)"
    # return_annotation = "-> CustomReturnType"
    # print(signature, return_annotation)
    return signature, return_annotation


class CustomClassDocumenter(ClassDocumenter):
    objtype = "class"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._last_line_skipped = False

    def add_line(self, line, *args):
        # Example: Add custom behavior here
        if line.startswith(".. py:class:: _"):
            # class starts with underscore
            # line = line.replace("class ", "custom_class ")
            print("SKIP:", line)
            self._last_line_skipped = True
            line = "-----"
        elif self._last_line_skipped:
            print("SKIP:", line)
            self._last_line_skipped = False
            line = ""
            # line = ".. py:class:: World Options"
        else:
            print("ADD:", line)
        super().add_line(line, *args)

    # def add_directive_header(self, sig):
    #     sourcename = self.get_sourcename()
    #     if sourcename.find(":docstring of ") >= 0:
    #         cl = sourcename.split(" ")[-1].split(".")[-1]
    #         # do not write the "class _ClassName..." line if it starts with "_"
    #         if cl.startswith("_"):
    #             self.add_line("---", sourcename)
    #             print("REPLACING", sourcename)
    #             return
    #     return super().add_directive_header(sig)


class CustomMethodDocumenter(MethodDocumenter):
    objtype = "method"

    def format_name(self):
        orig = super().format_name()
        print("ORIG", orig)
        if orig.startswith("_") and "." in orig:
            splits = orig.split(".")
            return "".join(splits[1:])
        return orig

    # def add_directive_header(self, sig):
    #     sourcename = self.get_sourcename()
    #     if sourcename.find(":docstring of ") >= 0:
    #         spaced = sourcename.split(" ")
    #         splits = spaced[-1].split(".")
    #         cl = splits[-2]
    #         method = splits[-1]

    #         def new_sig():
    #             sig = "".join(spaced[:-1] + splits[:-2] + [method])
    #             print("NEWSIG:", sig)
    #             return sig

    #         # do not write the "class _ClassName..." line if it starts with "_"
    #         if cl.startswith("_"):
    #             # self.add_line("---", sourcename)
    #             with patched(self, "get_sourcename", new_sig):
    #                 return super().add_directive_header(sig)

    #     return super().add_directive_header(sig)


class CurrentModuleDirective(Directive):
    has_content = True

    def run(self):
        # Process the content and create a node
        print("DIRECTIVE")
        paragraph = nodes.paragraph(text="\n".join(self.content))
        print(paragraph)
        return [paragraph]


def setup(app):
    # print(dir(app))
    # print(help(app.add_directive))
    # app.add_directive("currentmodule", CurrentModuleDirective, override=True)
    # app.add_autodocumenter(CustomMethodDocumenter)

    # app.add_autodocumenter(CustomClassDocumenter)
    app.connect("autodoc-process-signature", process_signature)

    pass
