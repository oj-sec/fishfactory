# docker image build -t 0jsec/kitprocessor_containerized_build

# base image
FROM rust:1.68-bullseye

# copy the project 
COPY . /app

# switch working directory
WORKDIR /app

# install dependencies
RUN cargo build --release

CMD ["./target/release/kitprocessor"]

# set entrypoint & run
#ENTRYPOINT [ "ldd" ]
#CMD ["--version" ]