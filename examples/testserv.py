import logging
import random

from aiohttp import web
from aiohttp_basicauth_middleware import basic_auth_middleware


def return_json_data():
    return web.json_response(
        {
            'status': 1,
            'data': "A" * random.randint(16, 1024) * 1024
        }
    )


class SimpleJsonView(web.View):
    async def get(self):
        headers = self.request.headers
        logging.info(headers)
        return return_json_data()

    async def post(self):
        data = await self.request.read()
        headers = self.request.headers
        logging.info(headers)
        logging.info(data)
        return return_json_data()


class AuthJsonView(SimpleJsonView):
    pass


async def app_factory():
    app = web.Application()
    app.router.add_view('/', SimpleJsonView)
    app.router.add_view('/auth', AuthJsonView)

    app.middlewares.append(
        basic_auth_middleware(
            ('/auth',),
            {'user': 'password'},
        )
    )

    return app


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s %(levelname)s] %(message)s'
    )
    web.run_app(app_factory(), port=8000)
