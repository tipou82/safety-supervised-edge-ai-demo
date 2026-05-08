# DD-001 — Camera AI Model Selection for Hand Detection

**Status**: OPEN — awaiting engineer decision
**Date**: 2026-05-09
**Author**: Yunpeng
**Milestone**: M4 — Camera AI Sensor Path
**Related issue**: #5

> Educational demonstrator — not ISO 26262 certified.
> AI inference runs in the development domain only. Detection results do NOT enter the safety path.

---

## 1. Problem Statement

The camera_ai_node must detect:
1. A human hand (empty)
2. A human hand holding an object

Detection results are published to `/detections` at ≥ 10 Hz. The `decision_node` uses `/detections` liveness only (`camera_valid` boolean, 2s timeout) — raw detection outputs do not enter the `StateEvaluator` or any safety path.

Three inference approaches are evaluated:

| Option | Model(s) |
|---|---|
| A | YOLOv8n only |
| B | MediaPipe Hands only |
| C | YOLOv8n + MediaPipe Hands (combined) |

---

## 2. Decision Criteria

| Criterion | Weight | Rationale |
|---|---|---|
| Detection accuracy — hand | High | Core functional requirement |
| Detection accuracy — hand + object | High | Core functional requirement |
| Inference latency on Pi5 CPU | High | Must sustain ≥ 10 Hz |
| Integration complexity | Medium | Affects maintainability |
| camera_valid reliability | High | Affects StateEvaluator correctness |
| Safety diagnostic coverage | Medium | ASIL-B-inspired demonstrator value |
| Portfolio demonstrator value | Medium | Demonstrates MBSE and AI safety discipline |

---

## 3. Option A — YOLOv8n Only

### Description

Single-stage object detector from Ultralytics, pretrained on COCO (80 classes including `person`). A hand-specific YOLO model (e.g., trained on EgoHands or 11k Hands dataset) would be used instead of COCO for accurate hand detection.

### Pros

- **Hand + object detection in one model**: bounding boxes for both hand and held object simultaneously — directly satisfies both detection requirements
- **Single pipeline**: one model, one inference call, simpler failure mode analysis
- **Flexible**: detectable object classes configurable via model training or fine-tuning
- **Industry standard**: Ultralytics ecosystem, ONNX export, widely documented
- **Quantitative confidence scores**: bounding box confidence usable for plausibility checks

### Cons

- **Standard COCO YOLOv8n is not hand-optimised**: COCO `person` class covers whole body, not isolated hands. A hand-specific model requires downloading a pre-trained variant or fine-tuning
- **Higher CPU load**: YOLOv8n nano is the lightest YOLO variant but still heavier than MediaPipe on ARM CPU
- **Latency risk**: YOLOv8n on Pi5 CPU achieves ~8–15 FPS without hardware acceleration — marginal for 10 Hz requirement under load
- **No hand landmark precision**: detects hand bounding box but not finger positions

### Performance estimate (Pi5 ARM Cortex-A76, CPU only)

| Metric | Estimate |
|---|---|
| Inference speed | 8–15 FPS (YOLOv8n, CPU, 640×640) |
| Model size | ~6 MB |
| RAM | ~150 MB |
| 10 Hz achievable? | Marginal — depends on image resolution and ROS2 overhead |

---

## 4. Option B — MediaPipe Hands Only

### Description

Google's MediaPipe Hands solution: two-stage pipeline (palm detection → hand landmark model). Produces 21 3D hand landmarks. Highly optimised for ARM CPUs.

### Pros

- **Purpose-built for hand detection**: state-of-the-art accuracy for isolated hand detection on edge devices
- **Very fast on Pi5**: 25–35 FPS at full resolution — comfortably exceeds 10 Hz
- **Low CPU load**: leaves headroom for ROS2 processing and other nodes
- **Robust under partial occlusion**: landmark model is tolerant of partial hand visibility
- **Lightweight**: MediaPipe runtime ~30 MB, inference model ~9 MB

### Cons

- **Cannot detect held objects**: detects hand shape and landmarks only — a hand holding a screwdriver and an empty hand produce the same output
- **Does not satisfy "hand holding object" requirement without extension**: would need a separate object detector or heuristic (e.g., infer object from hand pose)
- **No bounding box for the held object**: only hand bounding box and landmarks available
- **Limited class vocabulary**: binary output (hand present / not present) with landmark positions

### Performance estimate

| Metric | Estimate |
|---|---|
| Inference speed | 25–35 FPS (MediaPipe Hands, CPU, 1280×720) |
| Model size | ~9 MB |
| RAM | ~80 MB |
| 10 Hz achievable? | Yes — with significant headroom |

---

## 5. Option C — Combined YOLOv8n + MediaPipe Hands

### Description

MediaPipe Hands runs first (fast palm detection and landmark extraction). When a hand is detected, YOLOv8n runs on the cropped region-of-interest (ROI) around the hand to detect any held object. If no hand is detected by MediaPipe, YOLOv8n is skipped.

```
Frame → MediaPipe Hands
         │
         ├── Hand detected → crop ROI → YOLOv8n on ROI → classify held object
         │
         └── No hand → publish: hand=false, object=none
```

### Pros

