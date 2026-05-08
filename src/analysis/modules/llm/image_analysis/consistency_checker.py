from llama_cpp import Llama
import json
import config 

class ConsistencyChecker:
    def __init__(self, model_path=str(config.MODEL_PATH)):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            verbose=False
        )

    def check(self, paragraph, image_data):
        prompt = f"""
        Dane z obrazka: {image_data}
        Akapit z pracy: {paragraph}
        
        Przeanalizuj, czy dane w akapicie zgadzają się z obrazkiem.
        Zwróć wynik w JSON. Klawisze: "poprawnosc_danych" (jako string "True" lub "False") oraz "bledy" (jako string "None" lub cytaty błędnych zdań).
        """
        
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_object",
            }
        )
        
        result_text = response["choices"][0]["message"]["content"]
        
        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            return {"poprawnosc_danych": "False", "bledy": "Błąd parsowania wymuszonego JSONa z modelu."}