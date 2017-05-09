import asyncio
import concurrent.futures

from uvloop import _testbase as tb


def fib(n):
    if n < 2:
        return 1
    return fib(n - 2) + fib(n - 1)


class _TestExecutors:

    def run_pool_test(self, pool_factory):
        async def run():
            pool = pool_factory()
            with pool:
                coros = []
                for i in range(0, 10):
                    coros.append(self.loop.run_in_executor(pool, fib, i))
                res = await asyncio.gather(*coros, loop=self.loop)
            self.assertEqual(res, fib10)
            await asyncio.sleep(0.01, loop=self.loop)

        fib10 = [fib(i) for i in range(10)]
        self.loop.run_until_complete(run())

    def test_executors_process_pool_01(self):
        self.run_pool_test(concurrent.futures.ProcessPoolExecutor)

    def test_executors_process_pool_02(self):
        self.run_pool_test(concurrent.futures.ThreadPoolExecutor)


class TestUVExecutors(_TestExecutors, tb.UVTestCase):
    pass


class TestAIOExecutors(_TestExecutors, tb.AIOTestCase):
    pass