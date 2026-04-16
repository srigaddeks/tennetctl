import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://kcontrol_dev_write:f11ed80a81f588efbc667681038db3506e77bf7f297c252f@ks-prod-cin-psql-02.postgres.database.azure.com:5432/kcontrol_dev?sslmode=require')
    row = await conn.fetchrow('SELECT id, job_type, output_json FROM "20_ai"."45_fct_job_queue" WHERE job_type = \'task_builder_preview\' ORDER BY created_at DESC LIMIT 1')
    if row:
        print('Job ID:', row['id'])
        out = row['output_json']
        if isinstance(out, str):
            out = json.loads(out)
        print(type(out))
        if isinstance(out, dict):
            print('keys:', out.keys())
            logs = out.get('creation_log', [])
            print('logs type:', type(logs))
            if isinstance(logs, list):
                print('logs length:', len(logs))
            if logs:
                print('first log type:', type(logs[0]))
                print('last log type:', type(logs[-1]))
                print('last log:', logs[-1])
            if 'stats' in out:
                print('stats type:', type(out['stats']))
                print('stats:', out['stats'])
    await conn.close()

asyncio.run(main())
