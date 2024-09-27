import sys
import asyncio
import argparse

from github.github_users import org_nicknames
from docker.docker_hub import process_docker_user
from users.snov import fetch_company_emails


async def run(fetch_from_github=None, org_name=None, docker_usernames=None, fetch_emails_domain=None):
    if fetch_emails_domain:
        await fetch_company_emails(fetch_emails_domain)
        return

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
    parser = argparse.ArgumentParser(description="Fetch Docker info for GitHub org, specific Docker users, or emails.")
    parser.add_argument("--github-org", help="GitHub organization to fetch users from")
    parser.add_argument("--docker-users", nargs="*", help="Docker users whose layers should be found")
    parser.add_argument("--fetch-emails", metavar="DOMAIN", help="Get a list of emails by company domain")

    args = parser.parse_args()

    # Determine the mode of operation
    if args.fetch_emails:
        asyncio.run(run(fetch_emails_domain=args.fetch_emails))
    elif args.github_org:
        asyncio.run(run(fetch_from_github=True, org_name=args.github_org))
    elif args.docker_users:
        asyncio.run(run(fetch_from_github=False, docker_usernames=args.docker_users))
    else:
        print("You must provide either --github-org, --docker-users, or --fetch-emails.")
        sys.exit(1)


# Run the entire process
if __name__ == "__main__":
    main()
