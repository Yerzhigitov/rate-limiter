import unittest

from ratelimit import RateLimitExceeded, SlidingWindow, TokenBucket, rate_limited


class FakeClock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t


class RateLimitTest(unittest.TestCase):
    def test_token_bucket_refill(self):
        clock = FakeClock()
        tb = TokenBucket(3, 1.0, clock)
        self.assertEqual([tb.allow("u") for _ in range(4)], [True, True, True, False])
        clock.t = 2.0
        self.assertTrue(tb.allow("u"))
        self.assertTrue(tb.allow("u"))
        self.assertFalse(tb.allow("u"))

    def test_clients_isolated(self):
        sw = SlidingWindow(1, 10, FakeClock())
        self.assertTrue(sw.allow("a"))
        self.assertTrue(sw.allow("b"))
        self.assertFalse(sw.allow("a"))

    def test_window_slides(self):
        clock = FakeClock()
        sw = SlidingWindow(2, 1.0, clock)
        sw.allow("u"); sw.allow("u")
        self.assertFalse(sw.allow("u"))
        clock.t = 1.0
        self.assertTrue(sw.allow("u"))

    def test_decorator(self):
        @rate_limited(SlidingWindow(1, 60, FakeClock()), key_func=lambda user: user)
        def pay(user): return "ok"
        self.assertEqual(pay("ali"), "ok")
        with self.assertRaises(RateLimitExceeded):
            pay("ali")


if __name__ == "__main__":
    unittest.main()
