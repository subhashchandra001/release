# Dataset Card — PrivateMap-Bench NeurIPS 2026

## Summary

PrivateMap-Bench NeurIPS 2026 is a TurtleBot4 benchmark collection for measuring privacy leakage and utility loss in indoor SLAM map sharing.

## Collection scale

- Robot: TurtleBot4
- Environments or layout variants: 3
- Runs per environment: 5
- Total runs: 15
- RGB keyframes sampled per run: 300 during collection; RGB image files are
  excluded from this sanitized release.
- Reference maps: 3 moving-SLAM occupancy maps

## Run categories

Each environment includes mapping, relocalization-style, object-proxy, repeated-route, and privacy-stress runs.

## Legacy processed runs

The release also contains five legacy processed `run_*` folders retained for audit and future extension. These legacy runs are not included in the NeurIPS 2026 reported aggregate results, figures, or tables.

## Data modalities

Processed artifacts include occupancy maps, trajectories, keyframe indexes, and header-only detection files. Raw ROS bags, sampled RGB keyframe images, and contact sheets are excluded from this sanitized release.

## Sensitive content policy

Raw ROS bags, unreviewed keyframes, and contact sheets are private. No real private documents, faces, badges, IDs, medication, personal screens, or personal information should be released.

## Intended use

This dataset is intended for privacy leakage measurement, privacy-utility trade-off analysis, route/routine leakage analysis, and navigation utility evaluation.

## Limitations

Room annotations are abstract grid-space zones. Detections are header-only until manual review confirms safe proxy objects. Descriptor and point-cloud claims are disabled unless artifacts are later implemented and validated.

## Release recommendation

Release code, configs, docs, aggregate results, generated tables, and generated figures. Release processed maps and trajectories only after explicit safety review. Release keyframe indexes only when they do not expose private image paths; keep raw images and contact sheets private by default.
