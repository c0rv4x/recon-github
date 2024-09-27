import aiohttp


CLIENT_ID = '9834b3e98bbdd73a139c2af8126da1d9'
CLIENT_SECRET = 'b89774f6af730576e7199baa05660e13'


async def fetch_bearer_token(CLIENT_ID, CLIENT_SECRET):
    url = 'https://api.snov.io/v1/oauth/access_token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            response_json = await response.json()
            return response_json.get('access_token')


async def fetch_emails(session, domain, last_id, bearer_token):
    url = f"https://api.snov.io/v2/domain-emails-with-info?domain={domain}&limit=100&type=all&last_id={last_id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    async with session.get(url, headers=headers) as response:
        return await response.json()


async def fetch_company_emails(domain):
    # Fetch bearer token
    bearer_token = await fetch_bearer_token(CLIENT_ID, CLIENT_SECRET)

    if not bearer_token:
        print("Failed to retrieve bearer token.")
        return

    last_id = 0
    step = 100
    all_emails = []

    async with aiohttp.ClientSession() as session:
        while True:
            response_json = await fetch_emails(session, domain, last_id, bearer_token)
            meta = response_json.get('meta', {})
            data = response_json.get('data', [])

            # Exit loop if no more results
            if meta.get('result') == 0:
                print("No more results. Exiting loop.")
                break

            # Extract and collect emails from 'data'
            emails = [entry.get('email') for entry in data if 'email' in entry]
            all_emails.extend(emails)

            # Move to the next batch
            last_id += step

    # Print the total list of emails and its size
    print(f"Total emails collected: {len(all_emails)}")
    print('\n'.join(all_emails))
