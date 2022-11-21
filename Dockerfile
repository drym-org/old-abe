# Container image that runs your code
FROM python:bullseye

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY entrypoint.sh /entrypoint.sh
COPY money-in.py /github/workspace/money-in.py
COPY money-out.py /github/workspace/money-out.py

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/entrypoint.sh"]

