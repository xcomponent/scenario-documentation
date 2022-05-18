# worker.py - the XC Scenario worker engine

"""This is the worker.py script. It is the generic part of the python worker
program; it handles the core mechanism of polling for tasks, invoking the user
code for task execution, and posting task statuses. It imports a user module
that contains the actual user code.

"""

import os
import sys
import json
import requests
from time import sleep
from datetime import datetime

#-------------------------------------------------------------------------------
# Environment
#-------------------------------------------------------------------------------

# The address of the target XC Scenario system, and an API key providing
# authentication and authorization for REST API calls, are taken from
# environment variables. This makes it easy to configure the worker, in
# particular when running it inside a docker container.

# Target system server url
if 'XC_SCENARIO_SERVER' not in os.environ:
    raise RuntimeError('Missing XC_SCENARIO_SERVER environment variable')
server_url = os.environ['XC_SCENARIO_SERVER']

# Target system authentication token
if 'XC_SCENARIO_APIKEY' not in os.environ:
    raise RuntimeError('Missing XC_SCENARIO_APIKEY environment variable')
apikey = os.environ['XC_SCENARIO_APIKEY']

#-------------------------------------------------------------------------------
# Global settings
#-------------------------------------------------------------------------------

polling_interval = 1 # in seconds

#-------------------------------------------------------------------------------
# XC Scenario REST API function calls
#-------------------------------------------------------------------------------

def UpdateCatalogTaskDefinition(postedCatalogTaskDefinitions, namespace,
        removePreviousTasks=None):
    """Add tasks to Catalog.

    This function encaspulates a call to the TaskCatalog/Post REST API
    operation, to publish a task catalog.
    """
    
    url = f'{server_url}/taskcatalog/api/catalog-task-definitions/{namespace}'
    query_params = dict(
        removePreviousTasks=removePreviousTasks,
    )
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'bearer {apikey}',
    }
    data = json.dumps(postedCatalogTaskDefinitions)
    r = requests.post(url, headers=headers, data=data, params=query_params)
    if r.status_code >= 400:
        raise RuntimeError(f'[{r.status_code}] {r.text}')

#-------------------------------------------------------------------------------

def GetAvailableTask(catalogTaskDefinitionNamespace,
        catalogTaskDefinitionName=None):
    """Gets next task to execute.

    This function encaspulates a call to the Polling/Poll REST API
    operation, to retrieve tasks from the task queue.
    """
    
    url = f'{server_url}/polling/api/namespaces' \
      + f'/{catalogTaskDefinitionNamespace}/task-instances/poll'
    query_params = dict(
        catalogTaskDefinitionName=catalogTaskDefinitionName,
    )
    headers = {
        'Authorization': f'bearer {apikey}',
    }
    r = requests.post(url, headers=headers, params=query_params)
    if r.status_code >= 400:
        raise RuntimeError(f'[{r.status_code}] {r.text}')
    if r.status_code == 200:
        return r.json()

#-------------------------------------------------------------------------------

def UpdateTaskStatusEvent(taskStatus):
    """Sends status update.

    This function encaspulates a call to the TaskStatus REST API
    operation, to post an updated task status.
    """

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
# Worker code
#-------------------------------------------------------------------------------

def clean_dict(d):
    """Filter out "x#type" keys in the inputData dictionary"""
    return {k: v for k, v in d.items() \
            if not (k.endswith('#type') or k.endswith('#subtype'))}

#-------------------------------------------------------------------------------

def post_task_status(task_instance_id, status, msg, outputs=None):
    """Post a task status.

    The "status" parameter can have the values 'InProgress', 'Error', or
    'Completed'. This function sends the given status to XC Scenario, where the
    currenty running task will be updated, with its status being visible in the
    cockpit screen.

    """
    
    # Create the status object.
    task_status = {
        'taskInstanceId':  task_instance_id,
        'status': status,
        'message': msg,
        'outputValues': outputs,
    }
    
    # Post the given task status
    try:
        UpdateTaskStatusEvent(task_status)
    except RuntimeError as e:
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} worker: posting task status failed')
        print(e)
        return

    # Return the data in case we want to use it or print it
    return task_status

#-------------------------------------------------------------------------------

