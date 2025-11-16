import asyncio
from playwright.async_api import async_playwright, expect
from bs4 import BeautifulSoup
import json

def filter_minutes(el):
    if '\\' in el:
        index = el.index("\\")
        return int(el[0:index])
    return int(el)



async def parse_tables(page, dir_url):
    await page.goto(dir_url)
    await asyncio.sleep(1)

    stations_list = page.locator("#dlDirStops1")

    stations_list_html = await stations_list.inner_html()
    soup = BeautifulSoup(stations_list_html, "html.parser")

    stations_a = soup.find_all("a")

    stations = []
    for station_a in stations_a:
        stations.append({
            "station_name": station_a.text,
            "station_table_href": "https://www.marsruti.lv/liepaja/" + station_a.get("href")
        })

    stations_time_table = {}
    for station in stations:
        await page.goto(station["station_table_href"])
        await asyncio.sleep(0.5)
        tables_container = page.locator("#divScheduleContentInner")
        tables_container_html = await tables_container.inner_html()
        soup = BeautifulSoup(tables_container_html, "html.parser")
        tabels = soup.find_all("table")
        for table in tabels:
            time_table = {}
            all_trs = table.find_all("tr")
            for tr in all_trs:
                if (all_trs.index(tr) == 0):
                    continue
                hour = ''.join([char for char in tr.find("th").text if char.isdigit()])
                if (hour == ""):
                    continue
                hour = int(hour)
                all_a = tr.find_all("a")
                minutes = list(map(filter_minutes, [a.text.strip() for a in all_a]))
                time_table[hour] = minutes
            stations_time_table[station["station_name"]] = time_table
    return stations_time_table
        

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=False)
        page = await browser.new_page()

        with open("all_transports_urls.json", "r") as file:
            transports = json.load(file)

        routes_time_tables = {}
    
        for transport in transports:
            print(f"Прогресс - {int(round((transports.index(transport) + 1) / len(transports), 2)*100)}%")
            await page.goto(transport["url"])
            await asyncio.sleep(1)

            dir_choice = page.locator("#ulScheduleDirectionsList")
            dir_choice_html = await dir_choice.inner_html()
            soup = BeautifulSoup(dir_choice_html, "html.parser")

            all_direction_refs = soup.find_all("a")
            dirs = []
            for ref in all_direction_refs:
                dirs.append({
                    "direction_name": ref.text.strip(),
                    "direction_url": "https://www.marsruti.lv/liepaja/" + ref.get("href")
                })
            route_tables = {}
            for dir in dirs:
                route_tables[dir["direction_name"]] = await parse_tables(page, dir["direction_url"])

            routes_time_tables[transport["name"]] = route_tables

        with open("routes_time_tables.json", "w", encoding='utf-8') as file:
            json.dump(routes_time_tables, file, ensure_ascii=False, indent=1)

        await browser.close()
        


if __name__ == "__main__":
    asyncio.run(main())