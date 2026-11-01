# REAL Bangkok website

This is a static website; it has no build step, package installation, backend, or framework dependency.

## Run locally

From the repository root, start Python's standard-library web server:

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000/> and stop the server with `Ctrl+C`.

## Run with Docker Compose

Requirements: Docker Engine and the Docker Compose plugin.

Build the Nginx image and start the site on loopback:

```sh
docker compose -f compose.yaml -f compose.local.yaml up --build -d
```

Open <http://localhost:8080/>. Stop the site with:

```sh
docker compose -f compose.yaml -f compose.local.yaml down
```

The local port defaults to `8080`; override it with `WEB_PORT=8081` before the
Compose command. `IMAGE_TAG` defaults to `latest` and changes the locally built
image tag, for example `IMAGE_TAG=dev docker compose -f compose.yaml build`.
This does not publish an image to a registry.

### Deploy with Dokploy

1. Create a Git-backed application in standard Docker Compose mode, using
   `compose.yaml`. Do not use Docker Stack/Swarm mode or `compose.local.yaml`.
2. Deploy the `web` service and configure its internal container port as `80`.
   Production Compose exposes this port to the Docker network only; it does not
   publish a host port.
3. In Dokploy's Domains settings, attach both `www.realbkk.com` and
   `realbkk.com` to `web` on port `80` and enable HTTPS/TLS. Dokploy terminates
   public TLS; Nginx redirects apex requests to `www`.
4. Redeploy after adding or changing domains. Optionally set `IMAGE_TAG` in the
   application environment to choose the local Compose image tag.

The Compose image tag is local to the build. This setup does not push to GHCR
or another registry and requires no registry credentials.

## Locale routes

- English pages use the root paths: `/`, `/photos.html`, `/led-wall.html`, and `/vp-sim.html`.
- Thai pages use `/th/`: `/th/`, `/th/photos.html`, `/th/led-wall.html`, and `/th/vp-sim.html`.
- Japanese pages use `/ja/`: `/ja/`, `/ja/photos.html`, `/ja/led-wall.html`, and `/ja/vp-sim.html`.

The language selector keeps the current page when switching locales.

## Tools

The LED Wall Configurator previews wall dimensions and resolution from its pixel pitch, cabinet, size, and joint-angle settings. Its weight, power, and port figures are rough estimates; verify them against manufacturer specifications.

The Virtual Production Simulator uses an LED wall configuration with uploaded, pasted, or sample imagery and adjustable camera, lens, and sensor settings. It provides studio and camera views and can save the current camera frame.

## Tests

Run the static route, metadata, content, and discoverability checks with Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```
