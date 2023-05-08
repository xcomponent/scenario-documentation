# worker.py - un worker python pour X4B Scenario
# Auteur: Joao Moreira de Sa Coutinho, joao.moreira@invivoo.com
# (c) Invivoo, 2023

"""Ce script contient la partie générique du code du worker python, avec la
gestion de la file d'attente des tâches, l'appel aux fonctions "métier" de
l'utilisateur, et la publication des status des tâches.

Le script importe un module utilisateur qui contient la partie spécifique du
code, avec l'implémentation des tâches "métier", l'idée étant de ré-utiliser à
chaque fois cette partie générique.

"""

import os
import sys
import json
import requests
from time import sleep
from datetime import datetime
from importlib import import_module

#-------------------------------------------------------------------------------
# Configuration / environnement
#-------------------------------------------------------------------------------

# L'adresse cible (URL) du serveur X4B Scenario et la clé d'API qui fournit
# l'authentification et les autorisations pour les appels REST X4B sont
# attendues dans des variables d'environnement. Ce mécanisme permet de
# configurer facilement le worker, notamment lorsqu'il est exécuté dans un
# container docker.

# Adresse cible serveur (URL), par exemple https://scenario.xcomponent.com pour
# la plateforme en ligne Invivoo
if 'X4B_SCENARIO_SERVER' not in os.environ:
    raise RuntimeError('Missing X4B_SCENARIO_SERVER environment variable')
server_url = os.environ['X4B_SCENARIO_SERVER']

# Clé d'API pour les appels REST,  à récupérer depuis l'écran "Settings"
if 'X4B_APIKEY' not in os.environ:
    raise RuntimeError('Missing X4B_APIKEY environment variable')
apikey = os.environ['X4B_APIKEY']

#-------------------------------------------------------------------------------
# Paramètres globaux
#-------------------------------------------------------------------------------

# Définit le rythme d'interrogation de la file d'attente des tâches
polling_interval = 1 # en secondes

#-------------------------------------------------------------------------------
# APIs REST X4B Scenario
#-------------------------------------------------------------------------------

def publication_catalogue(postedCatalogTaskDefinitions, namespace,
        removePreviousTasks=None):
    """Publie un catalogue de tâches."""
    
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

def tache_suivante(catalogTaskDefinitionNamespace,
        catalogTaskDefinitionName=None):
    """Récupère la prochaine tâche à exécuter."""
    
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

def maj_status(taskStatus):
    """Met à jour le statut d'une tâche."""

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
# Fonctions du worker
#-------------------------------------------------------------------------------

def clean_dict(d):
    """Supprime certaines clés du dictionnaire fourni."""
    return {k: v for k, v in d.items() \
            if not (k.endswith('#type') or k.endswith('#subtype'))}

#-------------------------------------------------------------------------------

def post_task_status(task_instance_id, status, msg, outputs=None):
    """Publie le status d'une tâche.

    Le paramètre "status" peut prendre les valeurs 'InProgress', 'Error', ou
    'Completed'. Cette fonction envoie le status donné à X4B Scenario, où la
    tâche actuellement en cours d'exécution sera mise à jour, avec le status
    indiqué par la couleur de la pastille dans le cockpit.

    """
    
    # Création de l'objet TaskStatus
    task_status = {
        'taskInstanceId':  task_instance_id,
        'status': status,
        'message': msg,
        'outputValues': outputs,
    }
    
    # Publication du status
    try:
        maj_status(task_status)
    except RuntimeError as e:
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} worker: échec de la publication du status')
        print(e)
        return

    # Renvoie l'objet créé
    return task_status

#-------------------------------------------------------------------------------

class Notification():
    """Mécanisme de communication pour le code utilisateur.

    Cette classe fournit un mécanisme de communication qui permet au code
    python qui implémente une tâche métier d'envoyer des notifications à X4B
    Scenario. Une instance de cette classe est passée à chaque fonction
    utilisateur, pour lui permettre d'invoquer la méthode "notifie".

    """
    
    def __init__(self, task_instance_id, namespace):
        self.task_instance_id = task_instance_id
        self.namespace = namespace
        self.isError = False

    def notifie(self, status, msg, outputs=None, progressPercentage=None):
        """Publie un statut de tâche à destination de X4B Scenario.
        
        La string msg sera affichée par Scenario dans la partie "Message" de
        l'écran de cette tâche, dans le cockpit Scenario.

        """

        self.isError = (status == 'Error')
        
        task_status = post_task_status(self.task_instance_id, status, msg,
                                       outputs=outputs)
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} [{namespace}]: notification {status} envoyée')
        print(json.dumps(task_status, indent=4, ensure_ascii=False))

#-------------------------------------------------------------------------------
# do_work - le coeur du traitement effectué par le worker
#-------------------------------------------------------------------------------

