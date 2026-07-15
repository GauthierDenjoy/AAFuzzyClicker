# AAFuzzyClicker

Capture a button on screen, then let it auto-click that button every few
seconds. All saved buttons are searched and clicked.

## Run

Double-click `AAFuzzyClicker.bat`. The **first time**, it asks to install what it
needs (Python if missing, plus `opencv-python` and `pillow`); press **Y** to
accept. After that, every launch opens the app directly.

To reinstall, delete the `.installed` file next to the `.bat`.

## Use

1. **Capture button** — the screen dims; drag a box around the button and
   release (Esc or right-click to cancel). It's saved as a PNG in `buttons`.
2. Set the interval in seconds.
3. **Start** — every N seconds the screen is scanned and each saved button
   found is clicked. **Stop** (or close the window) to end.
4. **Delete** removes the selected saved button.

Matching is pixel-based: if the display scaling, theme, or button look
changes, recapture it. Adjust `THRESHOLD` in `aafuzzyclicker.py` if it misses
(lower) or misclicks (raise).

## License & disclaimer

Copyright (c) 2026 Gauthier DENJOY. Released under the MIT License — see
[`LICENSE`](LICENSE). Please read [`DISCLAIMER.md`](DISCLAIMER.md) for
responsible-use terms before running it.
