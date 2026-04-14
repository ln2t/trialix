<div align="center">

# Trialix

**First-level fMRI analysis for trial-based experimental designs**

[Installation](#installation) | [Quick Start](#quick-start) | [Usage](#usage) | [Configuration](#configuration) | [Workflow](#workflow) | [Output Structure](#output-structure) | [Events File Format](#events-file-format) | [Expected fMRIPrep Output Structure](#expected-fmriprep-output-structure) | [License](#license)

</div>

---

Trialix is a BIDS-application CLI tool that performs participant-level (first-level) fMRI analysis using [nilearn](https://nilearn.github.io/). It is designed for trial-based experimental conditions — block designs, event-related designs, or mixed designs.

Trialix is a wrapper around nilearn's `FirstLevelModel` that handles BIDS data discovery, GLM fitting, contrast computation, statistical thresholding, and BIDS-compliant output generation.

> **Note:** Trialix does **not** perform fMRI preprocessing. It expects data preprocessed by [fMRIPrep](https://fmriprep.org/) or a similar tool. Group-level (second-level) analysis is handled by the companion tool **StatCraft**.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/arovai/trialix.git
cd trialix

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install trialix and its dependencies
pip install -e .
```

### Dependencies

- Python ≥ 3.9
- [nilearn](https://nilearn.github.io/) ≥ 0.10
- [pybids](https://bids-standard.github.io/pybids/) ≥ 0.16
- [nibabel](https://nipy.org/nibabel/) ≥ 4.0
- numpy, pandas, pyyaml, matplotlib

---

## Quick Start

### Basic usage (BIDS rawdata + fMRIPrep derivatives)

```bash
trialix /data/rawdata /data/output participant \
    --task motor \
    --derivatives preproc=/data/derivatives/fmriprep
```

### Full analysis with contrasts and thresholding

```bash
trialix /data/rawdata /data/output participant \
    --task motor \
    --derivatives preproc=/data/derivatives/fmriprep \
    --participant-label 01 02 03 \
    --conditions left_hand right_hand \
    --regressors trans_x trans_y trans_z rot_x rot_y rot_z \
    --contrasts "left_hand - right_hand" "left_hand + right_hand" \
    --alpha 0.05 0.001 \
    --height-control fdr bonferroni
```

### Using a config file

```bash
trialix /data/rawdata /data/output participant --config config.yaml
```

CLI arguments always override config file values.

---

## Usage

```
trialix INPUT_DIR OUTPUT_DIR participant [options]
```

### Positional Arguments

| Argument | Description |
|---|---|
| `INPUT_DIR` | Path to BIDS rawdata folder (with `--derivatives`) or to preprocessed data folder (with `--events-file`). |
| `OUTPUT_DIR` | Path to output directory for analysis derivatives. |
| `participant` | Analysis level (currently only `participant` is supported). |

### Input Modes

**Mode 1: BIDS rawdata + derivatives**
- `INPUT_DIR` points to the BIDS rawdata folder
- Use `--derivatives preproc=PATH` to specify fMRIPrep output
- Events files are discovered automatically from rawdata

**Mode 2: Preprocessed data directly**
- `INPUT_DIR` points to the preprocessed data folder (e.g., fMRIPrep output)
- Use `--events-file PATH` to provide the events TSV file

### General Options

| Option | Description |
|---|---|
| `--help` | Show help message and exit. |
| `--version` | Show version and exit. |
| `--debug` | Enable debug mode with increased verbosity. |
| `--config FILE` | Path to YAML configuration file. |

### Derivatives

| Option | Description |
|---|---|
| `--derivatives KEY=PATH` | Specify BIDS derivatives location. Use `preproc=PATH` for preprocessed data. Can be specified multiple times. |

### BIDS Entity Filters

| Option | Default | Description |
|---|---|---|
| `--participant-label LABEL [LABEL ...]` | all | Subjects to process (without `sub-` prefix). |
| `--task TASK` | *required* | Task to process (without `task-` prefix). |
| `--session SESSION` | None | Session to process (without `ses-` prefix). |
| `--space SPACE` | `MNI152NLin2009cAsym` | Template space. |

### Modeling Options

| Option | Default | Description |
|---|---|---|
| `--events-file PATH` | auto | Path to events TSV file. Required in Mode 2. |
| `--confounds-file PATH` | auto | Custom confounds TSV file. Default: fMRIPrep output. |
| `--conditions COND [COND ...]` | all | Trial types to include from events.tsv. |
| `--regressors REG [REG ...]` | none | Confound regressors (column names from confounds file). |
| `--contrasts CON [CON ...]` | auto | Contrast definitions (e.g., `"cond1 - cond2"`). |

### Statistical Thresholding

| Option | Default | Description |
|---|---|---|
| `--alpha ALPHA [ALPHA ...]` | `0.05` | P-value threshold(s). |
| `--height-control METHOD [METHOD ...]` | none | Correction method: `fdr`, `bonferroni`, or `none`. |

### Config-File-Only Parameters

These parameters can only be set in the YAML configuration file and are passed directly to nilearn's `FirstLevelModel`:

| Parameter | Default | Description |
|---|---|---|
| `hrf_model` | `glover` | HRF model (`glover`, `spm`, `glover + derivative`, etc.) |
| `drift_model` | `cosine` | Drift model (`cosine`, `polynomial`, or `null`) |
| `drift_order` | `1` | Drift order for polynomial model |
| `high_pass` | `0.01` | High-pass filter cutoff in Hz |
| `smoothing_fwhm` | `null` | Spatial smoothing FWHM in mm |

---

## Configuration

Trialix supports a YAML configuration file. CLI arguments override config values. See [`config_example.yaml`](config_example.yaml) for a complete example.

```yaml
# Required
task: motor

# Optional BIDS filters
participant_label:
  - "01"
  - "02"
space: MNI152NLin2009cAsym

# Modeling
conditions:
  - left_hand
  - right_hand
regressors:
  - trans_x
  - trans_y
  - trans_z
contrasts:
  - "left_hand - right_hand"

# Thresholding
alpha:
  - 0.05
height_control:
  - fdr

# FirstLevelModel parameters (config-only)
hrf_model: glover
drift_model: cosine
high_pass: 0.01
smoothing_fwhm: 6
```

---

## Workflow

1. **Validate inputs** — Check CLI arguments and config file; verify data paths.
2. **Discover data** — Use pybids to find subjects, tasks, sessions, BOLD files, events, and confounds.
3. **Loop over subjects and sessions:**
   - Load preprocessed BOLD data
   - Load events TSV (filter by requested conditions)
   - Load confounds TSV (select requested regressors)
   - Extract TR from BIDS metadata or NIfTI header
   - Build `FirstLevelModel` with specified parameters
   - Fit the GLM
   - Compute contrasts (z-score, t-stat, p-value, effect size, effect variance)
   - Apply statistical thresholding
   - Save BIDS-compliant NIfTI outputs
   - Generate and save HTML report
4. **Write `dataset_description.json`** in output directory.

---

## Output Structure

```
OUTPUT_DIR/
├── dataset_description.json
├── logs/
│   └── trialix_YYYYMMDD_HHMMSS.log
├── sub-01/
│   ├── [ses-SES/]
│   │   ├── sub-01_[ses-SES_]task-TASK_space-SPACE_contrast-CON_desc-zScore_statmap.nii.gz
│   │   ├── sub-01_[ses-SES_]task-TASK_space-SPACE_contrast-CON_desc-tStat_statmap.nii.gz
│   │   ├── sub-01_[ses-SES_]task-TASK_space-SPACE_contrast-CON_desc-pValue_statmap.nii.gz
│   │   ├── sub-01_[ses-SES_]task-TASK_space-SPACE_contrast-CON_desc-effectSize_statmap.nii.gz
│   │   ├── sub-01_[ses-SES_]task-TASK_space-SPACE_contrast-CON_desc-effectVariance_statmap.nii.gz
│   │   ├── sub-01_[ses-SES_]task-TASK_space-SPACE_contrast-CON_desc-zScoreThresh*_statmap.nii.gz
│   │   └── sub-01_[ses-SES_]task-TASK_space-SPACE_report.html
│   └── ...
├── sub-02/
│   └── ...
└── ...
```

---

## Events File Format

The events TSV file must contain at least three columns:

| Column | Type | Description |
|---|---|---|
| `onset` | float | Event onset time in seconds |
| `duration` | float | Event duration in seconds |
| `trial_type` | string | Condition label |

Example:

```tsv
onset	duration	trial_type
0.0	15.0	left_hand
20.0	15.0	right_hand
40.0	15.0	left_hand
60.0	15.0	right_hand
```

---

## Expected fMRIPrep Output Structure

Trialix expects fMRIPrep output organized as:

```
PREPROC_PATH/
├── sub-SUB/
│   ├── [ses-SES/]
│   │   └── func/
│   │       ├── sub-SUB_[ses-SES_]task-TASK_space-SPACE_desc-preproc_bold.nii.gz
│   │       └── sub-SUB_[ses-SES_]task-TASK_desc-confounds_timeseries.tsv
│   └── ...
└── ...
```

---

## License

MIT
