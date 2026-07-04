FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY index.js .
CMD ["node", "index.js"]
