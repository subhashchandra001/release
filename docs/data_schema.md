# Data Schema

`trajectory.csv` columns:
`run_id,timestamp,x,y,z,qx,qy,qz,qw,yaw`

`keyframes.csv` columns:
`run_id,keyframe_id,timestamp,rgb_path,depth_path,x,y,z,qx,qy,qz,qw,yaw`

`detections.csv` columns:
`run_id,keyframe_id,image_path,class_name,confidence,xmin,ymin,xmax,ymax,map_x,map_y,is_sensitive`

`privacy_results.csv` columns:
`run_id,artifact_type,filter_name,attack_name,metric_name,value`

`utility_results.csv` columns:
`run_id,artifact_type,filter_name,utility_name,metric_name,value`

## Annotation Templates

`data/annotations/sensitive_objects.csv` uses the same columns as
`detections.csv` and starts with only a header row.

`data/annotations/nav_goals.yaml` stores reviewed navigation goals and routes:

```yaml
goals: []
routes: []
```

`data/annotations/rooms.geojson` is a GeoJSON `FeatureCollection`. Room features
should include a stable room name property.

## Result Files

Result CSVs must contain at least one row. Empty files are rejected so paper
assets cannot be generated from missing data.
