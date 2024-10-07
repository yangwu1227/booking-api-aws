FROM python:3.11.10-slim-bookworm AS python-base

# Prevents Python from creating pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    # Ensure python I/O is unbuffered so that log messages are flushed to the stream
    PYTHONUNBUFFERED=1 \
    # PDM version
    PDM_VERSION=2.18.2 \
    # Disable pdm update check
    PDM_CHECK_UPDATE=0 \
    # Environment and testing are set to prod and 0 respectively
    ENVIRONMENT=prod \
    TESTING=0 \
    # Set the home directory and app home directory
    USER=app_user \
    USER_GROUP=app_group 

ENV HOME=/home/$USER \
    # Working directory inside the container is set to 'project' under the home directory of the app user
    PROJECT_ROOT_PATH=/home/$USER/project

# Create an unprivileged user and group to run the application
RUN addgroup --system $USER_GROUP && \
    adduser --system --ingroup $USER_GROUP $USER && \
    mkdir -p $HOME

FROM python-base AS build-stage

# Install pdm 
WORKDIR $PROJECT_ROOT_PATH
# Copy project toml and lock files onto the container
COPY pyproject.toml pdm.lock ./
# 1. --no-editable: all packages to be installed in non-editable mode
# 2. --check: validate whether the lock is up to date
RUN pip install pdm==$PDM_VERSION && pdm install --check --no-editable -G cloud

FROM python-base AS production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy just .venv from the build stage
COPY --from=build-stage $PROJECT_ROOT_PATH/.venv $PROJECT_ROOT_PATH/.venv
ENV PATH=$PROJECT_ROOT_PATH/.venv/bin:$PATH
WORKDIR $PROJECT_ROOT_PATH
COPY ./ ./

# Change the owner of all the files under project to the app user
RUN chown -R $USER:$USER_GROUP $PROJECT_ROOT_PATH
USER $USER

# To be overridden by the ecs task definition
CMD ["/bin/bash"]
