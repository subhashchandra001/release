# Benchmark Card — PrivateMap-Bench NeurIPS 2026

## Benchmark task

Measure privacy leakage and utility preservation when indoor SLAM artifacts are filtered before sharing.

## Inputs

- Occupancy maps
- Trajectories
- Reviewed zone annotations
- Navigation routes
- Optional object detections after manual review

## Filters

The NeurIPS configuration evaluates occupancy blur, noise, component removal, trajectory downsampling, trajectory quantization, and parameter sweeps.

## Privacy attacks

Enabled attacks are floor-plan leakage, room-graph leakage, trajectory leakage, and routine leakage.

Disabled attacks are object leakage, geometry leakage, and descriptor leakage until reviewed artifacts exist.

## Utility metrics

Enabled utilities are map compactness and A* navigation with route success, path cost, path overhead versus reference, expanded nodes, and connectivity preserved.

## Outputs

The benchmark writes privacy_results.csv, utility_results.csv, aggregated_results.csv, and aggregated_results.json under data/results/.

## Supported claims

The benchmark supports claims about structural map leakage, room-graph recovery, trajectory leakage, routine leakage, navigation utility degradation, and privacy-utility trade-offs.

## Unsupported default claims

The benchmark does not claim object leakage, descriptor leakage, point-cloud leakage, or public release of raw bags/unreviewed images.
