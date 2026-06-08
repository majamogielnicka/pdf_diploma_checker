from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
import base64
import time
from analysis.modules.llm import config


class LlavaEngine:
    def __init__(self, model_path=str(config.LLAVA_MODEL_PATH), mmproj_path=str(config.LLAVA_MMPROJ_PATH)):
        print("[LLaVA][INIT] start", flush=True)
        print(f"[LLaVA][INIT] model_path={model_path}", flush=True)
        print(f"[LLaVA][INIT] mmproj_path={mmproj_path}", flush=True)
        print(f"[LLaVA][INIT] n_gpu_layers={config.N_GPU_LAYERS}", flush=True)
        init_start = time.perf_counter()

        self.chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
        self.llm = Llama(
            model_path=model_path,
            chat_handler=self.chat_handler,
            n_ctx=4096,
            n_gpu_layers=config.N_GPU_LAYERS,
            logits_all=True,
            verbose=False
        )
        self.max_tokens = 256

        init_elapsed = time.perf_counter() - init_start
        print(f"[LLaVA][INIT] done elapsed={init_elapsed:.2f}s", flush=True)
        print(f"[LLaVA][INIT] max_tokens={self.max_tokens}", flush=True)

    def extract_data(self, image_bytes):
        print("[LLaVA][EXTRACT] start", flush=True)
        print(f"[LLaVA][EXTRACT] image_bytes={len(image_bytes)}", flush=True)
        print(f"[LLaVA][EXTRACT] max_tokens={self.max_tokens}", flush=True)
        extract_start = time.perf_counter()

        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{base64_image}"

        print(f"[LLaVA][EXTRACT] base64_length={len(base64_image)}", flush=True)
        print("[LLaVA][EXTRACT] create_chat_completion start", flush=True)

        response = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text", "text": "Wyciągnij wszystkie etykiety, liczby i dane z tego wykresu/obrazka. Zwróć je jako surowe dane tekstowe."}
                    ]
                }
            ],
            max_tokens=self.max_tokens
        )

        extract_elapsed = time.perf_counter() - extract_start
        print(f"[LLaVA][EXTRACT] create_chat_completion done elapsed={extract_elapsed:.2f}s", flush=True)

        content = response["choices"][0]["message"]["content"]

        usage = response.get("usage")
        if usage is not None:
            print(f"[LLaVA][EXTRACT] usage={usage}", flush=True)

        print(f"[LLaVA][EXTRACT] output_length={len(content) if content else 0}", flush=True)
        print("[LLaVA][EXTRACT] done", flush=True)

        return content