import unittest
import time
from throttler import IntervalTrackerMixin
from datetime import timedelta


class TestIntervalTrackerMixin(unittest.TestCase):
    def setUp(self):
        self.duration = 2  # 2-second interval
        self.limit = 10  # Maximum 10 requests per interval
        self._execution_time = 10

        self.tracker = IntervalTrackerMixin(
            duration=self.duration, limit=self.limit,
            execution_time=self._execution_time
        )

    def test_initialize(self):
        """Test proper initialization"""
        interval = self.tracker.interval
        self.assertEqual(interval.duration, timedelta(seconds=self.duration))
        self.assertEqual(interval.limit, self.limit)
        self.assertEqual(
            self.tracker._execution_time, timedelta(milliseconds=self._execution_time)
        )

    def test_make_request(self):
        """Test returning False after limit is reached"""
        for _ in range(self.limit):
            self.assertTrue(self.tracker.make_request())
        self.assertFalse(self.tracker.make_request())

    def test_requests_after_interval_expiry(self):
        """Ensure requests are allowed again after the interval resets"""
        for _ in range(self.limit):
            self.assertTrue(self.tracker.make_request())

        self.assertFalse(self.tracker.make_request())

        # Wait for interval expiry
        time.sleep(self.duration + 0.1)

        # Requests should be allowed again
        self.assertTrue(self.tracker.make_request())

    def test_excess_requests_are_rejected(self):
        """Ensure excess requests beyond the limit are permanently rejected, not deferred"""
        for _ in range(self.limit):
            self.assertTrue(self.tracker.make_request())

        # Next requests should be immediately rejected
        for _ in range(5):  # Extra 5 requests
            self.assertFalse(self.tracker.make_request())

        # Wait for interval expiry
        time.sleep(self.duration + 0.1)

        # New requests should be allowed again, but previously rejected ones are lost
        self.assertTrue(self.tracker.make_request())

    def test_timer_reset_and_counter_drop(self):
        """Ensure timer resets and counter drops to 0 after interval expiration"""
        for _ in range(self.limit):
            self.assertTrue(self.tracker.make_request())

        self.assertFalse(self.tracker.make_request())

        # Capture old interval start before waiting
        previous_start = self.tracker.interval_start

        # Wait for interval expiry
        time.sleep(self.duration + 0.1)

        # Make the first request after interval reset
        self.assertTrue(self.tracker.make_request())

        # Ensure the interval has restarted (interval_start should be updated)
        self.assertGreater(self.tracker.interval_start, previous_start)

        # Ensure the counter has reset to 1 (because we just made one request)
        self.assertEqual(self.tracker.actions_counter, 1)


if __name__ == "__main__":
    unittest.main()
