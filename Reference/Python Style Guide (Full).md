# Python Style Guide

A comprehensive guide reflecting proven patterns for maintainable, type-safe, and reactive Python code.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Formatting](#formatting)
3. [Naming Conventions](#naming-conventions)
4. [Type Hints](#type-hints)
5. [Imports](#imports)
6. [Code Organization](#code-organization)
7. [Architecture Patterns](#architecture-patterns)
8. [Error Handling](#error-handling)
9. [Functions vs Methods](#functions-vs-methods)
10. [Classes and Inheritance](#classes-and-inheritance)
11. [Data and State Management](#data-and-state-management)
12. [Async Patterns](#async-patterns)
13. [Testing](#testing)
14. [Documentation](#documentation)
15. [Tooling](#tooling)
16. [Anti-Patterns](#anti-patterns)
17. [Decision Trees](#decision-trees)

---

## Core Principles

### Type Safety as Foundation
Use the type system not just for documentation but as a design tool. Let the type checker provide guarantees about code correctness. Types enable the "look before you leap" philosophy without runtime checks.

### Immutability + Reactivity
Prefer immutable data structures for caching and correctness. Use reactive patterns (AsyncIterable, Futures) to handle mutation when needed.

### Clear Separation of Concerns
- Use Protocols to define behavioral contracts
- Layer inheritance where each layer does one thing
- Separate data (Pydantic models) from context (hand-written classes)
- Keep side effects explicit and isolated

### Explicit Over Implicit
- Pass context explicitly through function signatures
- Avoid module-level mutable state
- Make stateful objects visible in type signatures
- Use `__all__` to control API surface area

---

## Formatting

### Line Length
**Target: 60 characters (soft limit), 80 characters (hard limit)**

Rationale: Works well with vertical window splits while maintaining readability. Aim for 60 but allow up to 80 when breaking would hurt clarity.

### Multi-line Constructs
Closing delimiter goes on its own line, aligned with the opening line:

```python
# Function signatures
def my_function(
    param1: MyType,
    param2: MyType | None = None
) -> MyType:
    ...

# Lists
my_list = [
    item1,
    item2,
    item3
]

# Dictionaries
my_dict = {
    'key1': value1,
    'key2': value2
}

# Function calls
result = some_function(
    arg1,
    arg2,
    arg3
)

# Class definitions with multiple inheritance
class MyClass(
    FirstMixin,
    SecondMixin,
    BaseClass
):
    ...
```

### String Quotes
**Differentiate by role:**
- **Double quotes `"`**: Text content, user-facing strings, messages
- **Single quotes `'`**: Keywords, dictionary keys, literals, constants

```python
# Good
user_message = "Welcome to the application"
config = {'api_key': 'prod', 'timeout': 30}
status = 'active'

# Avoid
user_message = 'Welcome'  # Should be double quotes
config = {"api_key": "prod"}  # Should be single quotes
```

### Blank Lines
- Two blank lines between top-level definitions
- One blank line between methods in a class
- Use blank lines sparingly within functions to separate logical sections

---

## Naming Conventions

### General Rules (PEP 8)
- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `ALL_CAPS`
- **Private members**: `_leading_underscore`

### Protocol/Implementation Hierarchy
Clear naming reveals the architectural layer:

```python
# Protocol: Simplest name, defines contract
class Animal(Protocol):
    def make_sound(self) -> str: ...

# Base class: Add "Base" suffix
class AnimalBase(ABC):
    def __init__(self, name: str):
        self.name = name

# Mixin: Add "Mixin" suffix
class GreyAnimalMixin(AnimalBase, ABC):
    @property
    def color(self) -> str:
        return "grey"

# Concrete: Specific prefix
class ElephantAnimal(GreyAnimalMixin, MammalAnimalBase):
    def make_sound(self) -> str:
        return "trumpet"
```

### Module-Level Objects
- **Constants**: `ALL_CAPS` at module level
- **Singletons**: `snake_case` at module level (though rare)
- **Module-level loggers**: `_log`

```python
# constants.py
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# app.py
_log = logging.getLogger()
_jinja_env = Environment(loader=PackageLoader('mypackage'))
```

---

## Type Hints

### Requirements
**Type hints are required everywhere:**
- All function signatures (parameters and return types)
- Variables when the type checker cannot infer them
- Class attributes

### Signature Types: Prefer Abstract
Use the most general type that provides required functionality:

```python
from collections.abc import Iterable, Mapping, Sequence

# Good - accepts any iterable
def process_items(items: Iterable[str]) -> list[str]:
    # Often copy to concrete type internally
    items = list(items)
    return [item.upper() for item in items]

# Too specific
def process_items(items: list[str]) -> list[str]:
    ...
```

### Instance Types: Prefer Built-in
When instantiating or annotating concrete types, use built-in generics:

```python
# Good - no import needed
items: list[str] = []
mapping: dict[str, int] = {}

# Avoid - requires typing import
from typing import List, Dict
items: List[str] = []
mapping: Dict[str, int] = {}
```

### Type Checking Philosophy
**Prefer runtime type checks over casts:**

```python
# Good
if isinstance(value, str):
    result = value.upper()
else:
    result = str(value).upper()

# Avoid
result = cast(str, value).upper()
```

**Static checker must resolve everything.** If the type checker complains, fix the types, don't suppress or cast.

---

## Imports

### Organization
Group imports into three sections with blank lines between:

1. Standard library
2. External packages
3. Internal/local modules

```python
# Standard library
import asyncio
import logging
from pathlib import Path
from typing import Protocol

# External packages
import yaml
from pydantic import BaseModel

# Internal
from .protocols import Animal
from .utils import format_name
```

### Import Style
**Prefer `from` imports over whole module imports:**

```python
# Preferred
from pathlib import Path
from collections.abc import Iterable

# Avoid (unless name conflicts)
import pathlib
import collections.abc
```

### `__all__` Export Control
Every module should explicitly define `__all__` to indicate items exposed at the package level:

```python
# animals.py
from typing import Protocol

__all__ = ['Animal', 'create_animal']

class Animal(Protocol):
    ...

def create_animal(name: str) -> Animal:
    ...
```

Package `__init__.py` imports from modules:

```python
# __init__.py
from .animals import *
from .handlers import *

# Now package.Animal and package.create_animal are available
```

### Type Variable and Alias Placement
Place between imports and constants:

```python
# mymodule.py
from typing import TypeVar, Protocol

__all__ = ['process', 'Item']

# Type variables and aliases
T = TypeVar('T')
ItemID = str | int

# Constants
MAX_ITEMS = 100

# Rest of module
...
```

---

## Code Organization

### Module Structure
Standard order for module contents:

1. Module docstring
2. Imports (stdlib, external, internal)
3. `__all__` definition
4. Type variables and aliases
5. Constants
6. Module-level functions
7. Classes
8. Main block (if applicable)

### Function Length
**Keep functions short enough to read at a glance.** If a function doesn't fit comfortably on screen at your line length, it's probably too long.

**Rule of thumb:** 10-20 lines for most functions, up to 30 for complex logic. Beyond that, extract helper functions.

### Class Organization
Order class members consistently:

1. Class-level variables and constants
2. `__init__` and factory/clone methods
3. Properties (using `@property`)
4. Public methods
5. Private methods (mixed with public as logical)
6. Abstract methods/properties (at the end)

```python
class DataProcessor(ProcessorBase):
    # Class-level
    DEFAULT_BATCH_SIZE = 100
    
    # Construction
    def __init__(self, config: Config):
        self.config = config
        self._cache: dict[str, Any] = {}
    
    @classmethod
    def from_file(cls, path: Path) -> 'DataProcessor':
        ...
    
    # Properties
    @property
    def cache_size(self) -> int:
        return len(self._cache)
    
    # Public methods
    def process(self, data: str) -> Result:
        ...
    
    # Private methods
    def _validate(self, data: str) -> bool:
        ...
    
    # Abstract (from base)
    @abstractmethod
    def _transform(self, data: str) -> str:
        ...
```

---

## Architecture Patterns

### Protocol-First Design

**Protocols define behavioral contracts.** They live in a centralized location (often `protocols.py` or organized by domain in `protocols/`) to avoid circular imports.

```python
# protocols/animals.py
from typing import Protocol

class Animal(Protocol):
    """Contract for animal-like objects."""
    
    @property
    def name(self) -> str: ...
    
    def make_sound(self) -> str: ...
    
    async def feed(self) -> None: ...
```

**Key benefits:**
- Prevents circular imports
- Documents public contracts
- Enables structural subtyping
- Makes testing easier (test the protocol, not implementation)

### Layered Inheritance

Use inheritance to separate orthogonal concerns. Each layer does one thing well.

```python
# Base provides common functionality
class AnimalBase(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def make_sound(self) -> str: ...

# Mixin adds specific capability
class GreyAnimalMixin(AnimalBase, ABC):
    @property
    def color(self) -> str:
        return "grey"

# Another orthogonal concern
class MammalAnimalBase(AnimalBase, ABC):
    @property
    def warm_blooded(self) -> bool:
        return True

# Concrete combines layers
class ElephantAnimal(GreyAnimalMixin, MammalAnimalBase):
    def make_sound(self) -> str:
        return "trumpet"
```

**When to use:** Genuinely orthogonal concerns that need to be mixed-and-matched. Don't over-engineer simple cases.

**Warning:** Keep inheritance depth ≤ 4 levels. If deeper, reconsider the design.

### Lazy Computation Classes

For complex or slow computations, encapsulate inputs in a class and use lazy properties for computation steps:

```python
from functools import cache

class DataAnalysis:
    """Encapsulates analysis inputs with lazy computation."""
    
    def __init__(self, raw_data: list[float]):
        self._raw_data = raw_data
    
    @property
    @cache
    def cleaned_data(self) -> list[float]:
        """First step: clean data."""
        return [x for x in self._raw_data if x > 0]
    
    @property
    @cache
    def mean(self) -> float:
        """Depends on cleaned_data."""
        return sum(self.cleaned_data) / len(self.cleaned_data)
    
    @property
    @cache
    def variance(self) -> float:
        """Depends on cleaned_data and mean."""
        mean = self.mean
        return sum(
            (x - mean) ** 2 for x in self.cleaned_data
        ) / len(self.cleaned_data)
```

**Benefits:**
- Explicit dependency graph (via property usage)
- Automatic caching
- Only computes what's needed
- Clear separation of computation steps

### Data vs Context

**Data classes:** Use frozen Pydantic models

```python
from pydantic import BaseModel

class UserData(BaseModel):
    """Pure data - immutable."""
    model_config = {'frozen': True}
    
    user_id: str
    email: str
    created_at: datetime
```

**Context classes:** Hand-written classes for runtime state

```python
class RequestContext:
    """Runtime context - mutable as needed."""
    
    def __init__(
        self,
        user: UserData,
        session_id: str
    ):
        self.user = user
        self.session_id = session_id
        self.start_time = datetime.now()
    
    @property
    def elapsed(self) -> timedelta:
        return datetime.now() - self.start_time
```

---

## Error Handling

### Philosophy: Type-Guided LBYL + Exception for Errors

**Use types to "look before you leap"** - let the type checker provide guarantees.

**For runtime, distinguish:**
- **Expected conditions**: Use conditionals, not exceptions
- **Error conditions**: Use exceptions

```python
# Expected: key might not exist
def get_config(config: dict[str, str], key: str) -> str:
    return config.get(key, 'default')

# Error: key should exist, it's a bug if it doesn't
def get_required_config(config: dict[str, str], key: str) -> str:
    return config[key]  # Let KeyError raise

# Expected: value might be None
def process_optional(value: int | None) -> int:
    if value is not None:
        return value * 2
    return 0

# Error: value should not be None
def process_required(value: int | None) -> int:
    assert value is not None  # Or raise ValueError
    return value * 2
```

### When to Use Exceptions

**Use exceptions for:**
- Actual errors (bugs, invalid states)
- Deep flow control (timeouts, cancellation)
- External failures (I/O, network)

**Don't use exceptions for:**
- Normal control flow
- Expected variations in data

### Catch Specific Exceptions

Always catch the most specific exception type:

```python
# Good
try:
    value = int(user_input)
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    value = 0

# Avoid
try:
    value = int(user_input)
except Exception:  # Too broad
    value = 0
```

### Custom Exceptions

Create custom exception classes for domain-specific errors:

```python
class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass
```

---

## Functions vs Methods

### When to Use Functions

**Prefer functions that take Protocol-typed arguments** for operations that:
- Feel like external tools or transformations
- Naturally work with multiple protocol types
- Need to be extended without modifying classes

```python
# Good - extensible via protocols
def serialize(obj: Serializable, format: str) -> bytes:
    if format == 'json':
        return json.dumps(obj.to_dict()).encode()
    elif format == 'yaml':
        return yaml.dump(obj.to_dict()).encode()
    raise ValueError(f"Unknown format: {format}")

# Usage
result = serialize(my_object, 'json')
```

### When to Use Methods

**Prefer methods for:**
- Core object operations that feel like intrinsic capabilities
- Operations that primarily manipulate object state
- Operations tightly coupled to the class implementation

```python
class DataBuffer:
    def __init__(self):
        self._items: list[str] = []
    
    # Method - intrinsic to the buffer
    def append(self, item: str) -> None:
        self._items.append(item)
    
    # Method - operates on internal state
    def clear(self) -> None:
        self._items.clear()
```

### Moving Away from "Function Categories"

Avoid classes that just group related functions:

```python
# Avoid - class as namespace
class StringUtils:
    @staticmethod
    def capitalize(s: str) -> str:
        return s.capitalize()
    
    @staticmethod
    def reverse(s: str) -> str:
        return s[::-1]

# Prefer - just functions
def capitalize(s: str) -> str:
    return s.capitalize()

def reverse(s: str) -> str:
    return s[::-1]
```

---

## Classes and Inheritance

### Protocol vs ABC

**Use Protocol for public contracts:**
- Define what users of your code see
- Enable structural subtyping
- Live in centralized location

```python
# protocols/storage.py
class Storage(Protocol):
    async def save(self, key: str, data: bytes) -> None: ...
    async def load(self, key: str) -> bytes: ...
```

**Use ABC for base implementations:**
- Provide shared functionality
- Define what subclasses must implement
- Live with their implementations

```python
# storage/base.py
from abc import ABC, abstractmethod

class StorageBase(ABC):
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def save(self, key: str, data: bytes) -> None:
        ...
    
    @abstractmethod
    async def load(self, key: str) -> bytes:
        ...
    
    # Concrete helper
    def _validate_key(self, key: str) -> None:
        if not key:
            raise ValueError("Key cannot be empty")
```

### Composition Over Inheritance

**Use composition when:**
- Relationship is "has-a" not "is-a"
- You need runtime flexibility
- Combining unrelated capabilities

```python
# Good - composition
class DataProcessor:
    def __init__(
        self,
        storage: Storage,
        validator: Validator
    ):
        self.storage = storage
        self.validator = validator
    
    async def process(self, data: bytes) -> None:
        if self.validator.is_valid(data):
            await self.storage.save('result', data)
```

**Use inheritance when:**
- True specialization relationship
- Sharing implementation across related types
- Multiple orthogonal concerns (via mixins)

### Private Members

**Use single underscore `_private` for internal members:**

```python
class DataCache:
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Any | None:
        if key in self._cache:
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None
```

**Never use double underscore `__private`** (name mangling) - it causes more problems than it solves.

---

## Data and State Management

### Prefer Immutability

Use frozen Pydantic models for data:

```python
from pydantic import BaseModel

class Event(BaseModel):
    model_config = {'frozen': True}
    
    event_id: str
    timestamp: datetime
    data: dict[str, Any]
```

**Why:** Enables caching, prevents accidental mutation, makes data flow clearer.

### Copy-on-Write

When you need to "modify" immutable data:

```python
def update_event(event: Event, new_data: dict[str, Any]) -> Event:
    """Return new event with updated data."""
    return event.model_copy(update={'data': new_data})
```

### State Management Patterns

**Stateful objects are explicit:**

```python
# Pass state explicitly
def process(data: str, context: Context) -> Result:
    ...

# Often with default
def process(
    data: str,
    context: Context | None = None
) -> Result:
    if context is None:
        context = Context()
    ...
```

**Reactive state with async:**

```python
from asyncio import Queue, Future
from collections.abc import AsyncIterable

# Future for single-value state
async def compute() -> int:
    result: Future[int] = asyncio.Future()
    # ... computation sets result ...
    return await result

# AsyncIterable for changing state
async def watch_value() -> AsyncIterable[int]:
    queue: Queue[int] = Queue()
    # ... producer adds to queue ...
    while True:
        value = await queue.get()
        yield value
```

### Module-Level State

**Rare and only for application scope:**

```python
# Acceptable - application-level resource
_jinja_env = Environment(loader=PackageLoader('mypackage'))

# Acceptable - global registry
_registered_handlers: dict[str, Callable] = {}

def register(name: str):
    def decorator(func: Callable) -> Callable:
        _registered_handlers[name] = func
        return func
    return decorator
```

**Module-level logging is appropriate:**

```python
_log = logging.getLogger()
```

---

## Async Patterns

### When to Use Async

**Use async/await for:**
- Long-running computations
- Real-time user feedback
- Network I/O and messaging
- Operations that need to run concurrently

### Protocol-Level Async

Define async at the protocol level when implementations may need to be external or background:

```python
class DataSource(Protocol):
    async def fetch(self) -> list[Record]:
        """Fetch data - may be network call or local."""
        ...

# Implementation might be sync internally but matches protocol
class LocalDataSource:
    async def fetch(self) -> list[Record]:
        # Could be just: return self._local_data
        # But protocol says async, so we maintain it
        return self._local_data

# Implementation that truly needs async
class RemoteDataSource:
    async def fetch(self) -> list[Record]:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)
            return parse_records(response.json())
```

### Async Boundaries

**Be intentional about where async starts:**

```python
# Top-level entry point
async def main():
    config = load_config()  # Sync
    processor = DataProcessor(config)
    await processor.run()  # Async from here

if __name__ == '__main__':
    asyncio.run(main())
```

**For scripts with minimal async needs:**

```python
def process_file(path: Path) -> None:
    # Mostly sync code...
    
    # One async operation
    result = asyncio.run(fetch_metadata(path))
    
    # Back to sync...
```

### Reactive Async Patterns

**AsyncIterable for change streams:**

```python
async def watch_file(path: Path) -> AsyncIterable[str]:
    """Yield file contents whenever it changes."""
    last_modified = path.stat().st_mtime
    
    while True:
        await asyncio.sleep(1)
        current_modified = path.stat().st_mtime
        
        if current_modified > last_modified:
            content = path.read_text()
            yield content
            last_modified = current_modified

# Usage
async for content in watch_file(Path('config.yaml')):
    config = yaml.safe_load(content)
    apply_config(config)
```

**Queues for producer-consumer:**

```python
async def producer(queue: Queue[int]) -> None:
    for i in range(10):
        await queue.put(i)
        await asyncio.sleep(0.1)

async def consumer(queue: Queue[int]) -> None:
    while True:
        item = await queue.get()
        process(item)
        queue.task_done()
```

---

## Testing

### Testing Philosophy: Behavioral

**Test behaviors and contracts, not implementations.**

Focus on:
- Observable outcomes through public APIs
- Protocol contracts (not internal details)
- User-facing behaviors

### Test Organization

**Tests live next to code with `_test` suffix:**

```
mypackage/
    animals.py          # Protocol definitions
    animals_test.py     # Protocol contract tests
    elephant.py         # ElephantAnimal implementation  
    elephant_test.py    # Elephant-specific tests
```

### Testing Protocols

**Test that implementations satisfy the protocol contract:**

```python
# animals_test.py
import pytest
from .animals import Animal
from .elephant import ElephantAnimal
from .lion import LionAnimal

@pytest.fixture(
    params=[ElephantAnimal, LionAnimal],
    ids=['elephant', 'lion']
)
def animal(request) -> Animal:
    """Test with all Animal implementations."""
    return request.param('Test')

def test_animal_has_name(animal: Animal):
    """All animals must have a name."""
    assert animal.name == 'Test'

def test_animal_makes_sound(animal: Animal):
    """All animals must make a sound."""
    sound = animal.make_sound()
    assert isinstance(sound, str)
    assert len(sound) > 0
```

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_fetch():
    source = RemoteDataSource('https://api.example.com')
    records = await source.fetch()
    assert len(records) > 0
```

### Mocking Side Effects

Use mocking for I/O, network, and database operations:

```python
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_processor_with_storage(monkeypatch):
    # Mock the storage
    mock_storage = AsyncMock(spec=Storage)
    mock_storage.save.return_value = None
    
    processor = DataProcessor(mock_storage)
    await processor.process(b'data')
    
    # Verify behavior
    mock_storage.save.assert_called_once_with(
        'result',
        b'data'
    )
```

### Testing Lazy Properties

```python
def test_lazy_computation():
    analysis = DataAnalysis([1.0, 2.0, 3.0, -1.0])
    
    # First access computes
    cleaned = analysis.cleaned_data
    assert cleaned == [1.0, 2.0, 3.0]
    
    # Second access uses cache
    assert analysis.cleaned_data is cleaned
    
    # Dependent properties work
    assert analysis.mean == 2.0
```

### Test Structure

Use pytest with clear test organization:

```python
class TestDataProcessor:
    """Tests for DataProcessor class."""
    
    @pytest.fixture
    def processor(self) -> DataProcessor:
        config = Config(batch_size=10)
        return DataProcessor(config)
    
    def test_process_empty(self, processor: DataProcessor):
        result = processor.process([])
        assert result == []
    
    def test_process_single_item(self, processor: DataProcessor):
        result = processor.process(['item'])
        assert len(result) == 1
```

### Running Type Checker in Tests

**Include a test that runs pyright:**

```python
# conftest.py or type_check_test.py
import subprocess
import pytest

def test_type_checking():
    """Run pyright to ensure type correctness."""
    result = subprocess.run(
        ['pyright', '.'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        pytest.fail(
            f"Type checking failed:\n{result.stdout}"
        )
```

---

## Documentation

### Docstrings: Google Style

Use Google-style docstrings for all public members and members intended to be overridden:

```python
def process_data(
    data: list[str],
    config: Config | None = None
) -> list[Result]:
    """Process data according to configuration.
    
    Transforms input data using the provided configuration
    settings. If no config is provided, uses defaults.
    
    Args:
        data: Input strings to process.
        config: Optional configuration. Defaults to None.
        
    Returns:
        List of processed results.
        
    Raises:
        ValueError: If data is empty.
        ConfigError: If config is invalid.
    """
    if not data:
        raise ValueError("Data cannot be empty")
    ...
```

### When Docstrings Are Required

- All public functions
- All public classes
- All public methods
- Abstract methods/properties (to document contract)
- Methods intended to be overridden

### When Docstrings Are Optional

- Private methods (if purpose is obvious)
- Test functions (name should be descriptive)
- Very simple properties

### Module Docstrings

Start each module with a docstring:

```python
"""Data processing utilities.

This module provides classes and functions for processing
data records, including validation, transformation, and
serialization.
"""
```

### Type Hints + Docstrings

Don't duplicate type information:

```python
# Good - types in signature, explanation in docstring
def calculate(value: float, rate: float) -> float:
    """Calculate result using the given rate.
    
    Args:
        value: The base value.
        rate: Multiplication rate.
        
    Returns:
        The calculated result.
    """

# Avoid - redundant type info
def calculate(value: float, rate: float) -> float:
    """Calculate result using the given rate.
    
    Args:
        value (float): The base value.
        rate (float): Multiplication rate.
        
    Returns:
        float: The calculated result.
    """
```

---

## Tooling

### Type Checker
**Use pyright for static type checking.**

Run pyright as part of your test suite (see Testing section).

### No Linter or Formatter
This style guide serves as the linter. Code review enforces style.

Manual formatting allows for context-sensitive choices that automated tools can't make.

### Testing Framework
**Use pytest** for all testing.

Key features used:
- Fixtures for test setup
- Parametrization for testing multiple implementations
- Markers for async tests (`@pytest.mark.asyncio`)

### Recommended Packages

- **pydantic**: Data validation and settings
- **pyyaml**: Configuration files
- **pathlib**: File path handling (stdlib)
- **asyncio**: Async patterns (stdlib)
- **pytest**: Testing
- **pytest-asyncio**: Async test support

---

## Anti-Patterns

### Avoid: Module-Level Mutable State

```python
# Bad - mutable state
_cache = {}

def get_data(key: str) -> Any:
    if key in _cache:
        return _cache[key]
    # ...
```

**Why:** Makes testing hard, creates hidden dependencies, causes issues in async code.

**Instead:** Pass state explicitly or use proper singleton pattern.

### Avoid: Broad Exception Catching

```python
# Bad
try:
    result = complex_operation()
except Exception:
    result = None
```

**Why:** Hides bugs, makes debugging harder.

**Instead:** Catch specific exceptions you expect.

### Avoid: Mutable Default Arguments

```python
# Bad
def process(items: list[str] = []) -> list[str]:
    items.append('new')
    return items
```

**Why:** Default is shared across calls (common Python gotcha).

**Instead:** Use None and create new instance:

```python
def process(items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append('new')
    return items
```

### Avoid: Methods as Function Categories

```python
# Bad
class StringUtils:
    @staticmethod
    def reverse(s: str) -> str:
        return s[::-1]
```

**Why:** Namespace pollution, less extensible than functions.

**Instead:** Just use functions.

### Avoid: Deep Nesting

```python
# Bad
if condition1:
    if condition2:
        if condition3:
            if condition4:
                # deeply nested code
```

**Why:** Hard to read, high cognitive load.

**Instead:** Use early returns or extract functions:

```python
# Good
if not condition1:
    return early_result
if not condition2:
    return other_result
# ... continue at base level
```

### Avoid: Over-Inheritance

**If your inheritance chain is > 4 levels deep, reconsider.**

```python
# Questionable
class A: ...
class B(A): ...
class C(B): ...
class D(C): ...
class E(D): ...  # Too deep
```

**Why:** Hard to understand, fragile to changes.

**Instead:** Use composition or flatten the hierarchy.

---

## Decision Trees

### Should this be a function or method?

```
Does it feel like an intrinsic capability of the object?
├─ YES → Method
└─ NO → Is it a transformation/tool that could work with multiple types?
    ├─ YES → Function taking Protocol argument
    └─ NO → Is it primarily about this object's state?
        ├─ YES → Method
        └─ NO → Function
```

### Should this be a Pydantic model or hand-written class?

```
Is this pure data?
├─ YES → Does it need to be mutable?
│   ├─ NO → Frozen Pydantic model
│   └─ YES → Regular Pydantic model (reconsider if you really need mutation)
└─ NO → Does it represent runtime context or behavior?
    └─ YES → Hand-written class
```

### Do I need inheritance here?

```
Is this a true "is-a" relationship?
├─ NO → Use composition
└─ YES → Is there shared implementation to reuse?
    ├─ NO → Just implement the Protocol directly
    └─ YES → Are there multiple orthogonal concerns?
        ├─ YES → Consider layered inheritance with mixins
        └─ NO → Single base class with ABC
```

### Should this be async?

```
Does this involve I/O (network, disk, database)?
├─ YES → Make it async
└─ NO → Does it need to run concurrently with other operations?
    ├─ YES → Make it async
    └─ NO → Does the protocol require it?
        ├─ YES → Make it async
        └─ NO → Keep it sync
```

### When should I use Protocol vs ABC?

```
Is this defining a public contract for users of my code?
├─ YES → Protocol (in centralized protocols module)
└─ NO → Is this a base class providing shared implementation?
    └─ YES → ABC (with the implementations)
```

### Boolean comparison: if x vs if x is not None?

```
What is the type of x?
├─ bool → Use "if x:" or "if not x:"
├─ Optional type (e.g., int | None) → Use "if x is not None:"
└─ Container or other → Use "if x:" (unless empty is valid and distinct from None)
```

---

## Complete Examples

### Example 1: Protocol/Base/Mixin/Concrete

```python
# protocols/storage.py
from typing import Protocol

class Storage(Protocol):
    """Contract for storage backends."""
    
    async def save(self, key: str, data: bytes) -> None:
        """Save data under key."""
        ...
    
    async def load(self, key: str) -> bytes:
        """Load data for key."""
        ...

# storage/base.py
from abc import ABC, abstractmethod
import logging

class StorageBase(ABC):
    """Base implementation with common functionality."""
    
    def __init__(self, prefix: str):
        self.prefix = prefix
        self._log = logging.getLogger()
    
    def _full_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}:{key}"
    
    @abstractmethod
    async def save(self, key: str, data: bytes) -> None:
        ...
    
    @abstractmethod  
    async def load(self, key: str) -> bytes:
        ...

# storage/caching.py
class CachingMixin(StorageBase, ABC):
    """Adds caching capability."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: dict[str, bytes] = {}
    
    async def load(self, key: str) -> bytes:
        """Load with caching."""
        full_key = self._full_key(key)
        
        if full_key in self._cache:
            self._log.debug(f"Cache hit: {full_key}")
            return self._cache[full_key]
        
        self._log.debug(f"Cache miss: {full_key}")
        data = await self._load_impl(full_key)
        self._cache[full_key] = data
        return data
    
    @abstractmethod
    async def _load_impl(self, full_key: str) -> bytes:
        """Actual load implementation."""
        ...

# storage/file.py
from pathlib import Path

class FileStorage(CachingMixin, StorageBase):
    """File-based storage with caching."""
    
    def __init__(self, base_dir: Path, prefix: str = ''):
        super().__init__(prefix)
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, key: str, data: bytes) -> None:
        full_key = self._full_key(key)
        path = self.base_dir / full_key
        path.write_bytes(data)
        self._cache[full_key] = data
    
    async def _load_impl(self, full_key: str) -> bytes:
        path = self.base_dir / full_key
        return path.read_bytes()
```

### Example 2: Lazy Computation

```python
from functools import cache
from pathlib import Path
import re

class TextAnalysis:
    """Analyze text file with lazy computation."""
    
    def __init__(self, path: Path):
        self.path = path
    
    @property
    @cache
    def raw_text(self) -> str:
        """Load text from file."""
        return self.path.read_text()
    
    @property
    @cache
    def lines(self) -> list[str]:
        """Split into lines."""
        return self.raw_text.splitlines()
    
    @property
    @cache
    def words(self) -> list[str]:
        """Extract words (depends on raw_text)."""
        return re.findall(r'\w+', self.raw_text.lower())
    
    @property
    @cache
    def word_count(self) -> int:
        """Count words (depends on words)."""
        return len(self.words)
    
    @property
    @cache
    def unique_words(self) -> set[str]:
        """Get unique words (depends on words)."""
        return set(self.words)
    
    @property
    @cache
    def vocabulary_size(self) -> int:
        """Size of vocabulary (depends on unique_words)."""
        return len(self.unique_words)

# Usage
analysis = TextAnalysis(Path('document.txt'))
print(f"Words: {analysis.word_count}")
print(f"Vocabulary: {analysis.vocabulary_size}")
# Only computes what's needed, caches results
```

### Example 3: Reactive Async Pattern

```python
from asyncio import Queue
from collections.abc import AsyncIterable
import asyncio

async def watch_config(
    path: Path,
    interval: float = 1.0
) -> AsyncIterable[dict[str, Any]]:
    """Yield config whenever file changes."""
    last_modified = path.stat().st_mtime
    
    while True:
        await asyncio.sleep(interval)
        
        try:
            current = path.stat().st_mtime
        except FileNotFoundError:
            continue
        
        if current > last_modified:
            content = path.read_text()
            config = yaml.safe_load(content)
            yield config
            last_modified = current

# Usage
async def main():
    config_path = Path('config.yaml')
    
    async for config in watch_config(config_path):
        print(f"Config updated: {config}")
        apply_config(config)

if __name__ == '__main__':
    asyncio.run(main())
```

### Example 4: Function with Protocol Argument

```python
# protocols/serializable.py
from typing import Protocol

class Serializable(Protocol):
    """Objects that can be serialized."""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...

# serialization.py
import json
import yaml
from .protocols.serializable import Serializable

def serialize(
    obj: Serializable,
    format: str = 'json'
) -> bytes:
    """Serialize object to bytes.
    
    Args:
        obj: Object to serialize (must be Serializable).
        format: Output format ('json' or 'yaml').
        
    Returns:
        Serialized bytes.
        
    Raises:
        ValueError: If format is unknown.
    """
    data = obj.to_dict()
    
    if format == 'json':
        return json.dumps(data, indent=2).encode()
    elif format == 'yaml':
        return yaml.dump(data).encode()
    else:
        raise ValueError(f"Unknown format: {format}")

# Any class implementing Serializable works
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    
    def to_dict(self) -> dict[str, Any]:
        return {'name': self.name, 'email': self.email}

user = User('Alice', 'alice@example.com')
data = serialize(user, 'json')
```

---

## Getting Started

### Minimal Viable Style

If you're new to this style or working on a simple project, start with:

1. **Type hints on all functions**
2. **Protocols for public contracts**
3. **Frozen Pydantic models for data**
4. **Explicit imports with `__all__`**
5. **Google-style docstrings on public APIs**

Don't worry about:
- Layered inheritance (use simple classes)
- Lazy computation patterns (use direct computation)
- Complex async patterns (use simple async/await)

### Growing Complexity

As your codebase grows, introduce:

1. **Base classes with ABC** when you have shared implementation
2. **Mixins** when you have orthogonal concerns
3. **Lazy computation** when performance matters
4. **Reactive patterns** when dealing with streams

### When to Apply Each Pattern

**Protocol/Base/Mixin/Concrete:** Use when you have 3+ related classes with genuine layers of concern.

**Lazy computation:** Use when you have expensive operations with dependencies.

**Reactive async:** Use when dealing with real-time data or streams.

**Functions over methods:** Use when operations feel external or need high extensibility.

---

## Summary of Key Principles

1. **Type safety first** - Let the type checker work for you
2. **Immutable by default** - Mutable when necessary, explicit always
3. **Protocols define contracts** - Implementations are private details
4. **Explicit over implicit** - Pass context, avoid global state
5. **Short, focused functions** - Each does one thing well
6. **Test behaviors** - Not implementations
7. **Document the why** - Types show the what
8. **Async for I/O** - Sync for computation
9. **Composition preferred** - Inheritance when justified

---

*This guide reflects patterns proven through practice. Adapt these principles to your specific needs while maintaining the core philosophy of type safety, explicitness, and clear separation of concerns.*
