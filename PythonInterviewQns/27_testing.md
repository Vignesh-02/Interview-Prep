# 27. Testing (pytest, mocking, fixtures) — Senior

## Q1. (Easy) What is the difference between unittest and pytest? Why might you prefer pytest?

**Answer:**  
**unittest** is in the standard library; class-based, **assertEqual**-style. **pytest** is third-party; uses plain **assert**, **fixtures**, **parametrize**, and auto-discovery. Prefer **pytest** for: less boilerplate, better failure output, fixtures and plugins, parametrized tests, and a large ecosystem. unittest is built-in and familiar to Java/JUnit users.

---

## Q2. (Easy) How do you run tests with pytest? How do you run a single test or a file?

**Answer:**  
**pytest** (no args) discovers and runs tests (files **test_*.py** or ***_test.py**, functions **test_***). **pytest path/to/test_file.py** runs that file. **pytest path/to/file.py::test_name** runs one test. **pytest -v** verbose; **-k "substring"** filter by name; **--tb=short** shorter tracebacks.

---

## Q3. (Medium) What is a fixture? How do you define and use one?

**Answer:**  
A **fixture** is a dependency (setup/teardown) for tests. Define with **@pytest.fixture**; use by adding a parameter with the **same name** to the test. Pytest injects the return value. **Scope**: function (default), class, module, session. Use for DB connections, temp dirs, mocks, etc. **yield** in a fixture: code after yield runs as teardown.

---

## Q4. (Medium) What is a mock (or MagicMock)? When would you use it?

**Answer:**  
A **mock** (unittest.mock.Mock or MagicMock) is a fake object that records calls and can define return values/side effects. Use to **isolate** the code under test from real dependencies (network, DB, file system). **patch** replaces an attribute/import with a mock for the duration of the test. **MagicMock** supports magic methods (e.g. __len__); **Mock** doesn’t by default.

---

## Q5. (Medium) What is pytest.raises? How do you assert that code raises an exception?

**Answer:**  
**with pytest.raises(SomeError):** runs the block and passes if **SomeError** (or subclass) is raised; fails if no exception or wrong type. **pytest.raises(SomeError).match("regex")** also checks the message. Use **as excinfo** to inspect **excinfo.value**. So you both assert the exception and can inspect it.

---

## Q6. (Medium) What is parametrize? Give an example.

**Answer:**  
**@pytest.mark.parametrize("arg1,arg2", [(a1, a2), ...])** runs the same test with different **(arg1, arg2)**. Each tuple is one case. Example: **@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (0, 0, 0)])** then **def test_add(a, b, expected): assert add(a, b) == expected**. Reduces duplication for many inputs.

---

## Q7. (Tough) How do you patch a function used inside the module under test (e.g. patch where it’s used, not where it’s defined)?

**Answer:**  
**Patch where it’s used (looked up).** If **mymodule** does **from other import func** and uses **func**, patch **mymodule.func** (the reference in mymodule’s namespace), not **other.func**. Use **@patch("mymodule.func")** or **with patch("mymodule.func") as mock_func:**. The target string is the dotted path in the namespace where the object is looked up.

---

## Q8. (Tough) What is the difference between Mock.return_value and Mock.side_effect?

**Answer:**  
**return_value** — single value returned for every call. **side_effect** — can be: an **exception** (raised when called), an **iterable** (each call gets the next value), or a **function** (called with the same args; return value is the mock’s return). Use **side_effect** for different returns per call or to raise. Use **return_value** for a constant return.

---

## Q9. (Tough) How do you test async code with pytest? What plugin or built-in support?

**Answer:**  
Use **pytest-asyncio**. Mark async tests: **@pytest.mark.asyncio** and define **async def test_...**. Run with **pytest** (plugin installed). Or use **asyncio.run()** inside a sync test to run one coroutine. **pytest-asyncio** can also provide an event loop fixture and support async fixtures.

---

## Q10. (Tough) What are best practices for test isolation and avoiding flaky tests?

**Answer:**  
**Isolation**: Each test independent; no shared mutable state; use fixtures for setup/teardown; patch/mock external services. **Avoid flakiness**: No **time.sleep** or real time if avoidable; mock time/network; avoid order-dependent tests; don’t rely on dict/set iteration order unless guaranteed; use fixed seeds for randomness; run in clean env (temp dir, test DB). Prefer fast, deterministic tests.
