import aiohttp
import asyncio
from bs4 import BeautifulSoup


BASE_URL = "https://github.com/orgs/{}/people"
COOKIE = "_octo=GH1.1.102197887.1725354010; _device_id=89e1fc3cf7953bf90cd4f69934a8839b; saved_user_sessions=7037785%3AcsqRUwcpqBufFlgxyvMRPQG7r2lQFAiTneaXbXzHzs5Aewsu; user_session=csqRUwcpqBufFlgxyvMRPQG7r2lQFAiTneaXbXzHzs5Aewsu; __Host-user_session_same_site=csqRUwcpqBufFlgxyvMRPQG7r2lQFAiTneaXbXzHzs5Aewsu; logged_in=yes; dotcom_user=c0rv4x; color_mode=%7B%22color_mode%22%3A%22dark%22%2C%22light_theme%22%3A%7B%22name%22%3A%22light%22%2C%22color_mode%22%3A%22light%22%7D%2C%22dark_theme%22%3A%7B%22name%22%3A%22dark_dimmed%22%2C%22color_mode%22%3A%22dark%22%7D%7D; tz=Europe%2FIstanbul; preferred_color_mode=light; _gh_sess=Dmbg5NvlWB2adjE4gRZx8RJz%2BCLhQeaK7juZaHgPa1%2Bmj4omtO4B55HqtwIunJXh33MxjkaJuponrRmbgzEd4iEIhj0%2BoNnEokL3TW7xihL%2Fm5IhAMNvynZODIBRnCI0gSs1GYU%2F16HCqfoS5lMrbYU0pniEhjQP8N6LQJGz5DYFLJ3GhE4ck3XLK1GJY99ngOxINfFI7yxUBa27KjmqsjvCIi5vDzNko8JQm4iXvvU5JI9GWOLieyYU4BPb6q7Wptdz47Aq6rEodP0j8HgSMaJLas%2BDKwgbwHlzAYnwumlb3HB6%2B9EZGJJUJYczpbXVcWjVSYEgM7rmcwCaQVCLfcpBlW4wU%2FJGOBQtb5UZgBeRBNF3EpxKb%2F8PnegjmFxI9%2B4LNLY%2F%2FtOZNjwMkp1GwOI7zPSNFTtEIODyZ%2FaNTuw0Ce5Z67iYlRxVzPnbUHS0IQE%2FrVM3e48J9f7eEPt63hLf0lrG3Lnx03mmc89pf5IBWsqhTe3qiYdRMbMHmq5OctZ11RceNIz6GgVrNPFoFHJV9jySPQllUFzGgbsiGTJzuPxlANIj8PSDjt0DH33zRYIJ3hSi8G502sd8cffF3Uk14cr0lMUv4UgFG0wBZewpDFApRec6ypxgb5sGJEiLPWGL4LmNtzM5X5VzWWx%2BI1QCbR2zY%2FYG%2BQYC3jWarjF5jBWuA%2Fy9akCLlbREK8BREfe%2Bjyzo2y6lxXx5KmV5jOLkFeg%2F4Cd366wNM%2F5xijAbCydNkFRb8bu%2FCDsEIxv%2BxZufvoUMxVqBLKJHGXiILhQ2STjcBDhNOEBx1YkEfNBfGgJRE1nyLZ8XN1pFVyrgvE4faceB6UFhN2NPlW8GKklTBSQQegWGeWvAjTJvDZG2BGhGAzUZi8PeajKOG3UFFOn5R0dHrEQ8106qrl%2F6pFFgN%2Bn4dIKHynEO8WsByOBwRhxyWGchBc9Ryh9z%2FXxNDPHlJ5QF1uTaElGHCMcm%2FvMBlo%2FgD9VnYctautKr5OZvG07XCtXhWKoObkZ8Z%2BU0Vlr%2B%2BIn7MnO0Ufxa6RuNAkIZd%2FcjkWVOePeOoHUX%2FWgblwVCG3%2FZiD1HzHdjz2rVQWu%2BJAn0qge8YOqOLmNTYkrbid2s8Zzjct8ojG8DvITXl8hEXMSGRk16pWlp%2FMwj4PUkMUtk%2BfwTqh7v2M%2Bfdou4fI83BBCGO5feoitiNSg8gQSY37vqPKaLr8e%2FDQ3dm6FnzeTZn5ymt1XHr41wYEg9GHHaVczqwxP73x3%2BRXuPwUmOHBtnD0wzI%2FjwYqQzBoQUrS0XgPqeGTD3amnqvIFkPbsB5YXFejyyB%2BYvOUHMxOMO4ya0OQtS4hr4DPmw8bZ3Rcf5d8wuj86ROSoqewBNH2Hp7TBZLpHFLU8FXURAGHs%2BHWgqjkSb6SUMDRnGUSat5Ah1KvI%3D--ATzPBn0SZ1KU4JON--nTMvhAfDYNhhx83Y6Z%2Favw%3D%3D"


async def org_nicknames(org):
    headers = {
        "Cookie": COOKIE
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        total_pages = await get_total_pages(org,session)
        tasks = []
        
        # Traverse all pages and collect nicknames
        for page in range(1, total_pages + 1):
            tasks.append(get_nicknames_from_page(org, session, page))
        
        results = await asyncio.gather(*tasks)

        all_nicknames = []
        all_nicknames.insert(0, org)
        all_nicknames += [nickname for result in results for nickname in result]

        return all_nicknames


async def fetch_html(session, url):
    async with session.get(url) as response:
        return await response.text()


async def get_total_pages(org, session):
    html = await fetch_html(session, BASE_URL.format(org))
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the em tag with the class 'current' to get the total number of pages
    try:
        pagination = soup.find('div', {'class': 'pagination'})
        current_page = pagination.find('em', {'class': 'current'})
        
        if current_page:
            total_pages = current_page.get('data-total-pages')
            return int(total_pages)
        else:
            raise Exception("Unable to find pagination data")
    except:
        return 1


async def get_nicknames_from_page(org, session, page_num):
    url = f"{BASE_URL}?page={page_num}".format(org)
    html = await fetch_html(session, url)
    soup = BeautifulSoup(html, 'html.parser')
    nicknames = []
    
    # Find all the anchor tags with the required attributes to get nicknames
    users = soup.find_all('a', {'class': 'd-inline-block', 'data-hovercard-type': 'user'})
    for user in users:
        href = user.get('href')
        nickname = href.split('/')[-1]
        nicknames.append(nickname)
    
    return nicknames


async def main():
    nicknames = await org_nicknames('aws')
    print(nicknames)


# Run the main function in an event loop
if __name__ == "__main__":
    asyncio.run(main())
