# Handcast

Handcast recognizes static hand poses from a webcam in real time. It uses
MediaPipe Hand Landmarker to track hands, compares their joint angles, finger
spread, and pinch distances against gesture templates, and reports stabilized
gesture start/end events in the console. An OpenCV window displays the camera
image, hand skeletons, matching scores, and recording status.

Gesture templates can be recorded while the app is running or edited in
`config/gestures.json`. Runtime options are in `config/settings.json`.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- A webcam and a graphical desktop session

The MediaPipe hand-landmarker model is included at
`models/hand_landmarker.task`. If it is missing, Handcast downloads it when
tracking starts.

## Install and run

From the project directory:

```powershell
uv sync
uv run handcast
```

The application opens a window named **Tracking**. Press **Esc** to quit.
Press **1** to record a gesture for the left hand, or **2** for the right
hand. After the configured countdown, hold the pose steady while samples are
collected. A successful recording is named `gesture_1`, `gesture_2`, and so
on, and is saved to the configured gestures file.

On startup, Handcast reads `config/settings.json`. If the file is absent, it
creates it with the defaults described below. The gesture-library path is
resolved relative to the project root unless it is absolute. Invalid gesture
entries are skipped with a console message.

## Runtime settings (`config/settings.json`)

All settings are optional: omitted values use the defaults shown below.
Unknown keys are ignored with a console warning. Numeric values should be
chosen within the normal operating ranges noted here; the application does
not validate every range.

| Section      | Setting                     |                  Default | Description                                                                                                                                                        |
| ------------ | --------------------------- | -----------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `camera`     | `index`                     |                      `0` | OpenCV camera device index. Change this to select another connected camera.                                                                                        |
| `camera`     | `mirror`                    |                   `true` | Flip captured frames horizontally before display and tracking, as in a mirror view.                                                                                |
| `tracking`   | `max_hands`                 |                      `2` | Maximum number of hands MediaPipe should track.                                                                                                                    |
| `tracking`   | `min_detection`             |                    `0.5` | Minimum hand-detection confidence (normally from `0.0` to `1.0`). Higher values are stricter.                                                                      |
| `tracking`   | `min_presence`              |                    `0.5` | Minimum hand-presence confidence for a detected hand (normally from `0.0` to `1.0`).                                                                               |
| `tracking`   | `min_tracking`              |                    `0.5` | Minimum confidence for continuing to track a hand (normally from `0.0` to `1.0`).                                                                                  |
| `tracking`   | `swap_sides`                |                   `true` | Invert MediaPipe's handedness result when assigning `left` and `right`. This is useful with mirrored camera input; change it if displayed hand sides are reversed. |
| `queues`     | `frames`                    |                      `2` | Maximum buffered camera frames. When full, the oldest frame is dropped to favor recent frames and lower latency.                                                   |
| `queues`     | `tracking`                  |                      `2` | Maximum buffered tracking results; the oldest result is dropped when full.                                                                                         |
| `queues`     | `gestures`                  |                      `2` | Maximum buffered gesture results; the oldest result is dropped when full.                                                                                          |
| `matching`   | `threshold`                 |                    `0.8` | Default minimum match score for templates without their own `threshold`. Scores range from `0` to `1`; higher thresholds require closer matches.                   |
| `matching`   | `angle_tolerance_deg`       |                   `45.0` | Per-feature comparison tolerance, in degrees, for finger joint angles. Larger tolerances make angle differences matter less.                                       |
| `matching`   | `spread_tolerance_deg`      |                   `30.0` | Per-feature comparison tolerance, in degrees, for the spread between neighboring fingers.                                                                          |
| `matching`   | `pinch_tolerance`           |                    `0.6` | Per-feature comparison tolerance for normalized thumb-to-fingertip distances.                                                                                      |
| `matching`   | `use_orientation`           |                  `false` | Include palm-facing direction and hand direction in the score. Disable this if a pose should match regardless of how the palm is oriented.                         |
| `matching`   | `orientation_tolerance_deg` |                   `40.0` | Angular tolerance, in degrees, for each orientation vector when `use_orientation` is enabled.                                                                      |
| `matching`   | `exclusive_per_hand`        |                   `true` | Allow at most the highest-scoring passing template to pass for each hand on a frame.                                                                               |
| `stabilizer` | `min_frames`                |                      `4` | Consecutive passing frames required before a gesture becomes active and emits a `started` event.                                                                   |
| `stabilizer` | `release_frames`            |                      `3` | Consecutive non-passing frames required before an active gesture emits an `ended` event.                                                                           |
| `stabilizer` | `cooldown_ms`               |                    `300` | Minimum delay after a gesture ends before that same gesture can start again, in milliseconds.                                                                      |
| `recording`  | `countdown_s`               |                    `3.0` | Seconds between requesting a recording and beginning to collect samples.                                                                                           |
| `recording`  | `samples`                   |                     `15` | Target number of valid hand samples. Recording completes as soon as this many are collected.                                                                       |
| `recording`  | `min_samples`               |                      `8` | Minimum samples needed to save a recording if the sampling timeout expires before reaching `samples`.                                                              |
| `recording`  | `sampling_timeout_s`        |                    `3.0` | Maximum time, in seconds, to collect samples after the countdown.                                                                                                  |
| `recording`  | `min_confidence`            |                    `0.8` | Minimum MediaPipe confidence required for a hand sample to be included (normally from `0.0` to `1.0`).                                                             |
| `recording`  | `message_s`                 |                    `4.0` | Seconds to show the success or retry message after recording ends.                                                                                                 |
| `paths`      | `gestures`                  | `"config/gestures.json"` | Gesture-library JSON path. Relative paths are resolved from the project root; absolute paths are used as given.                                                    |

