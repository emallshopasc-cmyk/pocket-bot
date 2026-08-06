import asyncio

# Patch extra_headers compatibility issue in asyncio loop
try:
    import asyncio.proactor_events
    orig_create_conn = asyncio.proactor_events._ProactorBasePipeTransport
except:
    pass

import asyncio
orig_create_conn = asyncio.BaseEventLoop.create_connection

def patched_create_conn(self, protocol_factory, host=None, port=None, **kwargs):
    kwargs.pop('extra_headers', None)
    kwargs.pop('additional_headers', None)
    return orig_create_conn(self, protocol_factory, host=host, port=port, **kwargs)

asyncio.BaseEventLoop.create_connection = patched_create_conn

from pocketoptionapi_async import AsyncPocketOptionClient

SSID = '42["auth",{"session":"bkalk3kp4bgm91033ln96qeccv","isDemo":1,"uid":137750196,"platform":2}]'

async def test():
    client = AsyncPocketOptionClient(SSID, is_demo=True)
    try:
        res = await client.connect()
        print("PO Connection Result:", res)
        if res:
            bal = await client.get_balance()
            print("Balance:", bal)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    asyncio.run(test())
