FROM python:3.13.0-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./req.txt /usr/src/app/req.txt
RUN pip install -r req.txt

COPY . /usr/src/app