### Matching behavior

For each template on the same hand side, Handcast compares the measured
features to the template. The score starts at `1.0` and decreases with
normalized feature differences; a score at or above the template's
`threshold` (or `matching.threshold` when the template threshold is `null`)
passes. The angle, spread, and pinch tolerances normalize their corresponding
feature differences. If orientation matching is enabled, palm-normal and
hand-direction differences are included too.

## Gesture templates (`config/gestures.json`)

The file is a JSON object with a `version` number and a `gestures` array. The
current writer saves `version: 1`. Each array item describes one pose:

| Field         | Required | Description                                                                                                                                                                                                                        |
| ------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | Yes      | Gesture name shown in the overlay and console events.                                                                                                                                                                              |
| `side`        | Yes      | Hand side for this template: `"left"` or `"right"`. A template is only compared with a hand assigned to that side.                                                                                                                 |
| `samples`     | No       | Number of samples used to record the template. Informational metadata; it does not affect matching. Defaults to `1` when omitted.                                                                                                  |
| `threshold`   | No       | Per-template minimum score from `0` to `1`. Use `null` or omit it to use `matching.threshold` from `settings.json`.                                                                                                                |
| `ignore`      | No       | Array of feature-name tokens to exclude from scoring. Tokens match whole underscore-separated parts of feature names; for example, `"thumb"` excludes thumb angles and spreads that involve the thumb. Defaults to an empty array. |
| `features`    | Yes      | Object containing every feature listed below, with its numeric template value. All features are required when loading a template.                                                                                                  |
| `orientation` | No       | Object containing optional `palm_normal` and `hand_dir` 3D vectors. Missing vectors default to `[0, 0, 0]`. Used only when `matching.use_orientation` is true.                                                                     |

The required `features` keys are:

- **Finger joint angles (degrees):** For each of `thumb`, `index`, `middle`,
  `ring`, and `pinky`: `<finger>_base`, `<finger>_mid`, and `<finger>_tip`.
  Example: `index_base`, `index_mid`, `index_tip`.
- **Neighboring-finger spread (degrees):** `spread_thumb_index`,
  `spread_index_middle`, `spread_middle_ring`, and `spread_ring_pinky`.
- **Thumb-to-fingertip distances (normalized by palm size):** `pinch_index`,
  `pinch_middle`, `pinch_ring`, and `pinch_pinky`. Smaller values mean the
  thumb is closer to that fingertip.

`ignore` tokens are matched against underscore-separated parts of those
feature keys. Useful tokens include finger names (`thumb`, `index`, `middle`,
`ring`, `pinky`) and parts such as `spread`, `pinch`, `base`, `mid`, and
`tip`. For example, `["pinky"]` ignores pinky angles and the spread features
that include the pinky. A token can exclude more than one feature.

An example template entry (the `features` object must include all 23 keys):

```json
{
  "name": "example_pose",
  "side": "left",
  "samples": 15,
  "threshold": null,
  "ignore": [],
  "features": {
    "thumb_base": 20.0,
    "thumb_mid": 20.0,
    "thumb_tip": 20.0,
    "index_base": 20.0,
    "index_mid": 20.0,
    "index_tip": 20.0,
    "middle_base": 20.0,
    "middle_mid": 20.0,
    "middle_tip": 20.0,
    "ring_base": 20.0,
    "ring_mid": 20.0,
    "ring_tip": 20.0,
    "pinky_base": 20.0,
    "pinky_mid": 20.0,
    "pinky_tip": 20.0,
    "spread_thumb_index": 20.0,
    "spread_index_middle": 20.0,
    "spread_middle_ring": 20.0,
    "spread_ring_pinky": 20.0,
    "pinch_index": 1.0,
    "pinch_middle": 1.0,
    "pinch_ring": 1.0,
    "pinch_pinky": 1.0
  },
  "orientation": {
    "palm_normal": [0.0, 0.0, 1.0],
    "hand_dir": [0.0, 1.0, 0.0]
  }
}
```

Handcast records templates in this format automatically. The recorded feature
values are medians across the collected samples, and the orientation vectors
are averaged and normalized. Editing templates by hand is useful for tuning
`threshold` or `ignore`; keep all required feature keys and use the exact
spelling shown above.

## Project layout

```text
config/                 Runtime settings and gesture templates
models/                 MediaPipe hand-landmarker model
src/handcast/
  capture/              Webcam frame capture
  core/                 Application, shared models, queues, settings
  gestures/             Feature extraction, matching, recording, stabilization
  service/              Capture, tracking, and gesture processing workers
  tracking/             MediaPipe hand tracking
  ui/                   OpenCV skeleton and status overlay
```