- **Satisfies both detection requirements precisely**: MediaPipe for hand presence and pose, YOLOv8n for object classification within hand region
- **Efficient gating**: YOLOv8n only runs when MediaPipe detects a hand → saves CPU when no hand is present
- **Redundant detection path**: hand presence confirmed by two independent models — higher confidence for `camera_valid` signal
- **Diagnostic coverage**: if MediaPipe fails (returns no hand despite hand present), YOLOv8n full-frame fallback could be added as a safety net
- **Richer telemetry**: hand landmarks + object bounding box available for portfolio demonstration
- **Best fit for the demonstrator narrative**: demonstrates sophisticated AI pipeline while keeping safety path simple (camera_valid boolean only)

### Cons

- **Highest complexity**: two models, sequential pipeline, more failure modes to handle
- **Highest CPU load**: both models active simultaneously when a hand is present
- **Latency accumulation**: MediaPipe + YOLOv8n on ROI latency adds up
- **Dependency on MediaPipe accuracy**: if MediaPipe misses the hand, YOLOv8n on the full frame is not triggered in gated mode

### Performance estimate

| Metric | Estimate |
|---|---|
| Inference speed (hand present) | 8–15 FPS (both models active) |
| Inference speed (no hand) | 25–35 FPS (MediaPipe only) |
| Combined RAM | ~230 MB |
| 10 Hz achievable? | Yes when no hand; marginal when hand present |

---

## 6. Safety Benefit Analysis

> **Architectural note**: In this system, the camera domain is the **development (AI) domain**. Camera detection outputs do NOT enter the safety path. The Pi400 supervisor makes safety decisions independently of camera AI. The only safety-relevant output of camera_ai_node is the `camera_valid` boolean (liveness flag) consumed by `decision_node`.

### Impact on `camera_valid` reliability

| Option | camera_valid reliability | Analysis |
|---|---|---|
| A (YOLOv8n only) | Medium | Single model; if model hangs or crashes, camera_valid goes false. No redundancy. |
| B (MediaPipe only) | Medium-High | Lighter model, less likely to hang; faster recovery. Still single model. Does not satisfy held-object requirement → partial functional coverage. |
| C (Combined) | High | Two independent models. If MediaPipe fails silently (publishes no detections), camera_valid still drops → StateEvaluator sees camera invalid → DEGRADED. YOLOv8n gating provides secondary confirmation of hand presence. Highest diagnostic coverage of camera pipeline health. |

### Impact on StateEvaluator transitions

All three options produce the same StateEvaluator behaviour when working correctly — `camera_valid=true` enables NORMAL/WARNING states. The safety difference lies in **failure mode coverage**:

| Failure mode | Option A | Option B | Option C |
|---|---|---|---|
| Model crashes silently | DEGRADED (camera_valid timeout) | DEGRADED | DEGRADED |
| Model publishes stale data | DEGRADED (2s timeout) | DEGRADED | DEGRADED |
| Hand detected but no object info | Partial ✗ | Not attempted ✗ | ✅ YOLOv8n fills gap |
| False positive hand detection | Possible | Less likely (landmark model) | Least likely (dual confirmation) |
| CPU overload → latency > 2s | DEGRADED | Unlikely | Possible when hand present |

### ASIL-B-inspired assessment

| Option | Diagnostic coverage | Functional completeness | CPU risk |
|---|---|---|---|
| A | Low-Medium | High (hand + object) | Medium |
| B | Medium | Low (hand only) | Low |
| **C** | **High** | **High (hand + object)** | **Medium-High** |

Option C provides the strongest ASIL-B-inspired argument:
- Two independent detection paths confirm camera pipeline liveness
- Failure of either model is detectable (liveness timeout)
- Gated execution limits CPU impact when no hand present
- Richer detection output supports the demonstrator narrative

---

## 7. Recommendation

**Option C — Combined MediaPipe Hands + YOLOv8n (gated)**

*Rationale*: Satisfies both detection requirements (hand; hand+object), provides the strongest diagnostic coverage of the camera pipeline, and is the most compelling portfolio demonstrator of AI sensor fusion within a safety-supervised architecture. CPU risk is manageable via image resolution tuning and ROI cropping.

*Mitigation for CPU risk*: use 640×480 or 320×240 input resolution; reduce YOLOv8n input to cropped ROI (~200×200 px); monitor actual FPS and fall back to Option B (MediaPipe only) if 10 Hz cannot be sustained.

**Fallback**: If Option C cannot sustain 10 Hz on Pi5 under full system load, fall back to Option B (MediaPipe Hands) for hand detection and document the held-object requirement as deferred.

---

## 8. Decision

**Decision**: ☐ Option A — YOLOv8n only
            ☐ Option B — MediaPipe Hands only
            ☑ Option C — Combined (recommended)
            ☐ Other (specify)

**Notes / conditions**:

_To be filled in by engineer before implementation begins._

**Decided by**: Yunpeng
**Decision date**: ___________

---

## 9. References

- [YOLOv8n — Ultralytics](https://docs.ultralytics.com)
- [MediaPipe Hands — Google](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
- EgoHands dataset (hand detection training)
- `requirements/interfaces.yaml` — timing constraints (10 Hz camera)
- `docs/safety_concept.md` — camera_valid role in StateEvaluator
- `AGENTS.md` — AI boundary rules (no AI in safety path)