def do_work(mod, namespace, autocomplete=True):
    """Ecoute la file d'attente, récupère des tâches, exécute.

    Cette fonction implémente le coeur du traitement effectué par le worker.
    Dans une boucle infinie, ce code extrait une tâche à la fois depuis la file
    d'attente et exécute la fonction python associé (si on la trouve dans le
    module utilisateur). Si le code utilisateur lève une exception, on notifie
    Scenario en publiant un statut "InError" ; sinon, on publie par défaut le
    status 'Completed'.

    """
    
    while True:
        # Récupère dans la file d'attente la prochaine tâche à exécuter.
        # L'instance de tâche que l'on récupère ici inclut le nom de la
        # fonction à exécuter ainsi que les valeurs des paramètres d'entrée.
        ti = tache_suivante(namespace)
            
        # Quand la file est vide, 'ti' revient à None
        if ti is None:
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f'{dt} [{namespace}]: aucune tâche en attente')
            sleep(polling_interval)
            continue

        # Récupère la tâche dans le module utilisateur
        task_name = ti['catalogTaskDefinitionName']
        if not hasattr(mod, task_name):
            # Il y a une incohérence entre le catalogue qui a été publié, et
            # qui a servi à la création du scenario dans lequel cette tâche
            # s'exécute, et le module python qui est censé l'implémenter : le
            # catalogue annonce une tâche, mais celle-ci ne se trouve pas dans
            # le module importé.
            print('-'*60)
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            task_namespace = ti['catalogTaskDefinitionNamespace']
            msg = f'{dt} [{namespace}]: tâche inconnue: {task_namespace}/{task_name}'
            print(msg)

            # Cette tâche ne peut pas s'exécuter, donc on la met en état
            # d'erreur, au sens de Scenario.
            post_task_status(ti['id'], 'Error', msg)
                
            # Retour à l'écoute de la file
            sleep(polling_interval)
            continue

        # On a trouvé le code de la fonction demandée, on va pouvoir exécuter
        print('-'*60)
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} [{namespace}]: appel de la tâche "{task_name}"')
        print(json.dumps(ti, indent=4))

        # Nettoyage de quelques paramètres cachés (#type)
        inputs = clean_dict(ti['inputData'])

        # Mécanisme de communication pour cette instance de tâche
        notif = Notification(ti['id'], namespace)
        
        # Invocation du code utilisateur: appel de la fonction task_name dans
        # le module utilisateur, avec les paramètres d'entrée reçus dans la
        # description de la tâche, et récupération des sorties produites.
        excep = None
        try:
            outputValues = getattr(mod, task_name)(notif, **inputs)
        except Exception as e:
            excep = e

        # Tracer le retour de la fonction et les sorties
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{dt} [{namespace}]: fin de la tâche "{task_name}"')
        if excep is None:
            s = json.dumps(outputValues, indent=4, ensure_ascii=False)
            print(f'{dt} [{namespace}]: sortie: {s}')
        print(f'#{"-"*60}')

        # Si une exception a été levée dans le code utilisateur, la tâche doit
        # être mise en état d'erreur dans X4B Scenario
        if excep is not None:
            print(excep)
            msg = f'Exception levée par la tâche utilisateur: "{excep}"'
            post_task_status(ti['id'], 'Error', msg)
            
        # Notifie l'état 'Completed' (si autocomplete)
        if excep is None and not notif.isError and autocomplete:
            post_task_status(ti['id'], 'Completed', '', outputs=outputValues)

        # Temps d'attente avant de ré-interroger la file des tâches
        sleep(polling_interval) 

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) not in [2, 3]:
        print(f"""\
Usage: {sys.argv[0]} <namespace> [ <autocomplete true/false> ]

On suppose qu'il existe un module python, avec le même nom que le namespace,
qui peut être trouvé par les mécanismes standard d'import de modules, comme la
variable PYTHONPATH.
""")
        exit(-1)

    # Normalement, le worker se charge de publier un statut 'Completed' quand
    # les tâches se terminent normalement (sans avoir levé d'exceptions). On
    # peut modifier ce comportement par défaut en passant ici autocomplete ===
    # False.
    autocomplete = True
    if len(sys.argv) == 3:
        s = sys.argv[2].lower()
        if s not in ['true', 'false']:
            print(f'"{sys.argv[2]}" booléen attendu')
            exit(-1)
        autocomplete = (s != 'false')

    # Le 'namespace' au sens du catalogue identifie aussi le module utilisateur
    namespace = sys.argv[1]

    # Importe le code utilisateur (avec importlib) et publie son catalogue
    mod = import_module(namespace)
    publication_catalogue(mod.task_definitions(), namespace)

    # Traitement : écoute de la file d'attente, exécution des tâches
    do_work(mod, namespace, autocomplete=autocomplete)

# End of worker.py
#-------------------------------------------------------------------------------
