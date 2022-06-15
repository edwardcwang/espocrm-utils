FROM ubuntu:22.04
MAINTAINER Edward Wang <edward.c.wang@compdigitec.com>

# Basic tools & dependencies
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Toronto
RUN apt-get update && apt-get -y install tzdata
RUN apt-get update && apt-get install -y dumb-init vim wget htop wget curl unzip git

# Python
RUN apt-get update && apt-get install -y --no-install-recommends python3-dateutil python3-pip python3-requests
RUN pip3 install yacron

# Entrypoint
WORKDIR /opt
COPY *.py /opt/
COPY crontab.yml /opt/
COPY run_reminders.sh /opt/
RUN chown -R www-data:www-data *

USER www-data

ENTRYPOINT ["dumb-init"]
CMD ["/opt/run_reminders.sh"]
