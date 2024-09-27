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
        self.session = None

    def get_random_proxy(self):
        # Pick a random proxy from the list
        proxy = random.choice(PROXIES)
        ip, port, user, password = proxy.split(":")
        # Format the SOCKS5 proxy URL
        proxy_url = f"socks5://{user}:{password}@{ip}:{port}"
        return proxy_url

    async def __aenter__(self):
        # Initialize the session on enter
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()  # Close the session when exiting the block

    async def _make_request(self, method, url, **kwargs):
        # Select a random proxy for each request
        proxy_url = self.get_random_proxy()
        # Create a ProxyConnector with the selected SOCKS proxy
        connector = ProxyConnector.from_url(proxy_url)
        async with ClientSession(connector=connector) as session:
            return await session.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        # Call _make_request with the GET method
        return self._make_request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        # Call _make_request with the POST method
        return self._make_request('POST', url, **kwargs)
