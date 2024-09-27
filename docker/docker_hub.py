import re
import json
from bs4 import BeautifulSoup

from docker.docker_image import fetch_docker_image_tags
from utils.proxy import RandomProxySession


async def process_docker_user(username):
    # Fetch Docker user info and repositories for the given Docker user
    docker_user = await fetch_docker_user_info(username)

    if docker_user and docker_user.docker_repositories:
        # For each Docker repository, fetch its tags and instructions
        for repo in docker_user.docker_repositories:
            print(f"\nFetching Docker tags and instructions for {username}/{repo}")
            docker_image = await fetch_docker_image_tags(username, repo)
            docker_image.display_tags()


async def fetch_docker_user_info(username):
    docker_user = DockerUser(username)

    async with RandomProxySession() as session:
        await docker_user.fetch_user_info_and_repos(session)
        if docker_user.docker_repositories:
            await docker_user.fetch_user_info(session)
            
    return docker_user


class DockerUser:
    def __init__(self, username):
        self.username = username
        self.full_name = None
        self.company = None
        self.user_type = None
        self.docker_repositories = []

    async def fetch_html(self, session, url):
        response = await session.get(url)
        if response.status == 200:
            return await response.text()
        elif response.status != 404:
            print(f"Weirds status code '{self.username}', {response.status}")
        return None

    async def fetch_user_info_and_repos(self, session):
        url = f"https://hub.docker.com/u/{self.username}"
        html = await self.fetch_html(session, url)

        if html:
            soup = BeautifulSoup(html, 'html.parser')
            script_tag = soup.find('script', string=re.compile(r'window.__remixContext'))

            if script_tag:
                script_content = script_tag.string
                match = re.search(r'window.__remixContext\s*=\s*(\{.*\});', script_content)

                if match:
                    json_data = match.group(1)
                    data = json.loads(json_data)

                    repositories = data["state"]["loaderData"]["routes/_layout.u.$namespace._index"]["repositories"]["results"]
                    self.docker_repositories = [repo['name'] for repo in repositories]

    async def fetch_json(self, session, url):
        response = await session.get(url)
        if response.status == 200:
            return await response.json()
        return None

    async def fetch_user_info(self, session):
        url = f"https://hub.docker.com/v2/users/{self.username}"
        data = await self.fetch_json(session, url)

        if data:
            self.full_name = data.get("full_name")
            self.company = data.get("company")
            self.user_type = data.get("type")

    def display_user_info(self):
        info = f"\nUsername: {self.username}\nFull Name: {self.full_name}\nCompany: {self.company}"
        if self.user_type and self.user_type != "User":
            info += f"\nType: {self.user_type}"
        info += f"\nDocker Repositories: {', '.join(self.docker_repositories) if self.docker_repositories else 'None'}"
        print(info)
