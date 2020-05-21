#!/usr/bin/env python
import asyncio
import argparse
import logging
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

from aiohttp import (BasicAuth,
                     ClientSession,
                     ClientConnectionError,
                     ClientResponseError,
                     TCPConnector)
from tqdm import tqdm


_URL_METHODS = ['GET', 'DELETE', 'OPTIONS', 'HEAD']
_DATA_METHODS = ['POST', 'PUT']
_LOGGER_FORMAT = '%(asctime)s %(message)s'

logging.basicConfig(format=_LOGGER_FORMAT, datefmt='[%H:%M:%S]')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class UserException(Exception):

    def __init__(self, msg, params=None):
        self.message = msg
        self.params = params
        super(UserException, self).__init__(self)

    def __str__(self):
        return f'{self.message}' \
               + (f', params: {self.params}' if self.params else '')


class ReqBench(object):

    def __init__(
            self,
            url: str,
            method: str = 'GET',
            data: dict = None,
            json_data: bool = False,
            concurrency: int = 1,
            auth: str = None,
            headers: dict = None,
            limit: int = None,
            duration: int = None,
            file_name: str = None):
        self.url = url
        self.method = method
        self.limit = limit
        self.duration = duration
        self.data = None
        self.json_data = None
        if method in _URL_METHODS:
            if data:
                self.url += '?' + urlencode(data)
        elif method in _DATA_METHODS:
            if json_data:
                self.json_data = data
            else:
                self.data = data
        if file_name:
            self.file_obj = open(file_name, 'r')
        else:
            self.file_obj = None
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
        # self.tqdm = tqdm(
        #     total=limit or duration
        # )

    @property
    def running_time(self) -> timedelta:
        return datetime.now() - self.time_start

    @property
    def avg_data_received(self) -> int:
        return int(self.data_received / self.request_sent)

    async def _request(self, session: ClientSession):
        start = datetime.now()
        data = {
            'method': self.method,
            'url': self.url
        }
        if self.data:
            data['data'] = data
        elif self.json_data:
            data['json_data'] = data
        try:
            async with session.request(**data) as response:
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

    async def run(self):
        connector = TCPConnector(limit=None)
        async with self.semaphore:
            async with ClientSession(
                    auth=self.auth,
                    headers=self.headers,
                    connector=connector
                ) as session:
                while (not self.limit or self.request_sent < self.limit) and \
                      (not self.duration or self.running_time.seconds < self.duration):
                    tasks = [self._request(session) for _ in range(self.concurrency)]
                    await asyncio.gather(*tasks)

    def show_interrupt_message(self):
        logger.info('Tasks was interrupted by user')

    def show_final_message(self):
        logger.info('Requests sent: %s success: %s errors: %s',
                    self.request_sent, self.success, self.errors)
        logger.info('Received data: %s bytes.', self.data_received)
        logger.info('Request data length min: %s bytes max: %s bytes avg: %s bytes',
                    self.min_data_received, self.max_data_received, self.avg_data_received)
        logger.info('Request duration time min: %s max: %s',
                    self.min_time_request, self.max_time_request)
        logger.info('Finished in %s', self.running_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reqbench is a tool for load testing web apps.')
    parser.add_argument('url', metavar='URL', type=str)

    parser.add_argument('-m', '--method', type=str,
                        default='GET', choices=_URL_METHODS + _DATA_METHODS, help='HTTP method.')

    group_data = parser.add_mutually_exclusive_group()
    group_data.add_argument('-D', '--data', type=str, action='append', help='Data. name:value')
    group_data.add_argument('-F', '--file', type=str,
                            help='Data file. File format: name1:value1 name2:value2')

    parser.add_argument('-j', '--json', action='store_true', default=False, help='Send json data.')

    parser.add_argument('-c', '--concurrency', type=int, default=1, help='Concurrency.')

    parser.add_argument('-a', '--auth', type=str, help='Basic auth. user:password')

    parser.add_argument('-H', '--headers', type=str, action='append',
                        help='Custom header. name:value',)

    group_limit = parser.add_mutually_exclusive_group()
    group_limit.add_argument('-l', '--limit', type=int, help='Limit of requests.')
    group_limit.add_argument('-d', '--duration', type=int, help='Duration in seconds.')

    parser.add_argument('-v', '--verbose', action='store_true', help='Detailed output.')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()

    try:
        if args.file:
            if not os.path.exists(args.file):
                raise UserException('Data file is not found')
        reqbench = ReqBench(
            args.url,
            method=args.method,
            data=dict((d.split(':') for d in args.data)) if args.data else None,
            concurrency=args.concurrency,
            auth=args.auth,
            headers=dict((h.split(':') for h in args.headers)) if args.headers else None,
            duration=args.duration,
            limit=args.limit
        )
        task = loop.create_task(reqbench.run())
        loop.run_until_complete(task)
    except UserException as e:
        reqbench.show_interrupt_message()
        task.cancel()
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
