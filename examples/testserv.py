import logging
import random

from aiohttp import web


def return_json_data():
    return web.json_response(
        {'status': 1, 'data': "A" * random.randint(1, 128) * 1024}
    )


class SimpleJsonView(web.View):

    async def get(self):
        return return_json_data()

    async def post(self):
        return return_json_data()


async def app_factory():
    app = web.Application()
    app.router.add_view('/', SimpleJsonView)
    return app


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s %(levelname)s] %(message)s'
    )
    web.run_app(app_factory())
