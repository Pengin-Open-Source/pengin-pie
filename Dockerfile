FROM python:3.9-alpine

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

#port
EXPOSE 5000

COPY . /app

CMD ["flask","run","--host=0.0.0.0"]