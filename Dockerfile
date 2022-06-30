FROM python:3.9-alpine

COPY ./requirements.txt /pengin-pie/requirements.txt

WORKDIR /pengin-pie

RUN pip install -r requirements.txt

#port
EXPOSE 5000

COPY . /app

CMD ["flask","run","--host=0.0.0.0"]