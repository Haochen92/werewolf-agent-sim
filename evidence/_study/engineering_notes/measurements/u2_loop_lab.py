"""Four small experiments on the event loop. Run one at a time:

    poetry run python loop_lab.py 1     (then 2, 3, 4)

Before each run, write down what you expect: how long it takes, and whether the
heartbeat keeps ticking. The heartbeat is a task that prints every 0.25 s, so a
gap in the ticks is the loop being stuck.
"""
import asyncio
import sys
import time

START = time.perf_counter()


def log(text):
    print(f"{time.perf_counter() - START:5.2f}s  {text}")


async def heartbeat():
    while True:
        log("  tick")
        await asyncio.sleep(0.25)


def charge_blocking(buyer):
    """An ordinary function: holds its thread for one second."""
    time.sleep(1)
    return f"receipt for {buyer}"


async def charge_async(buyer):
    """An async function: gives the loop back for one second."""
    await asyncio.sleep(1)
    return f"receipt for {buyer}"


async def experiment_1():
    """Three buyers, async charge. How long in total? Do the ticks continue?"""
    receipts = await asyncio.gather(*(charge_async(b) for b in "ABC"))
    log(f"done: {receipts}")


async def experiment_2():
    """Three buyers, blocking charge called straight from async code."""
    async def checkout(buyer):
        return charge_blocking(buyer)
    receipts = await asyncio.gather(*(checkout(b) for b in "ABC"))
    log(f"done: {receipts}")


async def experiment_3():
    """Three buyers, blocking charge handed to worker threads."""
    receipts = await asyncio.gather(*(asyncio.to_thread(charge_blocking, b) for b in "ABC"))
    log(f"done: {receipts}")


async def experiment_4():
    """A future: one task waits for an answer that another task supplies later."""
    answer_box = asyncio.get_running_loop().create_future()

    async def game():
        log("game: waiting for the human")
        answer = await answer_box
        log(f"game: resumed with {answer!r}")

    async def human_request():
        await asyncio.sleep(1.5)
        log("route: human answered, filling the future")
        answer_box.set_result("vote seat 3")

    await asyncio.gather(game(), human_request())


async def main(number):
    ticker = asyncio.create_task(heartbeat())
    await asyncio.sleep(0.3)
    log(f"--- experiment {number} starts")
    await globals()[f"experiment_{number}"]()
    await asyncio.sleep(0.3)
    ticker.cancel()


asyncio.run(main(sys.argv[1]))
