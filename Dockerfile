FROM python:3.7 AS build
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Stup the virtualenv
RUN python3 -m venv /venv

# Install Python and external dependencies, including headers and GCC
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext build-essential \
        libxml2-dev libxslt1-dev libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

# Copy and install reqs first to speed up future builds
ADD ./requirements.txt /app/requirements/requirements.txt
RUN /venv/bin/pip install -r /app/requirements/requirements.txt

# Now copy over our app for install fun
ADD . /app
RUN /venv/bin/pip install /app
WORKDIR /app

# App Image
FROM python:3.7 AS app
COPY --from=build /venv /venv

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV AWS_DEFAULT_REGION=us-east-1
ENV PATH="/venv/bin:$PATH"
ENV CONFIGFILE=/app/config.yml
ENV MONITORCONFIGFILE=/app/monitors.yml
ENV DATAPATH=/tmp/instance-data.yml

RUN apt-get -qy update \
  && apt-get -qy upgrade \
  && rm -rf /var/cache/apt/* /var/lib/apt/lists/*

RUN \
  groupadd \
    --gid 5000 \
    app \
  && useradd \
    --home-dir /app \
    --create-home \
    --uid 5000 \
    --gid 5000 \
    --shell /bin/bash \
    --skel /dev/null \
    --no-log-init \
    app

CMD ["aws-aware"]
WORKDIR /app
COPY config/default-config.yml /app/config.yml
COPY config/default-monitor.yml /app/monitors.yml
RUN chown -R app.app /app
USER app