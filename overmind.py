import sys
import asyncio
import argparse

from github_users import org_nicknames
from docker_hub import fetch_docker_user_info
from docker_image import fetch_docker_image_tags


async def process_docker_user(username):
    # Fetch Docker user info and repositories for the given Docker user
    docker_user = await fetch_docker_user_info(username)

    if docker_user and docker_user.docker_repositories:
        # For each Docker repository, fetch its tags and instructions
        for repo in docker_user.docker_repositories:
            print(f"\nFetching Docker tags and instructions for {username}/{repo}")
            docker_image = await fetch_docker_image_tags(username, repo)
            docker_image.display_tags()


async def run(fetch_from_github, org_name=None, docker_usernames=None):
    target_users = []

    # Step 1: Either fetch GitHub usernames from the organization or use provided Docker usernames
    if fetch_from_github:
        if not org_name:
            raise ValueError("Organization name must be provided when fetching from GitHub.")
        target_users = await org_nicknames(org_name)
        print(f"\nFound {len(target_users)} GitHub users in the organization.")
    else:
        if not docker_usernames:
            raise ValueError("At least one Docker Hub username must be provided.")
        target_users = docker_usernames

    # Step 2: For each GitHub or Docker Hub user, process their Docker info and images
    tasks = [await process_docker_user(user) for user in target_users]


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Fetch Docker info for GitHub org or specific Docker users.")
    parser.add_argument("--github-org", help="GitHub organization to fetch users from")
    parser.add_argument("--docker-users", nargs="*", help="List of Docker Hub usernames to process")
    
    args = parser.parse_args()

    # Determine the mode of operation (GitHub org or Docker usernames)
    if args.github_org:
        asyncio.run(run(fetch_from_github=True, org_name=args.github_org))
    elif args.docker_users:
        asyncio.run(run(fetch_from_github=False, docker_usernames=args.docker_users))
    else:
        print("You must provide either --github-org or --docker-users.")
        sys.exit(1)


# Run the entire process
if __name__ == "__main__":
    main()
