# Troubleshooting

If a script reports a missing input, check `configs/experiment.yaml` and
`configs/paths.yaml` first. All scripts are intended to run from the repository
root with `--config configs/experiment.yaml`.

Open3D-dependent point-cloud tests skip when Open3D is not installed. Install
the `geo` optional dependencies before running geometry workflows that read or
write point-cloud files.

Paper figures and tables are generated only from existing result CSVs. The
repository should not contain fabricated research results.

## Common Failures

- `No runs configured`: add real processed artifacts and run entries to
  `configs/experiment.yaml`.
- `Required occupancy map does not exist`: check `map_yaml` or the default
  `data/processed/<run_id>/map.yaml` path.
- `Required trajectory CSV does not exist`: check `trajectory_csv` or the
  default `data/processed/<run_id>/trajectory.csv` path.
- `Result CSV contains no rows`: run attacks or utility evaluation on real
  inputs before aggregation or paper asset generation.
- `ROS bag parsing requires ROS 2 and rosbag2_py`: source the ROS environment or
  export artifacts outside the offline Python environment.
