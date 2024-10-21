import asyncio
from termcolor import colored  # Import for colored text
from pygments import highlight
from pygments.lexers import DockerLexer
from pygments.formatters import TerminalFormatter

from utils.proxy import RandomProxySession


# Exportable function to fetch tags and their instructions for a given image
async def fetch_docker_image_tags(username, image_name):
    docker_image = DockerImage(username, image_name)
    await docker_image.fetch_all_tags()

    return docker_image


class DockerTag:
    def __init__(self, name, last_updater_username):
        self.name = name
        self.last_updater_username = last_updater_username
        self.instructions = []

    def __repr__(self):
        # Use Pygments to highlight the instructions
        formatted_instructions = highlight('\n'.join(self.instructions), DockerLexer(), TerminalFormatter())
        return f"{colored(self.name, 'green')}\n{formatted_instructions}"

    async def fetch_tag_instructions(self, session, username, image_name, tag_name):
        url = f"https://hub.docker.com/v2/repositories/{username}/{image_name}/tags/{tag_name}/images"
        response = await session.get(url)
        if response.status == 200:
            images_data = await response.json()
            if images_data:
                for image_data in images_data:
                    for layer in image_data.get('layers', []):
                        if 'instruction' in layer:
                            self.instructions.append(layer['instruction'].lstrip())
        else:
            print(f"Failed to fetch instructions for tag {tag_name} (status code: {response.status})")


class DockerImage:
    def __init__(self, username, image_name):
        self.username = username.lower()
        self.image_name = image_name
        self.tags = []
        self.seen_instuctions = set()

    async def fetch_tags(self, session, page_url):
        response = await session.get(page_url)
        if response.status == 200:
            return await response.json()
        else:
            return None

    async def fetch_tag_instructions_concurrent(self, tag_info, session, semaphore):
        async with semaphore:
            tag = DockerTag(
                name=tag_info['name'],
                last_updater_username=tag_info['last_updater_username']
            )
            await tag.fetch_tag_instructions(session, self.username, self.image_name, tag.name)
            concatted_instructions = '\n'.join(tag.instructions)
            if concatted_instructions not in self.seen_instuctions:
                self.seen_instuctions.add(concatted_instructions)
                self.tags.append(tag)

    async def fetch_all_tags(self):
        base_url = f"https://hub.docker.com/v2/repositories/{self.username}/{self.image_name}/tags"
        params = "?page_size=25&page=1&ordering=last_updated"
        page_url = base_url + params

        async with RandomProxySession() as session:
            semaphore = asyncio.Semaphore(5)  # Limit concurrency to 5 tasks at a time
            while page_url:
                data = await self.fetch_tags(session, page_url)
                if not data:
                    print(f"Failed to fetch data for {self.username}/{self.image_name}")
                    break

                tasks = []
                # Parse the tags from the response and create tasks for each tag
                for tag_info in data['results']:
                    task = self.fetch_tag_instructions_concurrent(tag_info, session, semaphore)
                    tasks.append(task)

                # Run the tasks in parallel, with the semaphore controlling concurrency
                await asyncio.gather(*tasks)

                # Move to the next page if available
                page_url = data.get('next')

    def display_tags(self):
        for tag in self.tags:
            print(f"[{colored(self.username, 'yellow')}/{self.image_name}] {tag}")
