# sample.py - an example of a user module for the Scenario python worker

from time import sleep
    
#-------------------------------------------------------------------------------
# Task implementations
#-------------------------------------------------------------------------------
#
# This section of the module defines functions that perform the actual user
# processing. For a proper interaction with the worker script and XC Scenario,
# these functions must follow some rules:
#
#   - the first parameter, called 'x4b' these examples, is an object reference
#     on which a 'notify' method can be invoked to send errors or progress
#     reports back to XC Scenario
#
#   - other input parameters can be added at will, to implement the required
#     functionality.
#
#   - the function must return a dictionary of simple types
#
#   - the function signature (inputs) and outputs must match the description
#     given in task definitions object below.
#-------------------------------------------------------------------------------

def simple(x4b, arg):
    """A simple task that echoes its input argument."""
    print(f'[{__name__}] simple: arg={arg}')
    msg = f'The argument received was "{arg}".'
    return {'msg': msg}

#-------------------------------------------------------------------------------

def double(x4b, str_in, nbr_in):
    """A simple task showing some processing on its inputs."""
    print(f'[{__name__}] double: str_in={str_in}, nbr_in={nbr_in}')
    str_out = str_in + str_in
    try:
        nbr_out = str(2*int(nbr_in))
    except ValueError:
            msg = f"Incorrect value '{nbr_in}' for nbr_in, should be integer"
            x4b.notify('Error', msg)
            return {}
    return {'str_out': str_out, 'nbr_out': nbr_out}

#-------------------------------------------------------------------------------

def reporting_task(x4b, n, param):
    """A long-running task that periodically reports its progress."""
    print(f'[{__name__}] reporting_task: n={n}, param={param}')

    # Numeric parameters should always be tested
    try:
        n = int(n)
    except ValueError:
        msg = f'Incorrect value "{n}" for n, should be integer'
        x4b.notify('Error', msg)
        return {}
    
    msg = f'Input "{param}": going to sleep for {n} seconds.'
    x4b.notify('InProgress', msg, progressPercentage=str(0.0))

    for i in range(n):
        sleep(1)
        x4b.notify('InProgress', str(i+1), progressPercentage=str((i+1)/n))

    msg = f'Waking up.'
    x4b.notify('InProgress', msg)
    return {'result': f'Input "{param}", result is ok'}

#-------------------------------------------------------------------------------

def error_placeholder(x4b):
    """Send an error status"""
    print(f'[{__name__}] error_placeholder: FATAL error')
    msg = 'Task "error_placeholder" reports a fatal error.'
    x4b.notify('Error', msg)
    return {}

#-------------------------------------------------------------------------------

def zero_division(x4b):
    """Force a python exception"""
    print(f'[{__name__}] zero_division: force a division by zero')
    return {'x': 1/0}

#-------------------------------------------------------------------------------
# Task definitions (catalog)
#-------------------------------------------------------------------------------

def task_definitions():
    """Return the array of XC Scenario task definition objects.
    
    This array must have one element for each task, i.e. for each function
    implemented in the Task implementations section above. Each element is a
    python version of the CatalogTaskDefinition JSON object defined in the REST
    API definition, see
    https://scenario.xcomponent.com/taskcatalog/swagger/ui/index, POST
    /api/catalog-task-definitions/{namespace} operation.

    """

    task_defs = []

    #---------------------------------------------------------------------------

    # simple - a simple task that echoes its input argument
    task = {
        'namespace': __name__,
        'name': 'simple',
        'displayName': 'Single argument echoing task',
        'schemaVersion': 0,
    }
    task['inputs'] = [
        {
            'name': 'arg',
            'baseType': 'String',
            'description': 'Some input data',
        },
    ]
    task['outputs'] = [
        {
            'name': 'msg',
            'baseType': 'String',
            'description': 'Text output',
        },
    ]
    task_defs.append(task)

    #---------------------------------------------------------------------------

    # double - immediate task
    task = {
        'namespace': __name__,
        'name': 'double',
        'displayName': 'Immediate processing task',
        'schemaVersion': 0,
    }
    task['inputs'] = [
        {
            'name': 'str_in',
            'baseType': 'String',
            'defaultValue': 'xyz (default)',
            'description': 'Text argument',
        },
        {
            'name': 'nbr_in',
            'baseType': 'String',
            'defaultValue': '123',
            'description': 'Numeric argument',
        },
    ]
    task['outputs'] = [
        {
            'name': 'str_out',
            'baseType': 'String',
            'description': 'Text output',
        },
        {
            'name': 'nbr_out',
            'baseType': 'String',
            'description': 'Numeric result',
        },
    ]
    task_defs.append(task)

    #---------------------------------------------------------------------------

    # reporting_task - a long-running task that reports its progress
    task = {
        'namespace': __name__,
        'name': 'reporting_task',
        'displayName': 'Sleep N seconds',
        'schemaVersion': 0,
    }
    task['inputs'] = [
        {
            'name': 'n',
            'baseType': 'String',
            'description': 'Number of seconds to sleep',
        },
        {
            'name': 'param',
            'baseType': 'String',
            'description': 'Free-form text parameter',
        },
    ]
    task['outputs'] = [
        {
            'name': 'result',
            'baseType': 'String',
            'description': 'Resulting value',
        },
    ]
    task_defs.append(task)

    #---------------------------------------------------------------------------

    # error_placeholder - force an error status
    task = {
        'namespace': __name__,
        'name': 'error_placeholder',
        'displayName': 'Send an error status',
        'schemaVersion': 0,
    }
    task_defs.append(task)

    #---------------------------------------------------------------------------

    # zero_division - force a python exception
    task = {
        'namespace': __name__,
        'name': 'zero_division',
        'displayName': 'Force a python exception',
        'schemaVersion': 0,
    }
    task_defs.append(task)


    #---------------------------------------------------------------------------

    # Return the array of task definitions
    return task_defs

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
