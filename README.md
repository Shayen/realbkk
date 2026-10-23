# REAL Bangkok website

This is a static website; it has no build step, package installation, backend, or framework dependency.

## Run locally

From the repository root, start Python's standard-library web server:

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000/> and stop the server with `Ctrl+C`.

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
