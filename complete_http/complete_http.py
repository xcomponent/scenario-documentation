# complete_http.py - complete an HTTP task using taskInstanceId

"""\ In X4B Scenario, the Connectors/RestCall task sends some information in
the HTTP headers:

  * X-Scenario-TaskStatusUrl
  * X-Scenario-WorkflowInstanceId
  * X-Scenario-TaskInstanceId

This code uses the TaskInstanceId parameter to complete the task.
"""
import os
import sys
import json
import requests

# Target system server url
if 'X4B_SCENARIO_SERVER' not in os.environ:
    raise RuntimeError('Missing X4B_SCENARIO_SERVER environment variable')
server_url = os.environ['X4B_SCENARIO_SERVER']

# Target system authentication token
if 'X4B_APIKEY' not in os.environ:
    raise RuntimeError('Missing X4B_APIKEY environment variable')
apikey = os.environ['X4B_APIKEY']

#-------------------------------------------------------------------------------

def UpdateTaskStatusEvent(taskStatus):
    """Sends status update"""
    url = f'{server_url}/taskstatus/api/task-statuses'
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'bearer {apikey}',
    }
    data = json.dumps(taskStatus)
    r = requests.post(url, headers=headers, data=data)
    if r.status_code >= 400:
        raise RuntimeError(f'[{r.status_code}] {r.text}')

#-------------------------------------------------------------------------------

def complete_http(task_inst_id):
    obj = {
        'taskInstanceId': task_inst_id,
        'status': 'Completed',
        'message': 'Completion by complete_http.py',
        'outputValues': { 'statusCode': '200' },
    }
    print('Sending task status update')
    UpdateTaskStatusEvent(obj)

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

# Command line argument
if len(sys.argv) != 2:
    print(f'Usage: {sys.argv[0]} <task_inst_id>')
    exit(-1)

complete_http(sys.argv[1])

# End of complete_http.py
#===============================================================================
