FROM python:3-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mail2divera.py ./

ENV IMAP_SERVER ""
ENV IMAP_USER ""
ENV IMAP_PASS ""
ENV MAIL_FROM ""
ENV MAIL_MAX_AGE 600
ENV FETCH_INTERVAL 1
ENV DIVERA_ACCESSKEY ""

USER www-data

CMD [ "python", "./mail2divera.py" ]
