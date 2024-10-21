import aiohttp
import asyncio
import time

CLIENT_ID = '9834b3e98bbdd73a139c2af8126da1d9'
CLIENT_SECRET = 'b89774f6af730576e7199baa05660e13'

RATE_LIMIT = 60  # Requests per minute

# Helper to manage rate limiting by tracking time between requests
class RateLimiter:
    def __init__(self, rate_limit_per_minute):
        self.rate_limit = rate_limit_per_minute
        self.requests_made = 0
        self.start_time = time.time()

    async def wait_if_needed(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if self.requests_made >= self.rate_limit:
            # If we've reached the rate limit, we need to wait for the next minute
            if elapsed_time < 60:
                wait_time = 60 - elapsed_time
                print(f"Rate limit reached. Waiting for {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)

            # Reset the counter after waiting for a minute
            self.requests_made = 0
            self.start_time = time.time()
        
        # Proceed with the request and increment the counter
        self.requests_made += 1


async def fetch_bearer_token(CLIENT_ID, CLIENT_SECRET, rate_limiter):
    url = 'https://api.snov.io/v1/oauth/access_token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            # Respect the rate limit
            await rate_limiter.wait_if_needed()
            response_json = await response.json()
            return response_json.get('access_token')


async def fetch_emails(session, domain, last_id, bearer_token, rate_limiter):
    url = f"https://api.snov.io/v2/domain-emails-with-info?domain={domain}&limit=100&type=all&last_id={last_id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    async with session.get(url, headers=headers) as response:
        await rate_limiter.wait_if_needed()
        return await response.json()


async def fetch_company_emails(domain):
    print(f'working on {domain}')
    rate_limiter = RateLimiter(RATE_LIMIT)
    
    bearer_token = await fetch_bearer_token(CLIENT_ID, CLIENT_SECRET, rate_limiter)

    if not bearer_token:
        print("Failed to retrieve bearer token.")
        return

    last_id = 0
    step = 100
    all_emails = []

    async with aiohttp.ClientSession() as session:
        while True:
            response_json = await fetch_emails(session, domain, last_id, bearer_token, rate_limiter)
            meta = response_json.get('meta', {})
            data = response_json.get('data', [])
            errors = response_json.get('errors', [])

            if meta.get('result') == 0 or errors:
                print("No more results. Exiting loop.")
                break

            emails = [entry.get('email') for entry in data if 'email' in entry]
            all_emails.extend(emails)

            print(f"Fetched {len(emails)} emails in this batch. Total so far: {len(all_emails)}")

            last_id += step

    print(f"Total emails collected: {len(all_emails)}")
    print('\n'.join(all_emails))
