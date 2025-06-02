import asyncpg
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import nltk
import uuid
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONN = "postgresql://postgres:myragpw@0.0.0.0:5434/ragdb2"
CHUNK_TOKENS = 800
EMBED_MODEL = "thenlper/gte-large"

# Agent-to-PDF mapping
AGENT_PDF_MAP = {
    "channel_agent": ["VL.pdf"],
    "entitlement_analyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
    "damage_analyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]
}

async def create_tables(conn):
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        logger.info("Enabled vector extension")
        # Drop existing tables to avoid conflicts
        for table_name in AGENT_PDF_MAP.keys():
            await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        # Create table for each agent
        for table_name in AGENT_PDF_MAP.keys():
            await conn.execute(f"""
                CREATE TABLE {table_name} (
                    id UUID PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding VECTOR(1024),
                    metadata JSONB NOT NULL
                )
            """)
            logger.info(f"Created table '{table_name}'")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def chunk_text(text, page_number, chunk_size=CHUNK_TOKENS):
    try:
        # Normalize text: replace multiple spaces/tabs with single space, keep \n\n
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\n+', '\n\n', text)
        # Infer paragraph breaks for headings or bullets
        text = re.sub(r'(\n\s*•|\n\s*\d+\.)', r'\n\n\1', text)
        
        logger.info(f"Page {page_number}: Raw text length: {len(text)} characters")
        
        # Split into paragraphs
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        current_tokens = 0

        logger.info(f"Page {page_number}: Found {len(paragraphs)} paragraphs")
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            tokens = len(nltk.word_tokenize(paragraph))
            
            if tokens > chunk_size:
                # Paragraph too large, split into sentences
                sentences = nltk.sent_tokenize(paragraph)
                logger.info(f"Page {page_number}: Paragraph too large ({tokens} tokens), splitting into {len(sentences)} sentences")
                temp_chunk = ""
                temp_tokens = 0
                for sentence in sentences:
                    sentence_tokens = len(nltk.word_tokenize(sentence))
                    if temp_tokens + sentence_tokens <= chunk_size:
                        temp_chunk += " " + sentence
                        temp_tokens += sentence_tokens
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = sentence
                        temp_tokens = sentence_tokens
                if temp_chunk:
                    chunks.append(temp_chunk.strip())
            else:
                # Paragraph fits, add to current chunk
                if current_tokens + tokens <= chunk_size:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                    current_tokens += tokens
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = paragraph
                    current_tokens = tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Page {page_number}: Chunked text into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks, 1):
            tokens = len(nltk.word_tokenize(chunk))
            logger.info(f"Page {page_number}: Chunk {i}: {tokens} tokens, Content: {chunk[:200]}...")
        return chunks
    except Exception as e:
        logger.error(f"Error chunking text on page {page_number}: {e}")
        return []

async def populate_database():
    try:
        model = SentenceTransformer(EMBED_MODEL)
        logger.info(f"Loaded embedding model: {EMBED_MODEL}")
        conn = await asyncpg.connect(DB_CONN)
        logger.info("Connected to database")
        async with conn.transaction():
            await create_tables(conn)
        docs_dir = Path("docs")
        if not docs_dir.exists():
            logger.error("docs/ directory does not exist")
            await conn.close()
            return
        pdf_files = list(docs_dir.glob("*.pdf"))
        if not pdf_files:
            logger.error("No PDF files found in docs/")
            await conn.close()
            return
        for pdf_path in pdf_files:
            pdf_name = pdf_path.name
            # Find which agent table to use
            table_name = None
            for agent, pdfs in AGENT_PDF_MAP.items():
                if pdf_name in pdfs:
                    table_name = agent
                    break
            if not table_name:
                logger.warning(f"No agent assigned for {pdf_name}, skipping")
                continue
            logger.info(f"Processing {pdf_path} for table {table_name}")
            try:
                reader = PdfReader(pdf_path)
                for page_number, page in enumerate(reader.pages, 1):
                    text = page.extract_text() or ""
                    if not text.strip():
                        logger.warning(f"No text extracted from {pdf_path} page {page_number}")
                        continue
                    chunks = chunk_text(text, page_number)
                    if not chunks:
                        logger.warning(f"No chunks created for {pdf_path} page {page_number}")
                        continue
                    for chunk in chunks:
                        doc_id = str(uuid.uuid4())
                        embedding = model.encode(chunk).tolist()
                        embedding_str = json.dumps(embedding)
                        metadata = {
                            "pdf_name": pdf_name,
                            "page_number": page_number
                        }
                        async with conn.transaction():
                            await conn.execute(
                                f"INSERT INTO {table_name} (id, text, embedding, metadata) VALUES ($1, $2, $3::vector, $4::jsonb)",
                                doc_id, chunk, embedding_str, json.dumps(metadata)
                            )
                            logger.info(f"Inserted chunk for {pdf_name}, Page: {page_number}, ID: {doc_id}, Table: {table_name}, Content: {chunk[:200]}...")
                logger.info(f"Completed processing {pdf_path}: {len(chunks)} chunks in table {table_name}")
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                continue
        await conn.close()
        logger.info("Database population completed")
    except Exception as e:
        logger.error(f"Error populating database: {e}")

if __name__ == "__main__":
    import asyncio
    nltk.download('punkt')
    nltk.download('punkt_tab')
    asyncio.run(populate_database())