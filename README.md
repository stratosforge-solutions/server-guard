# GuardServer - A simple Tornado WAF

## Concept

The [guard_server.py](./guard_server.py) program will start a reverse proxy that intercepts POST and GET requests sent to its own IP and PORT.
It then checks the request using WAF logic provided by the `WAFLogic` class in [WAFLogic.py](./WAFLogic.py)
Requests that pass the WAF check are forwarded to `protected_uri` which is the base URL for the protected application.

## Installation

First time:

```
python3 -m venv ve-guard
source ve-guard/bin/activate
pip install -r requirements
```

Subsequent usage:

```
source ve-guard/bin/activate
```

## Usage

```
python guard_server.py --bind=<ip_of_waf> --port=<port_of_waf> --protected_uri=<full_uri_of_protected_app>
```

Ex:

```
python guard_server.py --bind=192.168.88.101 --port=8875  --protected_uri=http://192.168.88.105:4080
```

## Testing

### Start a protected app

Open up a terminal and start the handy [http=https-echo](https://github.com/mendhak/docker-http-https-echo) server which we'll consider as our protected app.  This is a nice test app as it echos the request object (note tag 26 on pull)

```
docker run -p 4080:8080 -p 4443:8443 --rm -t mendhak/http-https-echo:26
```

This starts the protected app on the host port `4080` for `http` and `4443` for `https`

### Start GuardServer

In a second terminal on the same host, start the guard:

```
python guard_server.py --bind=192.168.88.101 --port=8875 --protected_uri=http://192.168.88.101:4080
```

Now try connecting with a browser:

```
http://192.168.88.101
```

You should be greated by some json showing the request.  

Try forbidden search term...the guard wont allow the string `password` in the request


Try curling..the guard won't allow curl user agents.