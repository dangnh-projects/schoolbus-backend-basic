FROM python:3.6.4-alpine3.7
RUN apk --update add build-base mysql-dev bash jpeg-dev zlib-dev libressl-dev

ENV PYTHONUNBUFFERED 1

RUN mkdir /www
COPY . /www/

WORKDIR /www

RUN rm -rf release
RUN mkdir -p logs
RUN chmod a+x entry.sh
RUN pip install -r  ischoolbus/requirements.txt

COPY cron/* /etc/crontabs/
RUN chmod 0644 /etc/crontabs/send_email.cron
RUN crontab /etc/crontabs/send_email.cron