class Notification():
    """Notification object.

    This object implements a communication mechanism to allow the python
    code that implements a task to send notifications to XC Scenario. An
    instance of this class is passed to each user function, so that the
    function can invoke the "notify" method.
    """
    
    def __init__(self, task_instance_id, module_name):
        self.task_instance_id = task_instance_id
        self.module_name = module_name
        self.isError = False

    def notify(self, status, msg, outputs=None, progressPercentage=None):
        """Send a task status to XC Scenario.
        
        The given message will be displayed by XC Scenario in the 
        "Message" section of the task's screen in the cockpit.
        """

        self.isError = (status == 'Error')
        
        task_status = post_task_status(self.task_instance_id, status, msg, outputs=outputs)
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} worker: task status (notification) posted')
        print(json.dumps(task_status, indent=4))

#-------------------------------------------------------------------------------
# work - periodically poll the task queue, retrieve tasks, do the actual work 
#-------------------------------------------------------------------------------

def do_work(mod, namespace, autocomplete=True):
    """Periodically poll the task queue, retrieve tasks, do the actual work.

    This is the heart of the worker's logic. The code extracts tasks
    from the task queue, and calls the corresponding function from the
    user module (if found). If the user function raises an exception,
    the code will notify XC Scenario by posting an 'InError' status; if
    it completes normally, without errors, and if the autocomplete flag
    is activated, the worker code will post the 'Completed' status.
"""
    
    while True:
        # Get (at most) one task instance from the task queue. The task
        # instance retrieved from the task queue includes the user function's
        # name, as well as the values for the input parameters.
        ti = GetAvailableTask(namespace)
            
        # When the queue is empty, there's no exception raised, 'ti' is None
        if ti is None:
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f'{dt} worker[{namespace}]: task queue is empty')
            sleep(polling_interval)
            continue

        # Get the task for execution from the user's module
        task_name = ti['catalogTaskDefinitionName']
        if task_name not in mod.__dict__:
            # This is a mismatch between the published catalog, used to create
            # a scenario definition, and the python module that's supposed to
            # implement the task. The catalog has advertised a task, but it
            # can't be found in the module. Log the error.
            print('-'*60)
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            namespace = ti['catalogTaskDefinitionNamespace']
            msg = f'{dt} worker[{namespace}]: unknown task: {namespace}/{task_name}'
            print(msg)

            # From the XC Scenario point of view, the task that we just
            # extracted from the task queue needs to be flagged as 'Error',
            # since we couldn't execute it.
            post_task_status(ti['id'], 'Error', msg)
                
            # Back to the loop
            sleep(polling_interval)
            continue

        # We found the task code, log it.
        print('-'*60)
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} worker[{namespace}]: calling task "{task_name}"')
        print(json.dumps(ti, indent=4))

        # Remove "#type" from the input data
        inputs = clean_dict(ti['inputData'])

        # Prepare the notification mechanism, so that user functions can call
        # notifier.notify() if needed.
        notifier = Notification(ti['id'], mod.__name__)
        
        # Invoke the task_name function from the user module (use module name),
        # pass the input data, and retrieve a dictionary of output data
        # (outputValues)
        excep = None
        try:
            outputValues = mod.__dict__[task_name](notifier, **inputs)
        except Exception as e:
            excep = e
        
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} worker[{namespace}]: task {task_name} returned')

        # If an exception was throw in the user code, post an error status
        if excep is not None:
            print(excep)
            msg = 'Exception raised by worker task'
            post_task_status(ti['id'], 'Error', msg)
            
        # Notify 'Completed' state only if we have autocomplete enabled
        if excep is None and not notifier.isError and autocomplete:
            post_task_status(ti['id'], 'Completed', '', outputs=outputValues)

        # Sleep between polls
        sleep(polling_interval) 

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) not in [2, 3]:
        print(f"""\
Usage: {sys.argv[0]} <namespace> [ <autocomplete true/false> ]

This code assumes there's a python module, with the same name as the namespace,
that can be found through python's standard import mechanisms, such as the
PYTHONPATH variable.""")
        exit(-1)

    # The worker will publish 'Completed' status for every task that finishes
    # normally (without having thrown any exceptions), unless explicitly
    # requested here with autocomplete == 'false'
    autocomplete = True
    if len(sys.argv) == 3:
        s = sys.argv[2].lower()
        if s not in ['true', 'false']:
            print(f'"{sys.argv[2]}" unrecognized boolean value')
            exit(-1)
        autocomplete = (s != 'false')

    # The namespace is also the user module name
    namespace = sys.argv[1]

    # Get the user module and publish its catalog
    mod = __import__(namespace)
    UpdateCatalogTaskDefinition(mod.task_definitions(), namespace)

    # Poll the task queue and call execution functions
    do_work(mod, namespace, autocomplete=autocomplete)

# End of worker.py
#-------------------------------------------------------------------------------
