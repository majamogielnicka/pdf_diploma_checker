from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
# albo:
# MODEL_NAME = "Qwen/Qwen3-Embedding-4B"
# MODEL_NAME = "Qwen/Qwen3-Embedding-8B"

model = SentenceTransformer(MODEL_NAME)

purpose = "Transformata Fouriera na grupach skończonych"
section = "Fragment pracy bada transformatę Fouriera na skończonych grupach abelowych, definiując jej własności."

purpose_emb = model.encode([purpose], convert_to_numpy=True, normalize_embeddings=True)
section_emb = model.encode([section], convert_to_numpy=True, normalize_embeddings=True)

score = cosine_similarity(purpose_emb, section_emb)[0][0]
print(score)