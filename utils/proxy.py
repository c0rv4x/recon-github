import asyncio
import random
from aiohttp import ClientSession, BasicAuth
from aiohttp_socks import ProxyConnector

# List of proxies in the format "ip:port:login:password"
PROXIES = [
    "130.185.126.77:6692:mbnsnnqk:dmw385lkdo89",
    "130.185.126.129:6744:mbnsnnqk:dmw385lkdo89",
    "130.185.126.166:6781:mbnsnnqk:dmw385lkdo89",
    "130.185.126.156:6771:mbnsnnqk:dmw385lkdo89",
    "130.185.126.113:6728:mbnsnnqk:dmw385lkdo89",
    "130.185.126.60:6675:mbnsnnqk:dmw385lkdo89",
    "130.185.126.209:6824:mbnsnnqk:dmw385lkdo89",
    "130.185.126.63:6678:mbnsnnqk:dmw385lkdo89",
    "130.185.126.57:6672:mbnsnnqk:dmw385lkdo89",
    "130.185.126.81:6696:mbnsnnqk:dmw385lkdo89"
]

class RandomProxySession:
    def __init__(self):
        self.proxy_url, self.proxy_auth = self.get_random_proxy()
        self.session = None

    def get_random_proxy(self):
        # Pick a random proxy from the list
        proxy = random.choice(PROXIES)
        ip, port, user, password = proxy.split(":")
        # Format the SOCKS5 proxy URL
        proxy_url = f"socks5://{user}:{password}@{ip}:{port}"
        proxy_auth = BasicAuth(login=user, password=password)
        return proxy_url, proxy_auth

    async def __aenter__(self):
        # Create a ProxyConnector with the selected SOCKS proxy
        connector = ProxyConnector.from_url(self.proxy_url)
        self.session = ClientSession(connector=connector)  # Create the session with the SOCKS proxy
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()  # Close the session when exiting the block

    def get(self, url, **kwargs):
        # Return an asynchronous context manager from the aiohttp session
        return self.session.get(url, **kwargs)

    def post(self, url, **kwargs):
        # Return an asynchronous context manager from the aiohttp session
        return self.session.post(url, **kwargs)
