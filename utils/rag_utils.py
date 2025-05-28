import asyncpg
import logging

logger = logging.getLogger(__name__)

DB_CONN = "postgresql://postgres:myragpw@localhost:5432/ragdb2"

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

        query_str = f"""
            SELECT text, metadata
            FROM {table_name}
            WHERE metadata->>'pdf_name' = $1
            AND (
                text ILIKE $2
                OR text ILIKE $3
                OR text ILIKE '%upload%'
                OR text ILIKE '%image%'
                OR text ILIKE '%send%'
                OR text ILIKE '%submit%'
            )
            AND (
                text ILIKE $2  -- Ensure region is present
                AND text ILIKE $3  -- Ensure language is present
            )
            LIMIT $4
        """
        params = [pdf_name, f'%{region}%', f'%{language}%', k]
        logger.debug(f"Executing query: {query_str} with params: {params}")
        rows = await conn.fetch(query_str, *params)
        chunks = [row["text"] for row in rows]
        ids = [row["metadata"] for row in rows]

        logger.info(f"Retrieved {len(chunks)} chunks for {pdf_name} with query: {query}")
        print(f"\nTop {len(chunks)} chunks for query '{query}':")
        for i, chunk in enumerate(chunks, 1):
            print(f"Chunk {i}: {chunk[:300]}...")

        await conn.close()
        return {"chunks": chunks, "ids": ids}
    except Exception as e:
        logger.error(f"Error querying vector DB: {e}")
        print(f"Error querying DB: {e}")
        return {"chunks": [], "ids": []}