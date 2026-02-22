# 15. Modules and Packages

## Q1. (Easy) What is a module? How do you import one?

**Answer:**  
A **module** is a file containing Python code (`.py`). Import with **`import module_name`** (use `module_name.attr`) or **`from module_name import attr`**. The file’s global namespace becomes the module’s attributes. Import runs the file once; subsequent imports reuse the same module object (cached in **sys.modules**).

---

## Q2. (Easy) What does `if __name__ == "__main__":` do? When is it true?

**Answer:**  
When the file is run as a **script** (e.g. `python file.py`), **`__name__`** is **`"__main__"`**. When the file is **imported**, `__name__` is the module name. So code under `if __name__ == "__main__":` runs only when the file is executed as the main program, not when imported. Used for tests, CLI entry points, or demo code.

---

## Q3. (Easy) What is the difference between `import x` and `from x import *`?

**Answer:**  
**import x** — use `x.attr`; namespace is explicit. **from x import *** — copies (most) names from `x` into the current namespace; can cause name clashes and is discouraged. Prefer explicit imports. `__all__` in the module can limit what `import *` brings in.

---

## Q4. (Medium) What is a package? How does Python recognize it?

**Answer:**  
A **package** is a directory containing an **`__init__.py`** file (or a namespace package without it in Python 3). Python recognizes it as a package so you can do **`import package`** or **`from package import module`**. `__init__.py` can be empty or run package-level initialization. **Namespace packages** (PEP 420) allow packages without __init__.py across multiple directories.

---

## Q5. (Medium) What is `sys.path`? What is the order of search when you import?

**Answer:**  
**sys.path** is a list of directories where Python looks for modules. Order: (1) directory of the script (or ""), (2) PYTHONPATH env, (3) installation-dependent default (site-packages, etc.). The first matching module found is used. You can modify sys.path (e.g. append project root) but prefer proper packaging and install.

---

## Q6. (Medium) What does `from package import something` load? Does it load the whole package?

**Answer:**  
It loads the **package** (runs package’s **__init__.py**) and the **module** or subpackage that contains `something`, then binds `something` in the current namespace. So yes, the package (and the specific module) get loaded. Submodules are loaded on first access when using **from package.submodule import x**.

---

## Q7. (Medium) What is `__all__`? What is it used for?

**Answer:**  
**__all__** is a list of strings (names) in a module. It defines the **public API** for **`from module import *`** — only those names are imported. It also helps documentation and static checkers. Without __all__, `import *` brings all names that don’t start with `_`.

---

## Q8. (Tough) What is a circular import? How can you avoid or fix it?

**Answer:**  
**Circular import** happens when A imports B and B imports A (directly or through a chain). When one module is only partially loaded, the other may see incomplete definitions. Fixes: (1) Restructure to remove the cycle (extract shared code to a third module). (2) Do the import inside the function that needs it (lazy import). (3) Use **importlib** or move one import to the bottom. Avoid circular dependencies at the design level when possible.

---

## Q9. (Tough) What is the difference between a package and a namespace package (PEP 420)?

**Answer:**  
A **regular package** has **__init__.py**; that directory is the package. A **namespace package** has no __init__.py (or only in some portions); multiple directories can contribute to the same package name. Used for split installations and plugin-style layouts. Import system merges namespace package portions when the same name is found on sys.path.

---

## Q10. (Tough) How do you run a module as a script with `python -m package.module`? What does `__package__` contain?

**Answer:**  
**`python -m package.module`** runs **package/module.py** with **__name__ == "__main__"** and **__package__ == "package"**. So the loader knows the package context (for relative imports). **__package__** is set to the package name (or "" for top-level). Useful for running tests or CLI entry points with correct import context.
