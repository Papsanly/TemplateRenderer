import asyncio
import os

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1500, "height": 600})

        html_path = os.path.abspath("renderer/templates/test_temp.html")
        await page.goto(f"file://{html_path}", wait_until="networkidle")
        await page.wait_for_timeout(500)

        await page.screenshot(
            path="../test_gift_card.png",
            clip={"x": 0, "y": 0, "width": 1500, "height": 600},
        )
        await browser.close()
        print("Generated: test_gift_card.png")


if __name__ == "__main__":
    asyncio.run(main())
