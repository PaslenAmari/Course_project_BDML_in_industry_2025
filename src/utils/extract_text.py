import base64
import io
import logging
import os

from uuid import uuid4

import numpy as np
import pymupdf

from chromadb import Client
from chromadb.config import Settings
from openai import OpenAI
from PIL import Image
from yandex_cloud_ml_sdk import YCloudML

logger = logging.getLogger(__name__)


VLM_MODEL_NAME = os.environ.get("VLM_MODEL_NAME", "qwen3-30b-vl")

YANDEX_FOLDER_ID=os.environ.get("YANDEX_FOLDER_ID")
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")

CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "language_books")

client = OpenAI(
    base_url=os.environ.get("LITELLM_BASE_URL"),
    api_key=os.environ.get("LITELLM_API_KEY"),
)

sdk = YCloudML(
        folder_id=YANDEX_FOLDER_ID,
        auth=YANDEX_API_KEY,
    )
doc_embedding_model = sdk.models.text_embeddings(f"emb://{YANDEX_FOLDER_ID}/text-search-doc/latest")

chroma = Client(Settings(anonymized_telemetry=False))
collection = chroma.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={
        "hnsw:space": "cosine",
    },
)

def extract_text_vlm(base64_image: str) -> str:

    response = client.chat.completions.create(
        model=VLM_MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                    {
                        "type": "text",
                        "text": "Extract all text from this PDF. Preserve reading order.",
                    },
                ],
            },
        ],
    )

    return response.choices[0].message.content

def get_text_from_pdf_doc_vlm(pdf_doc: pymupdf.Document) -> str:
    texts = []
    for i, page in enumerate(pdf_doc):

        pix = page.get_pixmap(dpi=144)
        mode = "RGBA" if pix.alpha else "RGB" if pix.colorspace.n >= 3 else "L"
        image = Image.frombytes(mode, [pix.width, pix.height], pix.samples).conver("GGB")

        buffer = io.BytesIO()
        image.save(buffer, format="png")
        img_bytes = buffer.getvalue()
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        text = extract_text_vlm(base64_image)
        texts.append(text)
        logger.info(f"Processed page {i+1}/{len(pdf_doc)}.")

    return "\n".join(texts)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
        if end == len(text):
            break
    return chunks


def save_chunks_chroma(chunks: list[str]) -> None:
    embeddings = [np.array(doc_embedding_model.run(chunk)) for chunk in chunks]
    ids = [str(uuid4()) for _ in chunks]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
    )

    logger.info(f"Saved {len(chunks)} chunks in Chroma.")

if __name__ == "__main__":
    doc_path = "..."
    doc = pymupdf.open(doc_path)
    text = get_text_from_pdf_doc_vlm(doc)
    chunks = chunk_text(text)
    save_chunks_chroma(save_chunks_chroma)
