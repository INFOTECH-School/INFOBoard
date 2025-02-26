# --------------------- Client Build Stage ---------------------
FROM node:lts AS client_builder

WORKDIR /srv

RUN apt update \
    && apt upgrade -y \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && npm i -g -f pnpm

RUN groupadd -r builder \
    && useradd --no-log-init -r -m -g builder builder \
    && chown builder:builder /srv

COPY --chown=builder:builder ./client/package.json ./client/pnpm-lock.yaml ./

USER builder

RUN pnpm install --frozen-lockfile

COPY ./client/ ./

RUN pnpm run build

# --------------------- Wheel Build Stage ---------------------
FROM python:3.10-slim AS wheel_builder

WORKDIR /opt

RUN apt update \
    && apt upgrade -y \
    && apt install -y --no-install-recommends gcc libc-dev libmariadb-dev libpq-dev \
    && apt autoremove -y && apt autoclean && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN groupadd -r builder \
    && useradd --no-log-init -r -m -g builder builder \
    && chown builder:builder /opt

USER builder

COPY --chown=builder:builder ./wheels.requirements.txt .

RUN mkdir -p wheels
RUN pip install --no-cache-dir -U pip setuptools wheel
RUN pip wheel -r wheels.requirements.txt -w ./wheels/

# --------------------- Final Stage ---------------------
FROM python:3.10-slim AS ltiapp

WORKDIR /srv

# Install Python dependencies
RUN pip install --no-cache-dir -U pip setuptools wheel

RUN apt update \
    && apt upgrade -y \
    && apt install -y --no-install-recommends gosu libmariadb3 libpq5 \
    && apt autoremove -y && apt autoclean && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=wheel_builder /opt/wheels /opt/wheels

COPY ./backends.requirements.txt .
RUN pip install --no-cache-dir -r backends.requirements.txt --find-links /opt/wheels

# Create an unprivileged user and allow access to the data folder
RUN groupadd -r ltiapp \
    && useradd --no-log-init -r -m -g ltiapp ltiapp \
    && mkdir data && chown -R ltiapp:ltiapp data

# Create media directory and set permissions so that the ltiapp user can write profile images
RUN mkdir -p /srv/media/profile_images && chown -R ltiapp:ltiapp /srv/media

# Copy client assets built from the previous stage
COPY --from=client_builder --chown=ltiapp:ltiapp /srv/dist/ /srv/client/dist/

# Copy the rest of the application code
COPY --chown=ltiapp:ltiapp . .

ENV DJANGO_SETTINGS_MODULE=draw.test_settings

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["draw.asgi", "--bind=0.0.0.0:8000"]

EXPOSE 8000

LABEL maintainer="maciej.jakubowicz@icloud.com"
LABEL org.opencontainers.image.source="https://github.com/INFOTECH-School/INFOBoard"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.description="Web application for creating and managing interactive boards based on Excalidraw and Django."
