from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio
import json

async def main():
    all_transport_urls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=False)
        page = await browser.new_page()
        await page.goto("https://www.marsruti.lv/liepaja/#liepaja")

        await asyncio.sleep(2)

        tbody = page.locator("#tblRoutes > tbody")
        response = await tbody.inner_html()
        soup = BeautifulSoup(response, "html.parser")

        all_a = soup.find_all("a", {"title": "Rādīt kustības sarakstus"})

        for a in all_a:
            route_name = a.find_all("span")[1].text
            route_url = "https://www.marsruti.lv/liepaja/" + a.get("href")
            route = {
                "name": route_name, 
                "url": route_url
            }
            all_transport_urls.append(route)

        await browser.close()

    with open("all_transports_urls.json", "w") as file:
        json.dump(all_transport_urls, file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())