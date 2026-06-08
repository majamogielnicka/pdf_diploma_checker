# Configuration guide: CPU / CUDA builds

This project uses an external JSON configuration to decide how LLM models should be loaded, especially whether the application should use CPU or CUDA and how many model layers should be offloaded to the GPU.

The important value is:

```json
"n_gpu_layers": 25
```

This value is read by `src/analysis/modules/llm/config.py` and exposed as:

```python
N_GPU_LAYERS
```

All modules that already import `N_GPU_LAYERS` from `config.py` can keep doing that. You do **not** need to pass `n_gpu_layers` manually through every function.

---

## Config files

Recommended files in the project root:

```text
cpu_config.json
gpu_config.json
app_config.json
```

Meaning:

- `cpu_config.json` — template for CPU mode.
- `gpu_config.json` — template for CUDA/GPU mode.
- `app_config.json` — active config used by the application.

`app_config.json` is the file that `config.py` automatically looks for. The CPU/GPU files are only templates. To switch mode, copy the selected template to `app_config.json`.

Example:

```bash
cp gpu_config.json app_config.json
```

or:

```bash
cp cpu_config.json app_config.json
```

On Windows CMD:

```bat
copy gpu_config.json app_config.json
```

or:

```bat
copy cpu_config.json app_config.json
```

---

## CPU config example

`cpu_config.json`:

```json
{
  "device": "cpu",
  "n_gpu_layers": 0,
  "model_dir": "C:/Users/Wiktor/models",
  "language": "pl"
}
```

For Linux:

```json
{
  "device": "cpu",
  "n_gpu_layers": 0,
  "model_dir": "/home/user/models",
  "language": "pl"
}
```

In CPU mode, `N_GPU_LAYERS` is forced to `0`.

---

## CUDA / GPU config example

`gpu_config.json`:

```json
{
  "device": "cuda",
  "n_gpu_layers": 25,
  "model_dir": "C:/Users/Wiktor/models",
  "language": "pl"
}
```

For Linux:

```json
{
  "device": "cuda",
  "n_gpu_layers": 25,
  "model_dir": "/home/user/models",
  "language": "pl"
}
```

In CUDA mode, `N_GPU_LAYERS` is read from `n_gpu_layers`. If the value is missing or invalid, the default is `25`.

---

## What `n_gpu_layers` means

`n_gpu_layers` controls how many layers of the GGUF model are loaded onto the GPU.

Typical values:

```text
0   = CPU only
10  = partial GPU offload, safer for low VRAM
25  = default CUDA value currently used in the project
-1  = try to offload all possible layers, may require a lot of VRAM
```

If the GPU runs out of memory, reduce the value, for example:

```json
"n_gpu_layers": 10
```

If CUDA is unavailable or unstable, use CPU mode:

```json
"device": "cpu",
"n_gpu_layers": 0
```

---

## Model paths

The config can use a shared `model_dir`:

```json
"model_dir": "C:/Users/Wiktor/models"
```

Then `config.py` builds these default paths:

```text
MODEL_PATH          = model_dir/gemma3_12b/google_gemma-3-12b-it-Q4_K_M.gguf
LLAVA_MODEL_PATH    = model_dir/llava-v1.6-mistral-7b.Q4_K_M.gguf
LLAVA_MMPROJ_PATH   = model_dir/mmproj-model-f16.gguf
```

If needed, paths can be overridden directly:

```json
{
  "device": "cuda",
  "n_gpu_layers": 25,
  "model_path": "C:/Users/Wiktor/models/gemma3_12b/google_gemma-3-12b-it-Q4_K_M.gguf",
  "llava_model_path": "C:/Users/Wiktor/models/llava-v1.6-mistral-7b.Q4_K_M.gguf",
  "llava_mmproj_path": "C:/Users/Wiktor/models/mmproj-model-f16.gguf",
  "language": "pl"
}
```

---

## Config loading priority

`config.py` should use this priority:

```text
1. Environment variables, e.g. PDF_CHECKER_N_GPU_LAYERS
2. External config file, e.g. app_config.json
3. Default values in config.py
```

This means environment variables can temporarily override the JSON file.

Example on Linux:

```bash
PDF_CHECKER_N_GPU_LAYERS=10 python src/app/entry.py
```

Example on Windows CMD:

