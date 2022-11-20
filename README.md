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
python guard_server.py --bind=192.168.88.105 --port=8875 --protected_uri=http://192.168.88.105:4080
```

This sets up the ServerGuard to listen for requests on its LAN interface (`192.168.88.105`) on port `8875`.
It will then send cleared, legit traffic to the protected_uri at `http://192.168.88.105:4080`

So if you request this :

```
http://192.168.88.105:8875/desktop
```

It will check the request (header, uri, user agent, body) and if legit, forward that request to 

```
http://192.168.88.105:4080/desktop
```

### Test

Now try connecting with a browser:

```
http://192.168.88.105:8875
```

You should be greated by some json showing the request.  


```
{
  "path": "/",
  "headers": {
    "host": "192.168.88.105:8875",
    "connection": "keep-alive",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip",
    "accept-language": "en-US,en;q=0.9"
  },
  "method": "GET",
  "body": "",
  "fresh": false,
  "hostname": "192.168.88.105",
  "ip": "::ffff:192.168.88.105",
  "ips": [],
  "protocol": "http",
  "query": {},
  "subdomains": [],
  "xhr": false,
  "os": {
    "hostname": "ddbcf20c36fe"
  },
  "connection": {}
}
```

Try forbidden search term...the guard wont allow the string `password` in the request

e.g.:  

```
http://192.168.88.105:8875/?q=password
```

Will respond:

```
Forbidden!
```

Now open a third windowm and try curling..the guard won't allow curl user agents.

```
curl -X GET http://192.168.88.105:8875
Forbidden!
```

## TODO:

* `POST` methods should work, but may need some tweaking
* `SSL/TLS` methods have not been tested and probably will need some work.  Recommend using [SSL Termination](https://en.wikipedia.org/wiki/TLS_termination_proxy) at the proxy and then shipping the request over http instead of trying to retain TLS throughout the entire chain.