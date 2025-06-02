import asyncpg
import logging
import json
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Updated connection string to match your debug_db.py
DB_CONN = "postgresql://postgres:myragpw@0.0.0.0:5434/ragdb2"
EMBED_MODEL = "thenlper/gte-large"

# Agent to table mapping
TABLE_MAP = {
    "ChannelAgent": "channel_agent",
    "EntitlementAnalyzer": "entitlement_analyzer", 
    "DamageAnalyzer": "damage_analyzer"
}

# Agent to document mapping
DOC_MAP = {
    "ChannelAgent": ["VL.pdf"],
    "EntitlementAnalyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
    "DamageAnalyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]
}

async def query_vector_db(pdf_name, query, k=5, region=None, language=None):
    """
    Query the vector database for relevant chunks
    
    Args:
        pdf_name: Name of the PDF to search in
        query: Search query
        k: Number of chunks to retrieve
        region: Customer region
        language: Customer language
    
    Returns:
        Dictionary with chunks and metadata
    """
    conn = None
    try:
        logger.info(f"query_vector_db called with pdf_name={pdf_name}, query='{query}', k={k}, region={region}, language={language}")
        
        # Connect to database
        conn = await asyncpg.connect(DB_CONN)
        logger.info("Connected to database successfully")
        
        # Determine which table to query based on PDF name
        table_name = None
        for agent, pdfs in DOC_MAP.items():
            if pdf_name in pdfs:
                table_name = TABLE_MAP.get(agent)
                break
        
        if not table_name:
            logger.error(f"No table found for PDF: {pdf_name}")
            return {"chunks": [], "ids": []}

        logger.info(f"Using table: {table_name} for PDF: {pdf_name}")

        # Enhanced query construction with region and language context
        if region and language:
            enhanced_query = f"{query} {region} {language} support instructions contact details upload"
        else:
            enhanced_query = f"{query} support instructions contact details upload"
        
        logger.info(f"Enhanced query: {enhanced_query}")

        # Generate embedding for the query
        model = SentenceTransformer(EMBED_MODEL)
        query_embedding = model.encode(enhanced_query).tolist()
        query_embedding_str = json.dumps(query_embedding)

        # Construct the SQL query for cosine similarity search
        sql_query = f"""
            SELECT text, metadata, 1 - (embedding <=> $1::vector) AS similarity
            FROM {table_name}
            WHERE metadata->>'pdf_name' = $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """
        
        params = [query_embedding_str, pdf_name, k]
        logger.info(f"Executing SQL query with params: embedding_vector, {pdf_name}, {k}")
        
        # Execute the query
        rows = await conn.fetch(sql_query, *params)
        
        # Extract results
        chunks = [row["text"] for row in rows]
        ids = [row["metadata"] for row in rows]
        similarities = [row["similarity"] for row in rows]

        logger.info(f"Retrieved {len(chunks)} chunks for {pdf_name}")
        
        # Log the retrieved chunks for debugging
        if chunks:
            logger.info(f"Top {len(chunks)} chunks retrieved:")
            for i, (chunk, sim) in enumerate(zip(chunks, similarities), 1):
                logger.info(f"Chunk {i} (Similarity: {sim:.4f}): {chunk[:150]}...")
        else:
            logger.warning(f"No chunks found for query: {enhanced_query}")

        return {
            "chunks": chunks,
            "ids": ids,
            "similarities": similarities
        }
        
    except Exception as e:
        logger.error(f"Error querying vector database: {str(e)}")
        return {"chunks": [], "ids": []}
    
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed")
