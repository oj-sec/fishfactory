# docker image build -t fishfactory .

# base image - must be python3.10 due to greenlet make errors
FROM mcr.microsoft.com/playwright/python:v1.37.0-jammy

# Update
RUN apt-get update -y
RUN apt-get install -y python3 pip

# copy the pip requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install python dependencies with pip
RUN pip install -r requirements.txt

# copy project to the image
COPY . /app

# set entrypoint & run
ENTRYPOINT [ "python" ]
CMD ["fishfactory_api.py" ]