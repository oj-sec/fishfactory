# Note that this exists purely to facilitate building the kitprocessor (processor) binary with a GLIBC version compatible with the parent images
# docker image build -t kitprocessor_containerized_build .
# docker run kitprocessor_containerized_build:latest sleep infinity
# docker cp {container_id}:/app/target/release/kitprocessor .

# base image
FROM rust:1.68-bullseye

# copy the project 
COPY . /app

# switch working directory
WORKDIR /app

# install dependencies
RUN cargo build --release

CMD ["./target/release/fileprocessor"]

# set entrypoint & run
#ENTRYPOINT [ "ldd" ]
#CMD ["--version" ]
