# md_toc.py - Markdown table of contents

import re

s = """\
* Introduction
  * Software Version
  * Documentation Overview
* General Description and Concepts
  * Scenario
  * Workers and Integration Endpoints
  * The Worker API
  * User Interaction
* Tasks
  * Overview
  * The Task Catalog
  * Namespaces
  * Task parameters
    * Input parameters
	* Output parameters
  * Task aspects
    * Three different aspects of tasks
	* Tasks in the scenario lifecycle
  * Task versions
* Scenario
  * Scenario Definition
    * Task Pipelines
	* Scenario Invariants
	* Scenario Re-Runs
  * Scenario Versions
  * Workflow Task Definition
  * Scenario Instance
  * Task Instance
* Worker
  * Retrieving tasks
  * Returning information
* User roles and rights
  * User management
  * Profiles
* SSO Authentication
* Workspaces
"""
for line in s.splitlines():
    m = re.match(r'(\s*\* )(.*)', line)
    prefix = m.group(1)
    txt = m.group(2)
    print(f'{prefix}[{txt}](#{txt.replace(" ", "-")})')