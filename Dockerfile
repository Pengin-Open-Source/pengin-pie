# start by pulling the python image
FROM python:3.8-alpine

# copy the requirements file into the image
COPY ./requirements.txt /pengin-pie/requirements.txt

# switch working directory
WORKDIR /pengin-pie

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

EXPOSE 5000

# copy every content from the local file to the image
COPY . /pengin-pie

# configure the container to run in an executed manner
# ENTRYPOINT [ "python" ]

CMD ["flask","run","--host=0.0.0.0"]