# Quality Baselines

## Overview

Baselines define the minimum quality thresholds for the Cabulous monorepo. Each baseline is a JSON file that records the current state and expected thresholds.

## Files

- `python-function-length.json` -- Max function length (50 lines), McCabe complexity (10)
- `python-coverage.json` -- Minimum branch coverage (35%)

## Updating Baselines

To update a baseline, run the corresponding check and capture the current value:

```bash
# Function length violations
make service function-length | tee /dev/null  # count violations

# Coverage report
make service coverage  # note the percentage
```

Then edit the relevant `baselines/*.json` file and update the value and date.

## CI Integration

Quality gates in CI compare current metrics against these baselines. If the current value falls below the threshold, the build fails.

## Process

1. Run the quality check locally
2. If intentional new violations or coverage drop, update the baseline
3. Commit the baseline change alongside the code change
