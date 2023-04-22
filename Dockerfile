# Container image that runs your code
FROM python:bullseye

RUN apt-mark hold git
RUN apt-mark hold git-man

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY entrypoint.sh /entrypoint.sh
COPY oldabe/__init__.py /oldabe/__init__.py
COPY oldabe/money_in.py /oldabe/money_in.py
COPY oldabe/money_out.py /oldabe/money_out.py
COPY oldabe/models.py /oldabe/models.py

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/entrypoint.sh"]
