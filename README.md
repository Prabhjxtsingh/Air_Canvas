# Air Canvas

Draw in the air using just your webcam and your index finger — no mouse, no stylus.

## Setup

```bash
pip install -r requirements.txt
```

(This needs Python 3.8–3.11 for best MediaPipe compatibility. It must run
on your own machine with a webcam — it won't work in a browser or a
headless server.)

## Run

```bash
python air_canvas.py
```

## How to use it

- **Draw**: hold up only your index finger and move it around. A line
  follows your fingertip.
- **Move without drawing**: hold up your index *and* middle finger — this
  is "pen up" mode, so you can reposition without leaving a mark.
- **Pick a color / tool**: while in pen-up mode (index + middle up), move
  your hand up to the toolbar at the top and hover over a color swatch,
  `ERASER`, or `CLEAR`.
- **Keyboard shortcuts**:
  - `q` or `Esc` — quit
  - `c` — clear the canvas
  - `+` / `-` — increase / decrease brush size

## How it works

1. **MediaPipe Hands** detects 21 landmarks on your hand every frame.
2. We check which fingers are extended by comparing fingertip and
   knuckle y-coordinates (x-coordinates for the thumb).
3. The index fingertip's position becomes the "pen." Its path is drawn
   onto a separate canvas layer (not directly onto the webcam frame),
   which is then composited back over the live video each frame — this
   is why strokes persist even as your hand moves away.
4. A small rolling average of recent points smooths out jitter.

## Common tweaks

- **Camera resolution**: change `CAM_WIDTH` / `CAM_HEIGHT` at the top of
  `air_canvas.py`.
- **Brush defaults**: `DEFAULT_BRUSH_SIZE`, `MIN_BRUSH`, `MAX_BRUSH`.
- **Colors**: edit the `COLORS` dictionary to add/remove palette options.
- **Save your drawing**: add a keypress handler that calls
  `cv2.imwrite("drawing.png", canvas)`.

## Troubleshooting

- **Webcam doesn't open**: try changing `cv2.VideoCapture(0)` to `1` or
  `2` if you have multiple cameras.
- **Hand not detected reliably**: make sure you have good, even lighting
  and your whole hand is in frame; lower `min_detection_confidence`
  slightly if needed.
- **Laggy**: lower `CAM_WIDTH`/`CAM_HEIGHT`, or reduce `max_num_hands`
  (already set to 1).
