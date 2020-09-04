#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 Harish Rajagopal
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
​
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
​
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Authentication script for FortiNet."""
import logging
import re
from argparse import ArgumentParser
from getpass import getpass
from http.client import RemoteDisconnected
from signal import SIGTERM, signal
from socket import timeout
from time import sleep
from urllib.error import URLError
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen
​
FORMAT = "%(asctime)s %(levelname)s %(message)s"  # format for logging info
​
​
class Authenticator:
    """Class for authenticating to FortiNet."""
​
    # Using HTTP as redirection to gateway raises SSL errors with HTTPS
    TEST_URL = "http://www.imdb.com"
​
    # All times are in seconds
    TIMEOUT = 5  # timeout for GET/POST requests
    SLEEP = {
        "retry": 20,  # pause before retrying login/keep-alive if they fail
        "keepAlive": 60,  # pause b/w two pings of the keep-alive URL
    }
​
    # Errors indicating that the request failed
    HTTP_ERRORS = (timeout, URLError, RemoteDisconnected)
​
    def __init__(self, username, password, logger=None):
        """Store user details.
​
        Args:
            username (str): The FortiNet username
            password (str): The FortiNet password
            logger (`logging.Logger`): The logger to be used
​
        """
        self.username = username
        self.password = password
​
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
​
        # This will later store the keep-alive and logout URLs
        self.urls = {}
​
    def __del__(self):
        """Automatically logout on exit."""
        self.logout()
​
    def authenticate(self):
        """Try to authenticate.
​
        Raises:
            RuntimeError: If the authentication fails
​
        """
        self.logger.info("Starting authentication...")
​
        with urlopen(self.TEST_URL, timeout=self.TIMEOUT) as resp:
            redir_url = resp.geturl()  # URL after redirection to FortiNet
​
        parsed = urlparse(redir_url)
        if parsed.path != "/fgtauth":
            # We weren't redirected to a FortiNet authentication page
            self.logger.info("Seems already authenticated")
            return
​
        # Redirected to a FortiNet authentication page
        params = {
            "username": self.username,
            "password": self.password,
            "magic": parsed.query,
        }
        data = urlencode(params).encode("utf8")  # POST data must be bytes
​
        # "Content-Type" headers are automatically added by Python
        with urlopen(redir_url, data=data, timeout=self.TIMEOUT) as resp:
            content = resp.read().decode("utf8")  # convert bytes to str
​
        # List of all URLs in the HTML response that are of the form:
        # href="http://url.to/some/page.html"
        all_urls = re.findall(r'href="([^"]+)"', content)
​
        if len(all_urls) == 0:
            # This mostly means that the username and/or password wrong
            raise RuntimeError("Failed to authenticate")
​
        # If this assertion fails, then it means that FortiNet has
        # changed its HTML template for authentication pages. This
        # implies that this code has to be changed as well.
        assert len(all_urls) == 3, "FortiNet HTML template has changed"
​
        self.logger.info("Successfully authenticated")
        self.urls["keepAlive"] = all_urls[2]
        self.urls["logout"] = all_urls[1]
​
    def keep_alive(self):
        """Ping the keep-alive URL.
​
        Args:
            url (str): The keep-alive URL from an existing login
​
        Returns:
            bool: True if keep-alive succeeds
​
        """
        assert "keepAlive" in self.urls, "No keep-alive URL is registered"
        self.logger.info("Pinging keep-alive")
​
        try:
            with urlopen(self.urls["keepAlive"], timeout=self.TIMEOUT) as resp:
                resp_url = resp.geturl()
            # Ensure that keep-alive succeeded
            assert urlparse(resp_url).path == "/keepalive"
​
        except self.HTTP_ERRORS + (AssertionError,):
            self.logger.warning("Keep-alive failed")
            return False
​
        else:
            return True
​
    def logout(self):
        """Logout from FortiNet."""
        assert "logout" in self.urls, "No logout URL is registered"
        self.logger.info("Logging out")
        try:
            urlopen(self.urls["logout"], timeout=self.TIMEOUT)
        except self.HTTP_ERRORS:
            self.logger.warning("Failed to log out")
​
    def open_session(self):
        """Open an authentication session and keep it open until closed.
​
        This session can be closed by deleting an instance of this object. This
        can be done by sending a KeyboardInterrupt, which causes Python to
        delete the instance. For handling SIGTERM, `exit` can be registered as
        a handler.
        """
        # This while loop ensures that in case of errors, we keep trying. If
        # the login succeeds, then the execution breaks out of this loop. Also,
        # if the user is already logged in, we keep pinging, in case this login
        # times out.
        while True:
            try:
                self.authenticate()
​
            # NOTE: A RuntimeError indicates that username and password are
            # wrong. We want to deliberately CRASH if that happens; hence we're
            # not handling it.
            except self.HTTP_ERRORS:
                self.logger.warning(
                    "Encountered error when logging in; "
                    "retrying in {} seconds".format(self.SLEEP["retry"])
                )
​
            if self.urls:  # this will not be empty if authentication succeeded
                break  # login succeeded, so break out of the loop
            else:
                sleep(self.SLEEP["retry"])
​
        # Wait for some time before pinging keep-alive
        sleep(self.SLEEP["keepAlive"])
​
        # Loop forever and keep the login alive
        while True:
            if self.keep_alive():
                sleep(self.SLEEP["keepAlive"])  # keep-alive succeeded
            else:
                sleep(self.SLEEP["retry"])  # keep-alive failed
​
​
def main(args):
    """Run the main program.
​
    Arguments:
        args (`argparse.Namespace`): The object containing the commandline
            arguments
​
    """
    username, password = args.username, args.password
    if username is None:
        username = input("Enter username: ")
    if password is None:
        password = getpass("Enter password: ")
​
    if args.quiet:  # log everything with custom format
        logging.basicConfig(format=FORMAT)
    else:  # log everything with level >= INFO and with custom format
        logging.basicConfig(format=FORMAT, level=logging.INFO)
​
    # Gracefully exit with a logout on SIGTERM
    signal(SIGTERM, lambda _, __: exit())
​
    auth = Authenticator(username, password)
    auth.open_session()
​
​
if __name__ == "__main__":
    parser = ArgumentParser(description="Authentication script for FortiNet")
    parser.add_argument("-u", "--username", type=str, help="FortiNet username")
    parser.add_argument("-p", "--password", type=str, help="FortiNet password")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="disable verbose output"
    )
    main(parser.parse_args())
