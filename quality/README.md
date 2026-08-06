# Quality Baselines

## Overview

Baselines pin the current state of quality metrics so they can only improve
(ratchet). The Cabulous monorepo has a single baselined metric:

- `baselines/jscpd.json` -- duplicates/lines/percentage ratchet for `jscpd`.

Real thresholds for coverage and function length are configured directly in:

- `service/pyproject.toml` -- `[tool.coverage.report]` (`fail_under`)
  and `[tool.flake8]` (`max-function-length`, `max-complexity`).
- `app/web` vitest config -- frontend coverage thresholds.

## Updating the jscpd baseline

To accept new known duplicates:

```bash
task service:duplication   # produce a fresh jscpd-report
```

Then edit `baselines/jscpd.json` (update `total_duplicates`,
`total_duplicated_lines`, `known_duplicates`, `updated`) and commit it
alongside the code change.

## Process

1. Run the quality check locally.
2. If intentional new violations or a coverage drop, update the baseline.
3. Commit the baseline change alongside the code change.