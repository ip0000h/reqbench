# reqbench

## description

Reqbench is a tool for load testing web apps.

## installation

pip install .

## usage

### arguments

usage: reqbench.py [-h] [-m {GET,DELETE,OPTIONS,HEAD,POST,PUT}]
                   [-D DATA | -F FILE] [-j] [-c CONCURRENCY] [-a AUTH]
                   [-H HEADERS] [-l LIMIT | -d DURATION] [-v]
                   URL

Reqbench is a tool for load testing web apps.

positional arguments:
  URL

optional arguments:

  -h, --help            show this help message and exit

  -m {GET,DELETE,OPTIONS,HEAD,POST,PUT}, --method {GET,DELETE,OPTIONS,HEAD,POST,PUT} HTTP method.

  -D DATA, --data DATA  Data. name:value

  -F FILE, --file FILE  Data file. File format: name1:value1 name2:value2

  -j, --json            Send json data.

  -c CONCURRENCY, --concurrency CONCURRENCY Concurrency.

  -a AUTH, --auth AUTH  Basic auth. user:password

  -H HEADERS, --headers HEADERS Custom header. name:value

  -l LIMIT, --limit LIMIT Limit of requests.

  -d DURATION, --duration DURATION Duration in milliseconds.

  -O OUTPUT, --output OUTPUT Output responses to file.

  -v, --verbose  Detailed output.
