# exemple.py - un exemple de module utilisateur pour le worker Scenario
# Auteur: Joao Moreira de Sa Coutinho, joao.moreira@invivoo.com
# (c) Invivoo, 2023

from time import sleep
    
#-------------------------------------------------------------------------------
# Fonctions de traitement
#-------------------------------------------------------------------------------

# Cette partie du module contient les fonctions métier qui sont à mises à
# disposition du concepteur de scenarios, pour être appelées par le worker.

def simple(x4b, arg):
    """Une fonction qui renvoie simplement son argument."""
    print(f'[{__name__}] sbimple: arg={arg}')

    # Début traitement spécifique
    # Fin traitement spécifique
    
    msg = f'The argument received was "{arg}".'
    return {'msg': msg}

#-------------------------------------------------------------------------------

def double(x4b, str_in, nbr_in):
    """Une fonction qui illustre un traitement spécifique."""
    print(f'[{__name__}] double: entrées: str_in={str_in}, nbr_in={nbr_in}')

    # Début traitement spécifique
    str_out = str_in + str_in
    try:
        nbr_out = str(2*int(nbr_in))
    except ValueError:
            msg = f"Incorrect value '{nbr_in}' for nbr_in, should be integer"
            x4b.notifie('Error', msg)
            return {}
    # Fin traitement spécifique

    return {'str_out': str_out, 'nbr_out': nbr_out}

#-------------------------------------------------------------------------------

def reporting_task(x4b, n, param):
    """Une tâche qui notifie périodiquement son avancement."""
    print(f'[{__name__}] reporting_task: n={n}, param={param}')

    # Vérification d'un paramètre numérique
    try:
        n = int(n)
    except ValueError:
        msg = f'Valeur "{n}" incorrecte, devrait être un entier'
        x4b.notifie('Error', msg)
        return {}
    
    # Début de traitement "long"
    msg = f'Input param = "{param}", nombre d\'itérations = {n}.'
    x4b.notifie('InProgress', msg, progressPercentage=str(0.0))

    for i in range(n):
        sleep(1)
        x4b.notifie('InProgress', str(i+1), progressPercentage=str((i+1)/n))

    msg = f'Fin d\'exécution de la tâche "reporting_task".'
    x4b.notifie('InProgress', msg)
    # Fin du traitement "long"

    # Un seul paramètre de sortie, de type string
    return {'result': f'Traitement correctement terminé.'}

#-------------------------------------------------------------------------------

def zero_division(x4b):
    """Force une exception python"""
    print(f'[{__name__}] zero_division: force une exception en divisant par zéro')
    return {'x': 1/0}

#-------------------------------------------------------------------------------
# Définition de tâches pour le catalogue
#-------------------------------------------------------------------------------

def task_definitions():
    """Retourne le tableau des définitions de tâches/fonctions.
    
    Le tableau produit doit avoir une entrée par tâche, i.e. une pour chaque
    fonction définie au-dessus. Chaque entrée est la version python de l'objet
    appelé CatalogTaskDefinition dans le swagger, et chaque paramètre d'entrée
    ou de sortie est la version python de l'objet CatalogParameterType. URL du
    swagger :

    https://scenario.xcomponent.com/taskcatalog/swagger/ui/index

    """

    task_defs = []

    #---------------------------------------------------------------------------

    # simple - une fonction qui renvoie simplement son argument
    task = {
        'namespace': __name__,
        'name': 'simple',
    }
    task['inputs'] = [
        {
            'name': 'arg',
            'baseType': 'String',
        },
    ]
    task['outputs'] = [
        {
            'name': 'msg',
            'baseType': 'String',
        },
    ]
    task_defs.append(task)

    #---------------------------------------------------------------------------

    # double - une fonction qui illustre un traitement spécifique
    task = {
        'namespace': __name__,
        'name': 'double',
    }
    task['inputs'] = [
        {
            'name': 'str_in',
            'baseType': 'String',
            'defaultValue': 'xyz (default)',
        },
        {
            'name': 'nbr_in',
            'baseType': 'Number',
            'defaultValue': '123',
        },
    ]
    task['outputs'] = [
        {
            'name': 'str_out',
            'baseType': 'String',
        },
        {
            'name': 'nbr_out',
            'baseType': 'Number',
        },
    ]
    task_defs.append(task)

    #---------------------------------------------------------------------------

    # reporting_task - une tâche qui notifie périodiquement son avancement
    task = {
        'namespace': __name__,
        'name': 'reporting_task',
    }
    task['inputs'] = [
        {
            'name': 'n',
            'baseType': 'String',
        },
        {
            'name': 'param',
            'baseType': 'String',
        },
    ]
    task['outputs'] = [
        {
            'name': 'result',
            'baseType': 'String',
        },
    ]
    task_defs.append(task)

    #---------------------------------------------------------------------------

    # zero_division - force une exception python
    task = {
        'namespace': __name__,
        'name': 'zero_division',
    }
    task_defs.append(task)


    #---------------------------------------------------------------------------

    # Retourne le tableau des définitions de tâches
    return task_defs

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print("Ce module n'a pas vocation à être exécuté directement.")
