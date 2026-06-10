# User Guide

## 1. Before running the application

Before starting the analysis, make sure that:

1. The application has been installed or extracted correctly.
2. The `app_config.json` file is present in the correct location.
3. The required local models are available.
4. The PDF file you want to analyze is ready.
5. The correct language of the thesis is selected in the application.

The application should not be run directly from inside a ZIP archive. Extract the package first.

## 2. Configuration file

The application requires a configuration file named:

```text
app_config.json
```

This file is responsible for basic application settings, such as the model directory and hardware mode.

The example files:

```text
cpu_config.json
gpu_config.json
```

are templates only. To use one of them, copy it and rename the copy to:

```text
app_config.json
```

If `app_config.json` is missing or has a different name, the application may not start correctly.

## 3. Model and file locations

The application uses local files stored on the user's computer.

Before running the analysis, make sure that the configuration file points to the correct model directory and that the required model files are available.

### Configuration file location

The configuration file must be placed in the main application directory.

Example:

```text
pdf_diploma_checker/
├── app_config.json
├── cpu_config.json
├── gpu_config.json
├── src/
├── requirements.txt
└── README.md
```

The files:

```text
cpu_config.json
gpu_config.json
```

are only templates. They can be copied and renamed to:

```text
app_config.json
```

### Model directory location

The model directory is defined in `app_config.json` using the field:

```json
"model_dir": "PATH_TO_MODELS_DIR"
```

Example on Windows:

```json
"model_dir": "C:/Users/YOUR_USERNAME/models"
```

Example on Linux:

```json
"model_dir": "/home/YOUR_USERNAME/models"
```

The path should point to the main folder containing all required local model files.

### Required model structure

The model directory should have the following structure:

```text
PATH_TO_MODELS_DIR/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

For example, on Linux:

```text
/home/YOUR_USERNAME/models/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

For example, on Windows:

```text
C:/Users/YOUR_USERNAME/models/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

### Model files download

The required model files can be downloaded from Google Drive:

[Download model files](https://drive.google.com/drive/folders/11GQeiS8VuTJpdSvF0uswwiqycTCtH-qt)

After downloading the files, place them in the model directory using the structure shown above.

### PDF file location

The analyzed PDF file can be stored in any accessible location on the computer.

For example:

```text
/home/YOUR_USERNAME/Documents/thesis.pdf
```

or:

```text
C:/Users/YOUR_USERNAME/Documents/thesis.pdf
```

The file is selected directly in the application interface.

### Output files location

If the application generates output files, such as reports or annotated PDFs, they may be saved in an output directory defined by the application or selected by the user.

If an `output` directory is used, it may look like this:

```text
pdf_diploma_checker/
├── output/
│   ├── report.pdf
│   └── analyzed_thesis.pdf
```

Before sharing any generated report, review the results manually.


## 4. Disclaimer

The application is a supporting tool for diploma thesis analysis.

It does not replace human review.

The results, especially merit assessment, should be treated as suggestions and indicators.

The user is responsible for interpreting and verifying the generated results.
