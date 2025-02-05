# Universal "Reverse Throttler"

![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📌 Overview

This Python module provides a **lightweight** and **universal** anti-throttling decorator that enforces rate limits on function calls and class methods. It supports both **synchronous** and **asynchronous** and **multithreaded** functions and contex. Ensures that execution adheres to the defined request limits within a specified interval. Additionally, the **target** can be configured to apply throttling at different granularities.

## ✨ Features

- 🚀 **Function and Class Support**: Can be applied to both functions and classes.
- 🔄 **Synchronous and Asynchronous Compatibility**: Works with both standard and async functions.
- 🔑 **Singleton Instance Management**: Ensures only one throttler instance per target.
- 🔒 **Thread-Safe Implementation**: Uses a lock to prevent race conditions.
- ⚙️ **Customizable Interval & Limit**: Define custom request limits over a given time window.
- 🎯 **Target-Specific Throttling**: Allows configuration of the throttling target.
- 🎛️ **Context Manager for Throttling**: Provides a structured way to handle request limits.


---

## 📦 Installation

This module does not require any external dependencies and can be used as a standalone script in your Python project.

---

## 🚀 Usage

### ✅ Basic Function Throttling

```python
from your_module import ThrottlerDecorator

@ThrottlerDecorator(duration=10, limit=5)
def my_function():
    print("Function executed")

# Calling the function multiple times
for _ in range(7):
    try:
        my_function()
    except RuntimeError as e:
        print(e)  # Output: "Request throttled due to exceeding limit"
```

### ⚡ Asynchronous Function Throttling

```python
import asyncio
from your_module import ThrottlerDecorator

@ThrottlerDecorator(duration=10, limit=3)
async def my_async_function():
    print("Async function executed")

async def main():
    for _ in range(5):
        try:
            await my_async_function()
        except RuntimeError as e:
            print(e)

asyncio.run(main())
```

### 🏛️ Class-Based Throttling

```python
from your_module import ThrottlerDecorator

@ThrottlerDecorator(duration=15, limit=2)
class MyClass:
    def method(self):
        print("Method executed")

obj = MyClass()
obj.method()
obj.method()
try:
    obj.method()
except RuntimeError as e:
    print(e)  # Output: "Request throttled due to exceeding limit"
```

### 🎯 Target-Specific Throttling

You can configure throttling to apply per target by specifying the `target` parameter:

```python
from your_module import ThrottlerDecorator

@ThrottlerDecorator(duration=10, limit=5, target="user_123")
def user_specific_function():
    print("Executed for user_123")
```

Each unique `target` value maintains its own independent throttling state.

---
### Execution time
You can configure the execution time of the function, and the throttling will be tracked more precisely.
```python
from your_module import ThrottlerDecorator
@ThrottlerDecorator(duration=20, limit=10, execution_time=10)
def user_specific_function():
   ...
```
Configured in milliseconds, default is 10. 

## ⚙️ Configuration

- `duration` (**int**): ⏳ Time window in seconds.
- `limit` (**int**): 🔢 Maximum allowed executions within the duration.
- `target` (**Any, optional**): 🎯 Identifier for specific throttling targets (e.g., user ID, API key).
- `execution_time` (**int, optional**): ⏳ Execution time, configure to match your server for more precision

---

## ❗ Error Handling

If the function call exceeds the limit within the specified duration, a `RuntimeError` with the message **"Request throttled due to exceeding limit"** is raised.

---

## 👤 Author

**Vladyslav Shepilov**
