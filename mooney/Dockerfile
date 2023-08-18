### 1. Get Linux
FROM python:3.10.8-alpine3.17


WORKDIR /home/mooney
COPY requirements.txt requirements.txt 

### 2. Get Java via the package manager
RUN apk update \
&& apk upgrade \
&& apk add --no-cache bash \
&& apk add --no-cache --virtual=build-dependencies unzip \
&& apk add --no-cache curl \
&& apk add --no-cache openjdk8-jre

### 3. Get Python, PIP

RUN apk add --no-cache python3 \
&& python3 -m ensurepip \
&& pip3 install --upgrade pip setuptools \
&& rm -r /usr/lib/python*/ensurepip && \
if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
rm -r /root/.cache

#WEIRD REQUIREMENTS FOR LXML
RUN apk add --update --no-cache g++ gcc libxslt-dev

#CREATE VENV, INSTALL REQUIREMENTS, EXPLICITLY INSTALL GUNICORN
RUN python3 -m venv venv
RUN venv/bin/pip3 install -r requirements.txt
RUN venv/bin/pip3 install gunicorn

COPY app app
COPY migrations migrations
COPY mooney.py config.py boot.sh ./
RUN chmod +x boot.sh
RUN cp boot.sh /.

ENV FLASK_APP mooney.py

###
#### OPTIONAL : 4. SET JAVA_HOME environment variable, uncomment the line below if you need it
#ENV JAVA_HOME="/usr/lib/jvm/java-1.8-openjdk"

####

EXPOSE 5000     
ENTRYPOINT ["./boot.sh"]