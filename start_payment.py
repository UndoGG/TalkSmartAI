import asyncio

from tortoise import Tortoise


async def main():
    await Tortoise.init(config_file='tortoise_config.json')
    await Tortoise.generate_schemas()

asyncio.run(main())

from engine.payment import start_rest
