#!/usr/bin/env python
import asyncio
import argparse
from datetime import datetime, timedelta
from urllib.parse import urlencode

from aiohttp import (BasicAuth,
                     ClientSession,
                     ClientConnectionError,
                     ClientResponseError)


_URL_METHODS = ['GET', 'DELETE', 'OPTIONS', 'HEAD']
_DATA_METHODS = ['POST', 'PUT']


class GracefulExit(SystemExit):
    code = 1


class ReqBench(object):

    def __init__(
            self,
            url: str,
            method: str = 'GET',
            data: dict = None,
            json_data: bool = False,
            concurrency: int = 1,
            auth: str = None,
            headers: dict = None):
        self.url = url
        self.method = method
        self.data = None
        self.json_data = None
        if method in _URL_METHODS:
            self.url += '?' + urlencode(data)
        elif method in _DATA_METHODS:
            if json_data:
                self.json_data = data
            else:
                self.data = data
        self.concurrency = concurrency
        self.time_start = datetime.now()
        self.min_time_request = None
        self.max_time_request = None
        self.request_sent = 0
        self.data_received = 0
        self.min_data_received = None
        self.max_data_received = None
        self.success = 0
        self.errors = 0
        self.auth = BasicAuth(*auth.split(':')) if auth else None
        self.headers = headers
        self.semaphore = asyncio.Semaphore(concurrency + 1)

    @property
    def running_time(self) -> timedelta:
        return datetime.now() - self.time_start

    async def _request(self):
        start = datetime.now()
        data = {
            'method': self.method,
            'url': self.url
        }
        if self.data:
            data['data'] = data
        elif self.json_data:
            data['json_data'] = data
        async with ClientSession(
                auth=self.auth,
                headers=self.headers
                ) as session:
            async with session.request(**data) as response:
                try:
                    resp_data = await response.read()
                    data_received = len(resp_data)
                    self.data_received += data_received
                    if not self.min_data_received or self.min_data_received > data_received:
                        self.min_data_received = data_received
                    if not self.max_data_received or self.max_data_received < data_received:
                        self.max_data_received = data_received
                except (ClientConnectionError, ClientResponseError):
                    self.errors += 1
                else:
                    self.success += 1
                finally:
                    self.request_sent += 1
                    duration = datetime.now() - start
                    if not self.min_time_request or self.min_time_request > duration:
                        self.min_time_request = duration
                    if not self.max_time_request or self.max_time_request < duration:
                        self.max_time_request = duration

    async def run_request_limit(self, limit):
        async with self.semaphore:
            while self.request_sent < limit:
                tasks = [self._request() for _ in range(self.concurrency)]
                await asyncio.gather(*tasks)

    async def run_duration_time(self, duration_time):
        async with self.semaphore:
            while self.running_time.seconds < duration_time:
                tasks = [self._request() for _ in range(self.concurrency)]
                await asyncio.gather(*tasks)

    def show_interrupt_message(self):
        print('Tasks was interrupted by user')

    def show_final_message(self):
        print(f'Requests sent: {self.request_sent} success: {self.success} errors: {self.errors}')
        print(f'Received data: {self.data_received} bytes.')
        print(f'Request data length min: {self.min_data_received} bytes'
              f' max: {self.max_data_received} bytes'
              f' avg: {int(self.data_received / self.request_sent)} bytes')
        print(f'Request duration time min: {str(self.min_time_request)}'
              f' max: {self.max_time_request}')
        print(f'Finished in {str(self.running_time)}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reqbench is a tool for load testing web apps.')
    parser.add_argument('url', metavar='URL', type=str)

    parser.add_argument('-m', '--method', type=str,
                        default='GET', choices=_URL_METHODS + _DATA_METHODS, help='HTTP method.')

    parser.add_argument('-D', '--data', type=str, action='append', help='Data. name:value')
    parser.add_argument('-j', '--json', action='store_true', default=False, help='Send json data.')

    parser.add_argument('-c', '--concurrency', type=int, default=1, help='Concurrency.')

    parser.add_argument('-a', '--auth', type=str, help='Basic auth. user:password')

    parser.add_argument('-H', '--headers', type=str, action='append',
                        help='Custom header. name:value',)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--limit', type=int, help='Limit of requests.')
    group.add_argument('-d', '--duration', type=int, help='Duration in seconds.')

    args = parser.parse_args()
    loop = asyncio.get_event_loop()

    try:
        reqbench = ReqBench(
            args.url,
            method=args.method,
            data=dict((d.split(':') for d in args.data)) if args.data else None,
            concurrency=args.concurrency,
            auth=args.auth,
            headers=dict((h.split(':') for h in args.headers)) if args.headers else None,
        )
        if args.limit:
            task = loop.create_task(reqbench.run_request_limit(args.limit))
        else:
            task = loop.create_task(reqbench.run_duration_time(args.duration))
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        reqbench.show_interrupt_message()
        task.cancel()
    finally:
        try:
            pending_tasks = [
                task for task in asyncio.Task.all_tasks() if not task.done()
            ]
            loop.run_until_complete(asyncio.gather(*pending_tasks))
        except asyncio.CancelledError:
            pass
        reqbench.show_final_message()
        loop.close()
