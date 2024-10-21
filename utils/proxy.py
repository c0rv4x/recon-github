import asyncio
import random
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from aiohttp import ClientError  # To catch aiohttp specific errors like timeouts

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
        self.proxy_index = random.randint(0, len(PROXIES) - 1)

    def get_round_robin_proxy(self):
        proxy = PROXIES[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(PROXIES)
        
        ip, port, user, password = proxy.split(":")
        proxy_url = f"socks5://{user}:{password}@{ip}:{port}"
        return proxy_url

    async def __aenter__(self):
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def _make_request(self, method, url, **kwargs):
        max_retries = len(PROXIES)
        for _ in range(max_retries):
            proxy_url = self.get_round_robin_proxy()
            connector = ProxyConnector.from_url(proxy_url)
            timeout = ClientTimeout(total=10)
            try:
                async with ClientSession(connector=connector, timeout=timeout) as session:
                    response = await session.request(method, url, **kwargs)
                    return response  # Return response if successful
            except (asyncio.TimeoutError, ClientError) as e:
                pass

    def get(self, url, **kwargs):
        # Call _make_request with the GET method
        return self._make_request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        # Call _make_request with the POST method
        return self._make_request('POST', url, **kwargs)

