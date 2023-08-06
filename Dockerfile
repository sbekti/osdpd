FROM python:3.11 as builder

WORKDIR /app

RUN apt update && \
    apt install -y \
        cmake \
        python3 \
        python3-pip \
        python3-dev \
        libssl-dev \
        doxygen

RUN git clone --recurse-submodules https://github.com/goToMain/libosdp.git && \
    cd libosdp && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    cd python && \
    python3 setup.py bdist_wheel


FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/libosdp/build/python/dist/osdp-2.3.0-cp311-cp311-linux_aarch64.whl .

RUN mv osdp-2.3.0-cp311-cp311-linux_aarch64.whl osdp-2.3.0-cp311-cp311-linux_armv7l.whl && \
    pip install osdp-2.3.0-cp311-cp311-linux_armv7l.whl

ADD src/* .

CMD ["python", "./main.py"]