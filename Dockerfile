FROM python:3.11.0-bullseye

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y libpq-dev gcc python3-dev musl-dev build-essential

RUN pip install pipenv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install  --system
RUN pipenv install

COPY ./blogs_api ./blogs_api

WORKDIR blogs_api

