from python:3.9-alpine
run pip install requests

# Python modules
env PYTHONUNBUFFERED 1

# main code
add worker.py sample.py /
entrypoint ["python", "/worker.py", "sample"]
