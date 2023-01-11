# docker image build -t 0jsec/fishfactory

# base image
FROM python:3.12.0a3-bullseye

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
CMD ["fishfactory_API.py" ]