```bat
set PDF_CHECKER_N_GPU_LAYERS=10
python src\app\entry.py
```

---

## Using a different config file without copying

Instead of copying `cpu_config.json` or `gpu_config.json` to `app_config.json`, you can point the application to a specific config file with `PDF_CHECKER_CONFIG`.

Linux:

```bash
export PDF_CHECKER_CONFIG=/home/user/pdf_diploma_checker/gpu_config.json
python src/app/entry.py
```

Windows CMD:

```bat
set PDF_CHECKER_CONFIG=C:\Users\Wiktor\zsd\pdf_diploma_checker\gpu_config.json
python src\app\entry.py
```

This is useful for testing.

For released builds, prefer shipping one active `app_config.json` next to the executable.

---

## Build strategy

Recommended release matrix:

```text
Windows CPU
Windows CUDA
Linux CPU
Linux CUDA
```

The Python source code should stay the same. Builds differ by:

1. Installed `llama-cpp-python` variant.
2. Active `app_config.json`.

CPU build:

```text
llama-cpp-python built/installed without CUDA
app_config.json -> device: cpu, n_gpu_layers: 0
```

CUDA build:

```text
llama-cpp-python built/installed with CUDA
app_config.json -> device: cuda, n_gpu_layers: 25
```

Important: setting `device: cuda` in JSON does not magically enable CUDA if `llama-cpp-python` was installed without CUDA support.

---

## Example build flow

Linux CUDA:

```bash
cp gpu_config.json app_config.json
python -m PyInstaller src/app/entry.py --name pdf-checker-linux-cuda
cp app_config.json dist/pdf-checker-linux-cuda/app_config.json
```

Linux CPU:

```bash
cp cpu_config.json app_config.json
python -m PyInstaller src/app/entry.py --name pdf-checker-linux-cpu
cp app_config.json dist/pdf-checker-linux-cpu/app_config.json
```

Windows CUDA:

```bat
copy gpu_config.json app_config.json
python -m PyInstaller src\app\entry.py --name pdf-checker-windows-cuda
copy app_config.json dist\pdf-checker-windows-cuda\app_config.json
```

Windows CPU:

```bat
copy cpu_config.json app_config.json
python -m PyInstaller src\app\entry.py --name pdf-checker-windows-cpu
copy app_config.json dist\pdf-checker-windows-cpu\app_config.json
```

---

## Testing which config is active

From the project root:

```bash
python -c "import sys, os; sys.path.insert(0, os.path.abspath('src')); from analysis.modules.llm import config; print('CONFIG =', config.EXTERNAL_CONFIG_PATH); print('DEVICE =', config.DEVICE); print('N_GPU_LAYERS =', config.N_GPU_LAYERS); print('MODEL_PATH =', config.MODEL_PATH); print('LLAVA_MODEL_PATH =', config.LLAVA_MODEL_PATH); print('LLAVA_MMPROJ_PATH =', config.LLAVA_MMPROJ_PATH)"
```

Expected CUDA output:

```text
DEVICE = cuda
N_GPU_LAYERS = 25
```

Expected CPU output:

```text
DEVICE = cpu
N_GPU_LAYERS = 0
```

---

## Recommended `.gitignore`

If `app_config.json` is local and may contain user-specific paths, add it to `.gitignore`:

```gitignore
app_config.json
```

Keep template configs in git:

```text
cpu_config.json
gpu_config.json
```

---

## Common problems

### The app still uses CPU even with `device: cuda`

Check whether `llama-cpp-python` was installed with CUDA support. The JSON config only sets `n_gpu_layers`; it does not change the installed backend.

### CUDA runs out of memory

Reduce:

```json
"n_gpu_layers": 10
```

or switch to CPU:

```json
"device": "cpu",
"n_gpu_layers": 0
```

### The wrong config is loaded

Print the active config:

```bash
python -c "import sys, os; sys.path.insert(0, os.path.abspath('src')); from analysis.modules.llm import config; print(config.EXTERNAL_CONFIG_PATH)"
```

If needed, force a config explicitly:

```bash
export PDF_CHECKER_CONFIG=/path/to/gpu_config.json
```

or on Windows:

```bat
set PDF_CHECKER_CONFIG=C:\path\to\gpu_config.json
```

### User changed `app_config.json`, but nothing changed

Restart the application. Config values are read when Python imports `config.py`.