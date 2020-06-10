import asyncio
import logging
import random

from aiohttp import web
from aiohttp_basicauth_middleware import basic_auth_middleware

from constants import HTTP_STATUSES


def return_json_data(status: int = None, random_data: bool = False):
    data = {
        'status': 'OK' if status is None else HTTP_STATUSES[status]
    }
    if random_data:
        data['data'] = "A" * random.randint(16, 1024) * 1024
    return web.json_response(data=data, status=status or 200)


def get_random_status():
    return random.choice(list(HTTP_STATUSES.keys()))


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


class RandomDataView(web.View):
    async def get(self):
        headers = self.request.headers
        logging.info(headers)
        return return_json_data(random_data=True)

    async def post(self):
        data = await self.request.read()
        headers = self.request.headers
        logging.info(headers)
        logging.info(data)
        return return_json_data(random_data=True)


class RandomStatusesView(web.View):
    async def get(self):
        headers = self.request.headers
        logging.info(headers)
        return return_json_data(status=get_random_status())

    async def post(self):
        data = await self.request.read()
        headers = self.request.headers
        logging.info(headers)
        logging.info(data)
        return return_json_data(status=get_random_status())


class RandomSleepView(web.View):
    async def get(self):
        headers = self.request.headers
        logging.info(headers)
        await asyncio.sleep(random.randint(2, 5))
        return return_json_data()

    async def post(self):
        data = await self.request.read()
        headers = self.request.headers
        logging.info(headers)
        logging.info(data)
        await asyncio.sleep(random.randint(2, 5))
        return return_json_data()


async def app_factory():
    app = web.Application()
    app.router.add_view('/', SimpleJsonView)
    app.router.add_view('/auth', AuthJsonView)
    app.router.add_view('/random_data', RandomDataView)
    app.router.add_view('/random_status', RandomStatusesView)
    app.router.add_view('/random_sleep', RandomSleepView)

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
