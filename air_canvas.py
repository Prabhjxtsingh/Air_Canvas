"""
Air Canvas - Draw in the air using your webcam and finger movements.

How it works
------------
- Uses MediaPipe to detect your hand and find your index fingertip.
- Tracks the fingertip position across frames and draws lines between
  consecutive points onto a persistent canvas layer.
- Gesture rules (based on which fingers are extended):
    * Only INDEX finger up      -> Drawing mode (pen down)
    * INDEX + MIDDLE fingers up -> Selection / hover mode (pen up, move freely)
    * All 4 fingers up          -> Hover over the on-screen buttons to
                                     pick a color, change brush size, or clear
- A color palette bar is drawn at the top of the window. Move your hand
  (in selection mode) over a color swatch to pick it, or over "CLEAR" to
  wipe the canvas, or over "ERASER" to erase.

Controls (keyboard)
--------------------
- 'q' or ESC : quit
- 'c'        : clear canvas
- '+' / '-'  : increase / decrease brush size

Requirements
------------
pip install opencv-python mediapipe numpy
"""

import cv2
import numpy as np
import mediapipe as mp
from collections import deque

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
CAM_WIDTH, CAM_HEIGHT = 1280, 720

COLORS = {
    "BLUE":   (255, 0, 0),
    "GREEN":  (0, 255, 0),
    "RED":    (0, 0, 255),
    "YELLOW": (0, 255, 255),
    "PURPLE": (255, 0, 255),
}
ERASER_COLOR = (0, 0, 0)  # matches canvas background so it "erases"

DEFAULT_BRUSH_SIZE = 6
ERASER_SIZE = 40
MIN_BRUSH, MAX_BRUSH = 2, 40

SMOOTHING_POINTS = 5  # for slight motion smoothing


# --------------------------------------------------------------------------
# UI: top toolbar layout
# --------------------------------------------------------------------------
def build_toolbar(width):
    """Returns a list of (label, x1, y1, x2, y2, color_or_None) button rects."""
    buttons = []
    button_w = width // (len(COLORS) + 2)  # + CLEAR + ERASER
    x = 0
    h = 80

    buttons.append(("CLEAR", x, 0, x + button_w, h, (50, 50, 50)))
    x += button_w

    for name, color in COLORS.items():
        buttons.append((name, x, 0, x + button_w, h, color))
        x += button_w

    buttons.append(("ERASER", x, 0, x + button_w, h, (200, 200, 200)))

    return buttons


def draw_toolbar(frame, buttons, active_color, brush_size):
    for label, x1, y1, x2, y2, color in buttons:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        text_color = (255, 255, 255) if sum(color) < 400 else (0, 0, 0)
        # Highlight the active swatch
        if (label != "CLEAR") and (
            (label == "ERASER" and active_color == ERASER_COLOR)
            or (label in COLORS and active_color == COLORS.get(label))
        ):
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 4)
        cv2.putText(frame, label, (x1 + 10, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2, cv2.LINE_AA)

    cv2.putText(frame, f"Brush: {brush_size}px", (frame.shape[1] - 180, h_text_y(frame)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)


def h_text_y(frame):
    return 110


def point_in_button(px, py, button):
    _, x1, y1, x2, y2, _ = button
    return x1 <= px <= x2 and y1 <= py <= y2


# --------------------------------------------------------------------------
# Hand tracking helpers
# --------------------------------------------------------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

FINGER_TIPS = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky


def fingers_up(hand_landmarks, handedness_label):
    """Returns a list of 5 booleans: [thumb, index, middle, ring, pinky]."""
    lm = hand_landmarks.landmark
    fingers = []

    # Thumb: compare x-coordinates (flips depending on hand)
    if handedness_label == "Right":
        fingers.append(lm[4].x < lm[3].x)
    else:
        fingers.append(lm[4].x > lm[3].x)

    # Other 4 fingers: tip above the pip joint (lower y = higher on screen)
    for tip_id in [8, 12, 16, 20]:
        pip_id = tip_id - 2
        fingers.append(lm[tip_id].y < lm[pip_id].y)

    return fingers


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------
def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    if not cap.isOpened():
        print("Error: could not open webcam.")
        return

    canvas = None
    buttons = None

    active_color = COLORS["BLUE"]
    brush_size = DEFAULT_BRUSH_SIZE

    prev_point = None
    point_history = deque(maxlen=SMOOTHING_POINTS)

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    ) as hands:

        while True:
            success, frame = cap.read()
            if not success:
                print("Error: failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)  # mirror for natural interaction
            h, w, _ = frame.shape

            if canvas is None:
                canvas = np.zeros((h, w, 3), dtype=np.uint8)
                buttons = build_toolbar(w)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            drawing_now = False

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                handedness_label = "Right"
                if results.multi_handedness:
                    handedness_label = results.multi_handedness[0].classification[0].label

                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )

                up = fingers_up(hand_landmarks, handedness_label)
                thumb, index, middle, ring, pinky = up

                index_tip = hand_landmarks.landmark[8]
                ix, iy = int(index_tip.x * w), int(index_tip.y * h)

                # --- Selection mode: index + middle up, hovering over toolbar ---
                if index and middle and not ring and not pinky:
                    prev_point = None
                    cv2.circle(frame, (ix, iy), 12, (255, 255, 255), 2)
                    if iy < 80:
                        for btn in buttons:
                            if point_in_button(ix, iy, btn):
                                label = btn[0]
                                if label == "CLEAR":
                                    canvas[:] = 0
                                elif label == "ERASER":
                                    active_color = ERASER_COLOR
                                    brush_size = ERASER_SIZE
                                elif label in COLORS:
                                    active_color = COLORS[label]
                                    brush_size = DEFAULT_BRUSH_SIZE

                # --- Drawing mode: only index finger up ---
                elif index and not middle and not ring and not pinky:
                    drawing_now = True
                    point_history.append((ix, iy))
                    smooth_x = int(np.mean([p[0] for p in point_history]))
                    smooth_y = int(np.mean([p[1] for p in point_history]))

                    cv2.circle(frame, (smooth_x, smooth_y), brush_size // 2 + 2,
                               active_color if active_color != ERASER_COLOR else (255, 255, 255),
                               -1)

                    if prev_point is not None and smooth_y > 80:
                        cv2.line(canvas, prev_point, (smooth_x, smooth_y),
                                 active_color, brush_size)
                    prev_point = (smooth_x, smooth_y)

                else:
                    prev_point = None
                    point_history.clear()
            else:
                prev_point = None
                point_history.clear()

            # Merge canvas onto the frame
            gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
            mask_inv = cv2.bitwise_not(mask)
            frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
            canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask)
            combined = cv2.add(frame_bg, canvas_fg)

            draw_toolbar(combined, buttons, active_color, brush_size)

            mode_text = "DRAWING" if drawing_now else "HOVER / IDLE"
            cv2.putText(combined, mode_text, (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.imshow("Air Canvas", combined)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('c'):
                canvas[:] = 0
            elif key == ord('+') or key == ord('='):
                brush_size = min(MAX_BRUSH, brush_size + 2)
            elif key == ord('-'):
                brush_size = max(MIN_BRUSH, brush_size - 2)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
