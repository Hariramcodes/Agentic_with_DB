from sentence_transformers import SentenceTransformer
import asyncpg
from pathlib import Path
from utils.rag_utils import pdf_to_txt
import asyncio
import logging

logger = logging.getLogger(__name__)

async def populate_db():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    conn = await asyncpg.connect("postgresql://postgres:myragpw@localhost:5432/ragdb2")
    pdfs = ["VL.pdf", "AccidentalDamage.pdf", "DELLSW.pdf", "BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]
    for pdf in pdfs:
        try:
            txt_path = pdf_to_txt(Path("docs") / pdf)
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            chunks = [content[i:i+200] for i in range(0, len(content), 200)]
            for chunk in chunks:
                embedding = model.encode(chunk).tolist()
                await conn.execute(
                    "INSERT INTO documents (pdf_name, content, embedding) VALUES ($1, $2, $3)",
                    pdf, chunk, embedding
                )
                logger.info(f"Inserted chunk for {pdf}")
        except Exception as e:
            logger.error(f"Error processing {pdf}: {e}")
    await conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(populate_db())