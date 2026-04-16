import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://kcontrol_dev_write:f11ed80a81f588efbc667681038db3506e77bf7f297c252f@ks-prod-cin-psql-02.postgres.database.azure.com:5432/kcontrol_dev?sslmode=require')
    
    # how does asyncpg handle $1::jsonb when a string is passed?
    s = json.dumps({"a": 1})
    val = await conn.fetchval('SELECT $1::jsonb', s)
    print("val:", val)
    print("val type:", type(val))
    
    # what if we use conn.execute and insert it into a dummy query
    val2 = await conn.fetchval('SELECT jsonb_typeof($1::jsonb)', s)
    print("typeof:", val2)
    
    await conn.close()

asyncio.run(main())
