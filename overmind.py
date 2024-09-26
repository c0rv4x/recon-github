import sys
import asyncio

from github_users import org_nicknames
from docker_hub import fetch_docker_user_info
from docker_image import fetch_docker_image_tags


async def process_docker_user(username):
    # Fetch Docker user info and repositories for the given GitHub user
    docker_user = await fetch_docker_user_info(username)

    if docker_user and docker_user.docker_repositories:
        # For each Docker repository, fetch its tags and instructions
        for repo in docker_user.docker_repositories:
            print(f"\nFetching Docker tags and instructions for {username}/{repo}")
            docker_image = await fetch_docker_image_tags(username, repo)
            docker_image.display_tags()



async def run():
    # Step 1: Get all GitHub usernames from the organization
    github_users = await org_nicknames(sys.argv[1])
    print(f"\nFound {len(github_users)} GitHub users in the organization.")

    # Step 2: For each GitHub user, process their Docker info and images
    tasks = [await process_docker_user(user) for user in github_users]
    # await asyncio.gather(*tasks)


# Run the entire process
if __name__ == "__main__":
    asyncio.run(run())
