# Use an official Python runtime as a parent image
FROM python:3.7-slim

# Set environment variables to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Update package list and install required dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    apt-utils \
    procps \
    build-essential \
    python3-dev \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install numpy
RUN python3.7 -m pip install --no-cache-dir numpy

# Copy the local tmhmm.py directory into the Docker image
COPY tmhmm.py /tmhmm.py

# Install tmhmm.py from the local copy
WORKDIR /tmhmm.py
RUN python3 setup.py install
