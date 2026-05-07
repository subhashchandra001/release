# Data Release Policy

PrivateMap-Bench uses indoor robot data that may reveal layout, routines, people, screens, documents, and other sensitive information.

## Never commit or release by default

- data/raw_rosbags/
- raw camera streams
- unreviewed RGB keyframes
- unreviewed contact sheets
- artifacts containing faces, badges, IDs, personal screens, medication, private documents, or personal information

## Conditional release after review

The following may be released only after review:

- processed occupancy maps
- trajectories
- keyframes
- contact sheets
- object detections

Review must confirm that artifacts do not expose private or identifying content and that any proxy objects are safe and non-identifying.

## Usually safe to release

The following are intended for public or reviewer release:

- source code
- tests
- configs
- protocol documentation
- aggregate result CSVs
- generated figures and tables derived from aggregate results
- paper source and anonymous paper PDF

## Detections policy

Detection rows must not be fabricated. Add object detections only after manual keyframe review confirms a real visible safe proxy object.

data/annotations/sensitive_objects.csv and per-run detections.csv files may remain header-only.

## Git policy

Before committing, run git status --short and confirm that no raw bags or unsafe processed images are staged. Use explicit git add paths rather than git add .
