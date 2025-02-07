import unittest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
from datetime import datetime, timedelta
from functools import wraps

from throttler import ThrottlerDecorator, KeywordSingleton


class TestThrottlerDecorator(unittest.TestCase):
    def setUp(self):
        """Set up two decorators with the same and different targets"""
        self.duration = 20
        self.limit = 500000
        self.target = "unique_key"

        self.throttler_1 = ThrottlerDecorator(self.duration, self.limit, target=self.target)
        self.throttler_2 = ThrottlerDecorator(self.duration, self.limit, target=self.target)

        self.throttler_diff = ThrottlerDecorator(self.duration, self.limit, target="other_key")

    def tearDown(self):
        """Clear singletons after each test"""
        KeywordSingleton.clear_instances()

    def test_singleton_behavior(self):
        """Ensure instances with the same target are the same object"""
        self.assertIs(self.throttler_1, self.throttler_2)
        self.assertIsNot(self.throttler_1, self.throttler_diff)

    def test_throttling_function(self):
        """Test that a function gets throttled after limit is reached"""
        @self.throttler_1
        def sample_function():
            return "Executed"

        for _ in range(self.limit):
            self.assertEqual(sample_function(), "Executed")

        with self.assertRaises(RuntimeError):
            sample_function()

    def test_throttling_async_function(self):
        """Test throttling an async function"""
        @self.throttler_1
        async def sample_async_function():
            return "Executed"

        async def run_test():
            results = [await sample_async_function() for _ in range(self.limit)]
            self.assertEqual(results, ["Executed"] * self.limit)

            with self.assertRaises(RuntimeError):
                await sample_async_function()

        asyncio.run(run_test())

    def test_throttling_class(self):
        """Test that all methods in a class get throttled"""
        @self.throttler_1
        class SampleClass:
            def method(self):
                return "Executed"

        instance = SampleClass()

        for _ in range(self.limit):
            self.assertEqual(instance.method(), "Executed")

        with self.assertRaises(RuntimeError):
            instance.method()

    def test_requests_after_interval_expiry(self):
        """Ensure requests are allowed again after the interval resets"""
        @self.throttler_1
        def sample_function():
            return "Executed"

        # Consume all allowed requests
        for _ in range(self.limit):
            self.assertEqual(sample_function(), "Executed")

        # This should be blocked
        with self.assertRaises(RuntimeError):
            sample_function()

        # Wait for the interval to expire
        time.sleep(self.duration + 0.1)

        # Now, it should allow requests again
        self.assertEqual(sample_function(), "Executed")

    def test_multithreaded_throttling(self):
        """Test the throttler in a multithreaded environment"""
        @self.throttler_1
        def sample_function(*args, **kwargs):
            return "Executed"

        def call_function(*args, **kwargs):
            try:
                return sample_function()
            except RuntimeError:
                return "Throttled"

        success_count = 0
        throttled_count = 0

        throtteled = 10  # amount must not be sent
        total = self.limit + throtteled

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(call_function) for _ in range(total)]
            results = [future.result() for future in futures]

        success_count = results.count("Executed")
        throttled_count = results.count("Throttled")

        self.assertEqual(success_count, self.limit)  # Ensure limit is respected
        self.assertGreater(throttled_count, 0)  # Some should be throttled

    def test_performance_comparision(self):
        max_workers = 10

        def time_decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwrags):
                start_time = datetime.now()
                func(*args, **kwrags)
                end_time = datetime.now()
                return end_time - start_time
            return wrapper

        @time_decorator
        def sample_function(*args, **kwargs):
            return "Executed"

        @time_decorator
        @self.throttler_1
        def decorated_function(*args, **kwargs):
            return "Executed"

        def call_function(func: Callable, *args):
            try:
                return func()
            except RuntimeError:
                return "Throttled"

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(call_function, sample_function) for _ in range(self.limit)
            ]
            results = [future.result() for future in futures]

        function_base_performance = sum(results, start=datetime.min) - datetime.min

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(call_function, decorated_function) for _ in range(self.limit)
            ]
            results = [future.result() for future in futures]

        function_decorated_performance = sum(results, start=datetime.min) - datetime.min

        print(
            f"Time for {len(results)} requests\n"
            f"Sample func: {function_base_performance}\n"
            f"Decorated func: {function_decorated_performance}\n"
        )


if __name__ == "__main__":
    unittest.main()
