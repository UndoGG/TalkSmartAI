import asyncio


async def one():
    return 123


async def two():
    return 456


async def main():
    print((await asyncio.gather(one(), two())))

asyncio.run(main())