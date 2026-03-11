import json
import subprocess

try:
    # Get the latest run ID
    output = subprocess.check_output(['gh', 'run', 'list', '--workflow=deploy_pages.yml', '--limit', '1', '--json', 'databaseId']).decode('utf-8')
    run_id = json.loads(output)[0]['databaseId']
    
    # Get the jobs for that run
    jobs_output = subprocess.check_output(['gh', 'api', f'repos/takumi160334-pixel/ec_consultant_portal/actions/runs/{run_id}/jobs']).decode('utf-8')
    jobs_data = json.loads(jobs_output)
    
    for job in jobs_data.get('jobs', []):
        print(f"Job: {job['name']} - {job['conclusion']}")
        for step in job.get('steps', []):
            if step['conclusion'] not in ['success', 'skipped']:
                print(f"  FAILED STEP: {step['name']}")
                
                # Fetch step log if possible
                try:
                    log_output = subprocess.check_output(['gh', 'run', 'view', str(run_id), '--log-failed']).decode('utf-8')
                    print("  LOGS:")
                    print(log_output)
                except Exception as e:
                    print(f"  Could not view log directly: {e}")
                    
except Exception as e:
    print(f"Error: {e}")
