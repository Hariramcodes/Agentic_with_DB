import asyncpg
import logging
import json
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DB_CONN = "postgresql://postgres:myragpw@localhost:5432/ragdb2"
EMBED_MODEL = "thenlper/gte-large"

TABLE_MAP = {
    "ChannelAgent": "channel_agent",
    "EntitlementAnalyzer": "entitlement_analyzer",
    "DamageAnalyzer": "damage_analyzer"
}

DOC_MAP = {
    "ChannelAgent": ["VL.pdf"],
    "EntitlementAnalyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
    "DamageAnalyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]
}

async def query_vector_db(pdf_name, query, k=5, region=None, language=None):
    try:
        conn = await asyncpg.connect(DB_CONN)
        table_name = TABLE_MAP.get("ChannelAgent") if pdf_name in DOC_MAP["ChannelAgent"] else None
        if not table_name:
            logger.error(f"No table found for PDF: {pdf_name}")
            await conn.close()
            return {"chunks": [], "ids": []}

        # Construct query with region and language
        full_query = f"{query} in location {region} language {language}"
        model = SentenceTransformer(EMBED_MODEL)
        query_embedding = model.encode(full_query).tolist()
        query_embedding_str = json.dumps(query_embedding)

        query_str = f"""
            SELECT text, metadata, 1 - (embedding <=> $1::vector) AS similarity
            FROM {table_name}
            WHERE metadata->>'pdf_name' = $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """
        params = [query_embedding_str, pdf_name, k]
        logger.debug(f"Executing query: {query_str} with params: [embedding, {pdf_name}, {k}]")
        rows = await conn.fetch(query_str, *params)
        chunks = [row["text"] for row in rows]
        ids = [row["metadata"] for row in rows]
        similarities = [row["similarity"] for row in rows]

        logger.info(f"Retrieved {len(chunks)} chunks for {pdf_name} with query: {full_query}")
        print(f"\nTop {len(chunks)} chunks for query '{full_query}':")
        for i, (chunk, sim) in enumerate(zip(chunks, similarities), 1):
            print(f"Chunk {i} (Similarity: {sim:.4f}): {chunk[:300]}...")

        await conn.close()
        return {"chunks": chunks, "ids": ids}
    except Exception as e:
        logger.error(f"Error querying vector DB: {e}")
        print(f"Error querying DB: {e}")
        return {"chunks": [], "ids": []}