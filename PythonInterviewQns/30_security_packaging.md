# 30. Security, Packaging, and Best Practices — Senior

## Q1. (Easy) Why is using eval() or exec() on user input dangerous? What are safer alternatives?

**Answer:**  
**eval/exec** run arbitrary code; if the input comes from the user, an attacker can run any Python (e.g. delete files, import os). **Never** use eval/exec on untrusted input. Alternatives: **ast.literal_eval** for literals only (no code). For expressions, use a restricted parser or a DSL; for config use **JSON**, **YAML**, or a safe config parser.

---

## Q2. (Easy) What is the risk of pickle for deserializing untrusted data?

**Answer:**  
**pickle** can execute arbitrary code during **unpickling** (it runs constructors and reduces). Never **loads** or **load** pickle data from an untrusted source. Use **json** for untrusted data, or **restricted unpicklers** (e.g. allowlist of classes) if you must unpickle from a controlled source. Prefer **json**, **msgpack**, or other non-code formats for cross-boundary data.

---

## Q3. (Medium) What is a virtual environment? How do you create and use one?

**Answer:**  
A **virtual environment** is an isolated Python environment: its own **site-packages** and (optionally) interpreter copy. Create: **python -m venv .venv**. Activate: **.venv/bin/activate** (Unix) or **.venv\Scripts\activate** (Windows). Then **pip install** only affects that env. Use one per project to isolate dependencies and avoid version conflicts.

---

## Q4. (Medium) What is pyproject.toml? What sections are commonly used for packaging?

**Answer:**  
**pyproject.toml** (PEP 518+) is the modern way to configure builds and metadata. Common sections: **[build-system]** (e.g. setuptools, hatch); **[project]** — name, version, dependencies, optional deps, requires-python; **[project.scripts]** for entry points; **[tool.setuptools]** or **[tool.hatch]** for package layout. Replaces much of **setup.py** and **setup.cfg** for new projects.

---

## Q5. (Medium) What are entry points? How do you define a console script?

**Answer:**  
**Entry points** (in **pyproject.toml** or **setup.cfg**) register a name to a callable. **Console script**: **[project.scripts]** or **[console_scripts]** — e.g. **mycli = mypkg.cli:main**. When the package is installed, **mycli** is created as a script that calls **main** in **mypkg.cli**. Used for CLI tools and plugin discovery (e.g. **pytest** plugins).

---

## Q6. (Tough) What is SQL injection? How do you prevent it in Python (e.g. with SQLite or PostgreSQL)?

**Answer:**  
**SQL injection** — attacker puts SQL in user input; if you concatenate into a query, they can run arbitrary SQL. **Prevent**: Never build SQL with string concatenation. Use **parameterized queries**: **cursor.execute("SELECT * FROM t WHERE id = ?", (user_id,))** or **%(name)s** with a dict. The driver escapes parameters. Same for **psycopg2**, **sqlite3**, **SQLAlchemy** (use its API, not raw concatenation).

---

## Q7. (Tough) What is the principle of least privilege in the context of running Python apps? How does it apply to file permissions and network?

**Answer:**  
Run with the **minimum** permissions needed: dedicated user, no root; restrict file/dir permissions (read-only where possible); limit network (bind to localhost if only local access, firewall). Use **secrets**/env for credentials; don’t run as root in production. Apply to: process user, open files, network bind/connect, and what the code can import/execute.

---

## Q8. (Tough) How do you securely handle secrets (API keys, passwords) in a Python application? What not to do?

**Answer:**  
**Do**: Use **environment variables** or a secret manager (e.g. AWS Secrets Manager, HashiCorp Vault); load at runtime; use **getpass** for interactive passwords. **Don’t**: Commit secrets to git; hardcode in source; log secrets; put in frontend or URLs. Use **.env** files only if they’re gitignored and only in dev; in production use the platform’s secret store.

---

## Q9. (Tough) What is the difference between a source distribution (sdist) and a wheel (whl)? When would you build each?

**Answer:**  
**sdist** — source archive (tar.gz/zip); contains **pyproject.toml**/setup and source; installer runs build. **wheel** — built distribution; pre-built for a platform/Python version; install is just unpack. Prefer **wheels** for faster, reproducible installs. Build **wheels** for target platforms (CI); publish both so pip can choose wheel when possible and fall back to sdist. **bdist_wheel** and **build** (pyproject) produce wheels.

---

## Q10. (Tough) What are dependency conflicts and how do you manage them (e.g. with pip, pip-tools, poetry)?

**Answer:**  
**Conflicts** — two packages require incompatible versions of the same dependency. **Manage**: (1) **pip** — resolve at install time; **pip check** to see conflicts. (2) **pip-tools** — **pip-compile** locks dependencies from a high-level **requirements.in**; **pip-sync** installs the lock file. (3) **Poetry** — **pyproject.toml** + **poetry.lock**; **poetry install** uses the lock file. Lock files (requirements.txt from pip-compile, poetry.lock) ensure reproducible installs and make conflicts visible at lock time.
