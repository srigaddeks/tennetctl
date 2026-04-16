import asyncio, asyncpg, json
async def main():
    conn = await asyncpg.connect('postgresql://kcontrol_dev_write:f11ed80a81f588efbc667681038db3506e77bf7f297c252f@ks-prod-cin-psql-02.postgres.database.azure.com:5432/kcontrol_dev?sslmode=require')
    row = await conn.fetchrow('SELECT id, job_type, error_message, status_code, output_json FROM "20_ai"."45_fct_job_queue" WHERE job_type = \'task_builder_apply\' ORDER BY created_at DESC LIMIT 1')
    if row:
        print('Apply Job:', row['id'])
        print('Status:', row['status_code'])
        print('Error:', row['error_message'])
        out = row['output_json']
        if isinstance(out, str): out = json.loads(out)
        if isinstance(out, dict):
            print('stats:', out.get('stats'))
            print('stats type:', type(out.get('stats')))
            logs = out.get('creation_log', [])
            if logs: print('log type:', type(logs[0]))
    await conn.close()
asyncio.run(main())
