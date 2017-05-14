import aiohttp
import asyncio

async def fetch(client, domain):
    print(domain)
    async with client.get(domain, proxy="http://106.32.66.161:21281") as resp:
        assert resp.status == 200
        return await resp.text()

async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        html = await fetch(client, 'http://amazon.com')
        print(html)
    async with aiohttp.ClientSession(loop=loop) as client:
        html = await fetch(client, 'http://google.com')
        print(html)
    async with aiohttp.ClientSession(loop=loop) as client:
        html = await fetch(client, 'http://immobiliare.it')
        print(html)

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))