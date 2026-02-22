# 28. Design Patterns in Python — Senior

## Q1. (Easy) Implement a Singleton in Python (classic approach). What’s the caveat with inheritance?

**Answer:**
```python
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```
**Caveat:** Subclasses share the same **_instance** if they don’t override __new__; if they do, each subclass can have its own singleton. For “one per subclass,” use a dict keyed by cls in __new__.

---

## Q2. (Easy) What is the Factory pattern? Give a simple function that acts as a factory.

**Answer:**  
A **factory** creates and returns objects without exposing the constructor. Callers depend on the factory interface. Example: **def create_reader(format): return CSVReader() if format == "csv" else JSONReader()**. The factory chooses the concrete type; callers use the returned object via a common interface (duck typing or ABC).

---

## Q3. (Medium) Implement the Observer (pub/sub) pattern: subscribers register and get notified when an event occurs.

**Answer:**
```python
class Observable:
    def __init__(self):
        self._subscribers = []
    def subscribe(self, fn):
        self._subscribers.append(fn)
    def notify(self, *args, **kwargs):
        for fn in self._subscribers:
            fn(*args, **kwargs)
```
Or use a list of (event, callback) and filter by event. For production, consider an event bus or library (e.g. blinker, pydispatch).

---

## Q4. (Medium) What is the Strategy pattern? How would you implement it in Python?

**Answer:**  
**Strategy** — encapsulate algorithms (or behavior) behind a common interface; swap at runtime. In Python: pass a **callable** or an object with a method. Example: **def process(data, strategy): return strategy(data)** where **strategy** is a function or an object with **process(data)**. No need for a formal interface; duck typing is enough. Could use an ABC for explicit contract.

---

## Q5. (Medium) What is the Context Manager pattern in terms of design patterns? What problem does it solve?

**Answer:**  
It’s a **resource management** pattern: acquire resource on enter, release on exit, even on exception. Ensures cleanup (files, locks, transactions) and avoids leaks. Python’s **with** is the built-in support. Solves: consistent teardown, exception-safe cleanup, and clear scope of the resource.

---

## Q6. (Tough) Implement a simple Dependency Injection container: register a factory for a key, resolve to get an instance (singleton or new each time).

**Answer:**
```python
class Container:
    def __init__(self):
        self._factories = {}
        self._singletons = {}
    def register(self, key, factory, singleton=True):
        self._factories[key] = (factory, singleton)
    def resolve(self, key):
        if key not in self._factories:
            raise KeyError(key)
        factory, singleton = self._factories[key]
        if singleton and key in self._singletons:
            return self._singletons[key]
        obj = factory()
        if singleton:
            self._singletons[key] = obj
        return obj
```
Extend with constructor injection (inspect factory args and resolve dependencies) for full DI.

---

## Q7. (Tough) What is the Repository pattern? How would you use it with an ORM?

**Answer:**  
**Repository** — abstraction over data access; code uses a “repository” (e.g. get_by_id, save, find) instead of direct DB/ORM calls. Benefits: testability (mock the repository), swap storage (in-memory, different DB). With an ORM: repository methods wrap model queries (e.g. **UserRepository.get_by_id** calls **User.query.get**); tests use a fake repository (in-memory list or mock). Keeps domain logic free of ORM details.

---

## Q8. (Tough) When would you use Composition over Inheritance in Python? Give a short example.

**Answer:**  
Prefer **composition** when: you want “has-a” or “uses-a,” you need to swap behavior, or inheritance would create deep/fragile hierarchies. Example: **class Logger:** with a **Formatter** injected: **def __init__(self, formatter): self.formatter = formatter**. You can change formatter without subclassing Logger. **Strategy** and **Dependency Injection** often use composition.

---

## Q9. (Tough) What is the Decorator pattern (design pattern, not Python decorators)? How does Python’s decorator syntax support it?

**Answer:**  
**Decorator pattern** — wrap an object to add behavior without subclassing. Python’s **@decorator** and **decorator(func)** are exactly that: the decorator returns a wrapper (the “decorator” object) that adds behavior and delegates to the original. So the language syntax directly supports the design pattern for functions/methods; for classes, class decorators or wrappers do the same.

---

## Q10. (Tough) Implement a simple Circuit Breaker: after N failures, stop calling the real function for a cooldown period, then try again.

**Answer:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
            else:
                raise Exception("Circuit open")
        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.monotonic()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise
```
(Add **time** import; optionally wrap as a decorator.)
