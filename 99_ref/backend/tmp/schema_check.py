import asyncio, asyncpg, json
from importlib import import_module
import sys
import os

# add backend to path
sys.path.insert(0, os.path.abspath('backend'))

async def main():
    schemas = import_module('20_ai.31_task_builder.schemas')
    TaskBuilderJobStatusResponse = schemas.TaskBuilderJobStatusResponse
    conn = await asyncpg.connect('postgresql://kcontrol_dev_write:f11ed80a81f588efbc667681038db3506e77bf7f297c252f@ks-prod-cin-psql-02.postgres.database.azure.com:5432/kcontrol_dev?sslmode=require')
    row = await conn.fetchrow("SELECT id, job_type, error_message, status_code, output_json, started_at, completed_at FROM \"20_ai\".\"45_fct_job_queue\" WHERE id = '606ae4e8-e0d6-4a42-98a1-5bd50579e4eb'")
    
    if row:
        data = dict(row)
        out = data['output_json']
        if isinstance(out, str): out = json.loads(out)
        out = out or {}
        
        raw_log = out.get('creation_log', [])
        creation_log = []
        for item in raw_log:
            if isinstance(item, str):
                try: item = json.loads(item)
                except Exception: item = {'event': 'log', 'message': item}
            creation_log.append(item)
            
        stats = out.get('stats', {})
        if isinstance(stats, str):
            try: stats = json.loads(stats)
            except Exception: stats = {}
            
        def _dt(v):
            return v.isoformat() if v is not None and hasattr(v, 'isoformat') else str(v) if v else None
            
        try:
            res = TaskBuilderJobStatusResponse(
                job_id=str(data['id']),
                status=data['status_code'],
                job_type=data['job_type'],
                creation_log=creation_log,
                stats=stats,
                error_message=data.get('error_message'),
                started_at=_dt(data.get('started_at')),
                completed_at=_dt(data.get('completed_at'))
            )
            print('Schema check passed!')
        except Exception as e:
            print('SCHEMA FAILED:', e)
            import traceback
            traceback.print_exc()
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
