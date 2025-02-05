import unittest
import asyncio
import time
from throttler import ThrottlerDecorator, KeywordSingleton


class TestThrottlerDecorator(unittest.TestCase):
    def setUp(self):
        """Set up two decorators with the same and different targets"""
        self.duration = 1
        self.limit = 5
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


if __name__ == "__main__":
    unittest.main()
