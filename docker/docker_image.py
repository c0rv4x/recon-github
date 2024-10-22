import asyncio
import json
from termcolor import colored  # Import for colored text
from pygments import highlight
from pygments.lexers import DockerLexer
from pygments.formatters import TerminalFormatter

from utils.proxy import RandomProxySession


async def process_docker_image(username, image_name):
    docker_image = DockerImage(username, image_name)
    await docker_image.process_tags()

    return docker_image


class DockerImage:
    def __init__(self, username, image_name):
        self.username = username.lower()
        self.image_name = image_name
        self.tags = []
        self.seen_instructions = set()

    async def process_tags(self):
        base_url = f"https://hub.docker.com/v2/repositories/{self.username}/{self.image_name}/tags"
        params = "?page_size=25&page=1&ordering=last_updated"
        page_url = base_url + params

        semaphore = asyncio.Semaphore(10)  # Limit concurrency to 5 tasks at a time

        while page_url:
            async with RandomProxySession() as session:
                data = await self.fetch_tags(session, page_url)
                if not data:
                    print(f"Failed to fetch data for {self.username}/{self.image_name}")
                    break

            tasks = []
            # Parse the tags from the response and create tasks for each tag
            for tag_info in data['results']:
                task = self.process_tag_concurrent(tag_info, semaphore)
                tasks.append(task)

            # Wait for the batch of tasks to complete
            await asyncio.gather(*tasks)

            for tag in self.tags:
                async with RandomProxySession() as session:
                    await tag.process(session)

            page_url = data.get('next')

    async def fetch_tags(self, session, page_url):
        response = await session.get(page_url)
        if response.status == 200:
            return await response.json()
        else:
            return None

    async def process_tag_concurrent(self, tag_info, semaphore):
        async with semaphore:
            # Create a new session within the semaphore block for each task
            async with RandomProxySession() as session:
                tag = DockerTag(
                    username=self.username,
                    image_name=self.image_name,
                    tag_name=tag_info['name'],
                    last_updater_username=tag_info['last_updater_username']
                )
                await tag.process(session)
                concatted_instructions = '\n'.join(tag.instructions)
                if concatted_instructions not in self.seen_instructions:
                    self.seen_instructions.add(concatted_instructions)
                self.tags.append(tag)

    def display_tag_instructions(self):
        for tag in self.tags:
            print(f"[{colored(self.username, 'yellow')}/{self.image_name}] {tag}")


class DockerTag:
    def __init__(self, username, image_name, tag_name, last_updater_username):
        self.username = username
        self.image_name = image_name
        self.tag_name = tag_name
        self.last_updater_username = last_updater_username
        self.instructions = []

        self.unique_secrets_in_files = set()
        self.blacklisted_file_parts = ['md5sums', 'test', 'example', 'python2.7', 'python3.8', 'Tiny.pm']

    def __repr__(self):
        formatted_instructions = highlight('\n'.join(self.instructions), DockerLexer(), TerminalFormatter())
        return f"{colored(self.tag_name, 'green')}\n{formatted_instructions}"

    async def process(self, session):
        await self.run_trufflehog_scan()

    async def output_layers(self, session):
        url = f"https://hub.docker.com/v2/repositories/{self.username}/{self.image_name}/tags/{self.tag_name}/images"
        response = await session.get(url)
        if response.status == 200:
            images_data = await response.json()
            if images_data:
                for image_data in images_data:
                    for layer in image_data.get('layers', []):
                        if 'instruction' in layer:
                            self.instructions.append(layer['instruction'].lstrip())
        else:
            print(f"Failed to fetch instructions for tag {self.tag_name} (status code: {response.status})")

    async def run_trufflehog_scan(self):
        try:
            # Use asyncio to run the trufflehog command asynchronously
            process = await asyncio.create_subprocess_exec(
                "trufflehog", "docker", "--image", f"{self.username}/{self.image_name}:{self.tag_name}", "--json", "--no-verification",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                output_lines = stdout.decode().splitlines()

                # Parse TruffleHog's JSON output
                for line in output_lines:
                    json_data = json.loads(line)

                    # Extract Docker image, tag, file, and secret
                    docker_info = json_data.get("SourceMetadata", {}).get("Data", {}).get("Docker", {})
                    docker_image = docker_info.get("image", "unknown_image")
                    docker_tag = docker_info.get("tag", "latest")
                    docker_file = docker_info.get("file", "unknown_file")
                    secret = json_data.get("Raw", "unknown_secret")

                    should_skip = False
                    for pattern in self.blacklisted_file_parts:
                        if pattern in docker_file:
                            should_skip = True
                            break

                    if should_skip:
                        continue
                    
                    # Format the output
                    unique_entry = (
                        f"\nDocker Image: {docker_image}:{docker_tag}\n"
                        f"File: {docker_file}\n"
                        f"Secret: {secret}"
                    )
                    # Only print the result if it is unique for this repo
                    if unique_entry not in self.unique_secrets_in_files:
                        self.unique_secrets_in_files.add(unique_entry)
                        print(unique_entry)

            else:
                print(f"Error scanning {self.username}/{self.image_name}:{self.tag_name}: {stderr.decode()}")

        except Exception as e:
            print(f"Exception occurred during scan for {self.username}/{self.image_name}:{self.tag_name}: {str(e)}")

