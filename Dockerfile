# start by pulling the python image
FROM python:3.9-alpine

EXPOSE 5000/tcp

# copy the requirements file into the image
COPY ./requirements.txt pengin-pie/requirements.txt

# switch working directory
WORKDIR /pengin-pie

# install the dependencies and packages in the requirements file
RUN pip3 install -r requirements.txt

# copy every content from the local file to the image
COPY . /pengin-pie


CMD ["flask", "run" ,"--host=0.0.0.0"]