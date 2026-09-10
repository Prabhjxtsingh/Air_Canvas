# Air Canvas

Draw in the air using your webcam and your index finger in a Django web app.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser and allow camera access. The
browser runs hand tracking locally; Django serves the interface and stores
saved PNGs in `media/`.

## How to use it

- **Draw**: hold up only your index finger and move it around. A line
  follows your fingertip.
- **Move without drawing**: hold up your index *and* middle finger — this
  is "pen up" mode, so you can reposition without leaving a mark.
- **Pick a color / tool**: raise your index and middle fingers, then hover
  over the top toolbar to choose a color, `ERASER`, or `CLEAR`.
- **Keyboard shortcuts**:
  - `s` — save and download the drawing as `drawing.png`
  - `c` — clear the canvas
  - `+` / `-` — increase / decrease brush size

## How it works

1. The browser camera feed is processed by MediaPipe Hands from a CDN.
2. The index fingertip becomes the pen and its path is drawn onto a canvas.
3. Django serves the page and accepts PNG data at `/api/save/`.

## Common tweaks

- **Brush defaults**: edit the controls in `static/aircanvas/app.js`.
- **Colors**: edit the swatches in `aircanvas/templates/aircanvas/canvas.html`.
- **Saved files**: server copies are written to the ignored `media/` folder.

## Troubleshooting

- **Webcam doesn't open**: check browser camera permissions and close other
  apps that may already be using the camera.
- **Hand not detected reliably**: make sure you have good, even lighting
  and your whole hand is in frame; lower `min_detection_confidence`
  slightly if needed.
- **Laggy**: close other camera-heavy tabs or reduce the camera dimensions in
  `static/aircanvas/app.js`.
