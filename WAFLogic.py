#
#  WAFLogic is an interface where you can implement your WAF rules
#  (or send requests to other code in your project)
#
import logging
import os
import sys
import socket
import asyncio

logger = logging.getLogger('tornado_proxy')


class WAFLogic():
    def __init__(self):
        logger.info("WAFLogic ready")

    #
    # check_request checks a request to the WAF for legitimacy
    #
    # It should return True for any legitimate request, false for illegitimate or suspicous requests
    #
    # You can add custom logging here to pull intelligence about the attacker
    #
    def check_request(self, request):
        logger.info("WAF checking request: {}".format(request))
        #Put all your request checks here. Examples.        
        if "password" in request.uri:
            logger.warning("rejected request due to the word password in the uri.  Someone is trying a traversal or injection attack")
            return False

        if "curl" in request.headers["User-Agent"]:
            logger.warning("rejected request due to curl user agent")
            return False

        return True