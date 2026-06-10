# User Guide

## 1. Purpose of this guide

This guide explains how to use the application after it has been installed and configured.

For installation and model configuration, see:

```text
config_guide.md
```

For a general description of the project and available checks, see:

```text
README.md
```

## 2. Before running the application

Before starting the analysis, make sure that:

1. The application has been installed or extracted correctly.
2. The `app_config.json` file is present in the correct location.
3. The required local models are available.
4. The PDF file you want to analyze is ready.
5. The correct language of the thesis is selected in the application.

The application should not be run directly from inside a ZIP archive. Extract the package first.

## 3. Configuration file

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

## 4. Starting the application

Start the application according to the package you are using.

For a packaged executable, run the appropriate application file.

For a source-code version, start the application from the project directory using the command described in the installation guide.

After startup, the main application window should appear.

## 5. Selecting the thesis language

Before running the analysis, select the language of the thesis in the application interface.

Choose the language that matches the content of the PDF file.

For example:

* select Polish for a thesis written in Polish,
* select English for a thesis written in English.

The selected language affects text processing, linguistic analysis and selected content-related checks.

If the wrong language is selected, the results may be inaccurate.

## 6. Loading a PDF file

To load a thesis:

1. Open the application.
2. Select the correct thesis language.
3. Choose the PDF file using the file selection option in the interface.
4. Make sure the selected file is correct before starting the analysis.

The input file should be a readable PDF document.

If the PDF contains scanned pages instead of selectable text, some results may be incomplete or less accurate.

## 7. Image analysis option

The application may contain an option named:

```text
Image analysis
```

or a checkbox/button with a similar name.

This option enables additional analysis of figures, charts, diagrams and other visual elements in the thesis.

When Image analysis is enabled, the application may analyze:

* figures,
* charts,
* diagrams,
* labels and data visible in images,
* image readability,
* font consistency inside images.

Image analysis may significantly increase processing time.

It can also require more memory and GPU resources.

Use Image analysis when figures, charts or diagrams are important for the thesis assessment.

Disable Image analysis if:

* you want faster processing,
* the document contains many images,
* the application freezes during visual analysis,
* the computer does not have enough resources.

If Image analysis is disabled, the rest of the analysis can still be performed.

## 8. Running the analysis

After selecting the PDF file, language and analysis options, start the analysis using the main analysis button in the interface.

The analysis time depends on:

* document length,
* number of pages,
* number of images,
* selected options,
* hardware performance,
* CPU/GPU configuration.

Do not close the application while the analysis is running.

## 9. Reading the results

After the analysis is complete, the application displays the results in the interface.

Depending on the selected options, the results may include:

* detected issues,
* comments,
* suggestions,
* content-related score,
* image-related information,
* final report or summary.

Review the results manually before using them.

## 10. Important note about content-related analysis

The content-related analysis is indicative only.

It is generated automatically using local AI models and text-processing methods.

The score and comments should not be treated as a final grade or an authoritative evaluation of the thesis.

Do not rely on the content-related score in 100%.

The result may be affected by:

* incorrectly extracted text,
* unusual PDF structure,
* missing or unclear thesis goal,
* formatting problems,
* scanned pages,
* OCR issues,
* wrong language selection,
* limitations of local AI models.

The final assessment should always be made by a human reviewer, supervisor or examiner.

## 11. Exporting or saving results

If the application provides an export option, you can save the generated results or report.

Before sharing or submitting the report, review it manually.

Automatically generated comments may require correction, interpretation or removal.

## 12. Common usage problems

### The PDF does not load

Check whether:

* the file is a valid PDF,
* the file is not open or locked by another program,
* the path to the file does not contain unsupported characters,
* the file is not corrupted.

### The analysis is very slow

Possible reasons:

* the PDF is large,
* Image analysis is enabled,
* the application is running in CPU mode,
* many images are present in the document,
* other applications are using system resources.

Try disabling Image analysis and running the analysis again.

### Image analysis takes too long or freezes

Image analysis is computationally expensive.

Disable the Image analysis option and run the analysis again.

### Results seem inaccurate

Check whether:

* the correct thesis language was selected,
* the PDF text is selectable,
* the document is not scanned,
* the PDF structure is correct,
* the file was exported properly from Word or LaTeX.

Automatic analysis may not work perfectly for every PDF.

## 13. Quick usage checklist

Before starting analysis:

1. Open the application.
2. Select the thesis language.
3. Load the correct PDF file.
4. Decide whether Image analysis should be enabled.
5. Start the analysis.
6. Wait until the process finishes.
7. Review all results manually.
8. Treat content-related results as indicative, not final.

## 14. Disclaimer

The application is a supporting tool for diploma thesis analysis.

It does not replace human review.

The results, especially AI-generated comments and content-related scores, should be treated as suggestions and indicators.

The user is responsible for interpreting and verifying the generated results.
