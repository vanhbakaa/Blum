FROM python:3.11.10-alpine3.20 AS python-base
FROM node:alpine AS node-base

FROM python-base AS final
# Copy Node from the node-base stage
COPY --from=node-base /usr/local/bin/node /usr/local/bin/
COPY --from=node-base /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-base /usr/local/bin/npm /usr/local/bin/
COPY --from=node-base /usr/local/bin/npx /usr/local/bin/

# Install other dependencies
RUN apk add --no-cache gcc musl-dev

WORKDIR app/

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install --no-warn-script-location --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py", "-a", "1", "-m", "y"]
