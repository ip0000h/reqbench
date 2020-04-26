import logging
import random
import string
from os import getenv

from aiohttp import web

LOG_FORMAT = '[%(asctime)s %(levelname)s] %(message)s'
LOG_LEVEL = logging._nameToLevel[getenv('LOG_LEVEL', 'INFO').upper()]


def unique_strings(k: int, ntokens: int,
                   pool: str = string.ascii_letters) -> list:
    """Generate a set of unique string tokens.

    k: Length of each token
    ntokens: Number of tokens
    pool: Iterable of characters to choose from
    """

    seen = set()

    # An optimization for tightly-bound loops:
    # Bind these methods outside of a loop
    join = ''.join
    add = seen.add

    while len(seen) < ntokens:
        token = join(random.choices(pool, k=k))
        add(token)
    return list(seen)


class SimpleJsonView(web.View):

    async def get(self):
        return web.json_response({'status': 1, 'data': unique_strings(100, 4, string.printable)})

    async def post(self):
        return web.json_response({'status': 1, 'data': unique_strings(100, 4, string.printable)})


async def app_factory():
    app = web.Application()
    app.router.add_view('/', SimpleJsonView)
    return app


if __name__ == '__main__':
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )
    web.run_app(app_factory())
