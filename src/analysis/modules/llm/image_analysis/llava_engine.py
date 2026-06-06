from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
import base64
import config 

class LlavaEngine:
    def __init__(self, model_path=str(config.LLAVA_MODEL_PATH), mmproj_path=str(config.LLAVA_MMPROJ_PATH)):
        '''
        wejscie: model_path i mmproj_path w formacie stringów (ścieżki do plików modelu).
        wyjscie: brak (inicjalizacja instancji klasy).
        opis: Ładuje do pamięci model wizyjny LLaVA wykorzystywany do czytania danych z wykresów.
        '''
        self.chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
        self.llm = Llama(
            model_path=model_path,
            chat_handler=self.chat_handler,
            n_ctx=4096,
            n_gpu_layers=-1,
            logits_all=True,
            verbose=False 
        )

    def extract_data(self, image_bytes):
        '''
        wejscie: image_bytes w formacie surowych bajtów obrazu.
        wyjscie: string zawierający surowe dane tekstowe wygenerowane przez model.
        opis: Wydobywa z obrazka lub wykresu wszystkie etykiety, liczby i dane tekstowe.
        '''
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{base64_image}"

        response = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text", "text": "Wyciągnij wszystkie etykiety, liczby i dane z tego wykresu/obrazka. Zwróć je jako surowe dane tekstowe."}
                    ]
                }
            ]
        )
        return response["choices"][0]["message"]["content"]