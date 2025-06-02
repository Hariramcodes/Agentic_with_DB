import asyncpg
import asyncio
import logging
import json
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONN = "postgresql://postgres:myragpw@0.0.0.0:5434/ragdb2"
EMBED_MODEL = "thenlper/gte-large"

async def check_vector_extension(conn):
    try:
        result = await conn.fetchval("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        logger.info(f"Vector extension enabled: {result}")
        return result
    except Exception as e:
        logger.error(f"Error checking vector extension: {e}")
        return False

async def list_tables(conn):
    try:
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        table_names = [table['tablename'] for table in tables]
        logger.info(f"Existing tables: {table_names}")
        return table_names
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return []

async def check_schema(conn, table_name):
    try:
        schema_query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = $1 AND column_name = 'embedding'
        """
        result = await conn.fetchrow(schema_query, table_name)
        if result:
            logger.info(f"Schema for {table_name}.embedding: {result['data_type']}")
            return result['data_type']
        else:
            logger.error(f"No embedding column found in {table_name}")
            return None
    except Exception as e:
        logger.error(f"Error checking schema for {table_name}: {e}")
        return None

async def inspect_table(conn, table_name, pdf_name):
    try:
        # Check schema
        embedding_type = await check_schema(conn, table_name)
        if embedding_type != 'vector':
            logger.warning(f"Embedding column in {table_name} is {embedding_type}, expected 'vector'")

        pdf_query = f"SELECT DISTINCT metadata->>'pdf_name' AS pdf_name FROM {table_name}"
        pdfs = await conn.fetch(pdf_query)
        pdf_names = [pdf['pdf_name'] for pdf in pdfs]
        logger.info(f"PDFs in {table_name}: {pdf_names}")

        if pdf_name in pdf_names:
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE metadata->>'pdf_name' = $1"
            total_chunks = await conn.fetchval(count_query, pdf_name)
            logger.info(f"Total chunks for {pdf_name} in {table_name}: {total_chunks}")

            # Skip dimension check if not vector type
            embedding_dim = None
            if embedding_type == 'vector':
                dim_query = f"SELECT array_dims(embedding) FROM {table_name} WHERE metadata->>'pdf_name' = $1 LIMIT 1"
                dim_result = await conn.fetchval(dim_query, pdf_name)
                if dim_result:
                    embedding_dim = int(dim_result.split(':')[1].strip(']'))
                    logger.info(f"Embedding dimension for {pdf_name}: {embedding_dim}")

            chunks_query = f"""
                SELECT text, metadata, embedding
                FROM {table_name}
                WHERE metadata->>'pdf_name' = $1
                LIMIT 10
            """
            chunks = await conn.fetch(chunks_query, pdf_name)
            logger.info(f"Contents for {pdf_name} (Top 10 chunks):")
            for i, chunk in enumerate(chunks, 1):
                print(f"Chunk {i}:")
                print(f"  Text: {chunk['text'][:300]}...")
                print(f"  Metadata: {chunk['metadata']}")
                print(f"  Embedding (first 5 dims): {chunk['embedding'][:5]}...")
                print()

            # Test cosine similarity
            model = SentenceTransformer(EMBED_MODEL)
            sample_query = f"French speaking France region" #Image upload instructions for Dell support in location France speaking French
            query_embedding = model.encode(sample_query).tolist()
            query_embedding_str = json.dumps(query_embedding)
            similarity_query = f"""
                SELECT text, metadata, 1 - (embedding <=> $1::vector) AS similarity
                FROM {table_name}
                WHERE metadata->>'pdf_name' = $2
                ORDER BY embedding <=> $1::vector
                LIMIT 5
            """
            similar_chunks = await conn.fetch(similarity_query, query_embedding_str, pdf_name)
            logger.info(f"Top 5 cosine similarity chunks for query: {sample_query[:50]}...")
            for i, chunk in enumerate(similar_chunks, 1):
                print(f"Similar Chunk {i}:")
                print(f"  Text: {chunk['text'][:300]}...")
                print(f"  Similarity: {chunk['similarity']:.4f}")
                print(f"  Metadata: {chunk['metadata']}")
                print()
    except Exception as e:
        logger.error(f"Error inspecting table {table_name}: {e}")

async def main():
    try:
        conn = await asyncpg.connect(DB_CONN)
        logger.info("Connected to database")

        await check_vector_extension(conn)
        tables = await list_tables(conn)

        for table in tables:
            if table in ['channel_agent', 'entitlement_analyzer', 'damage_analyzer']:
                agent_name = table.replace('_', ' ').title().replace(' Agent', 'Agent')
                logger.info(f"Inspecting agent: {agent_name}")
                await inspect_table(conn, table, 'VL.pdf')

        await conn.close()
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())