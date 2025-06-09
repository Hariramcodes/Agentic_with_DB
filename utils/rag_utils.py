import asyncpg
import logging
import json
import asyncio
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Database configuration
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

# Cache for model to avoid reloading
_model_cache = None

def get_sentence_transformer():
    """Get cached sentence transformer model"""
    global _model_cache
    if _model_cache is None:
        _model_cache = SentenceTransformer(EMBED_MODEL)
    return _model_cache

async def query_vector_db(pdf_name, query, k=5, region=None, language=None, table_name=None):
    """
    Optimized query function with better timeout handling
    
    Args:
        pdf_name: Name of the PDF to search in
        query: Search query
        k: Number of chunks to retrieve
        region: Customer region (optional)
        language: Customer language (optional)
        table_name: Optional table name override
    
    Returns:
        Dictionary with chunks, ids, and similarities
    """
    conn = None
    try:
        logger.info(f"Querying vector DB: pdf={pdf_name}, query='{query[:50]}...', k={k}, region={region}")
        
        # Connect to database with timeout
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(DB_CONN),
                timeout=5  # 5 second connection timeout
            )
        except asyncio.TimeoutError:
            logger.error("Database connection timeout")
            return {"chunks": [], "ids": [], "similarities": []}
        
        # Determine target table
        if table_name:
            target_table = table_name
        else:
            target_table = None
            for agent, pdfs in DOC_MAP.items():
                if pdf_name in pdfs:
                    target_table = TABLE_MAP.get(agent)
                    break
        
        if not target_table:
            logger.error(f"No table found for PDF: {pdf_name}")
            return {"chunks": [], "ids": [], "similarities": []}

        logger.info(f"Using table: {target_table} for PDF: {pdf_name}")

        # Enhanced query construction
        enhanced_query = query
        if region:
            enhanced_query = f"{query} {region}"
        if language:
            enhanced_query = f"{enhanced_query} {language}"
        
        logger.info(f"Enhanced query: {enhanced_query}")

        # Generate embedding for the query with timeout
        try:
            model = get_sentence_transformer()
            query_embedding = model.encode(enhanced_query, show_progress_bar=False).tolist()
            query_embedding_str = json.dumps(query_embedding)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return {"chunks": [], "ids": [], "similarities": []}

        # SQL query for cosine similarity search
        sql_query = f"""
            SELECT text, metadata, 1 - (embedding <=> $1::vector) AS similarity
            FROM {target_table}
            WHERE metadata->>'pdf_name' = $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """
        
        # Execute the query with timeout
        try:
            rows = await asyncio.wait_for(
                conn.fetch(sql_query, query_embedding_str, pdf_name, k),
                timeout=10  # 10 second query timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"SQL query timeout for {pdf_name}")
            return {"chunks": [], "ids": [], "similarities": []}
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return {"chunks": [], "ids": [], "similarities": []}
        
        # Extract results
        chunks = [row["text"] for row in rows]
        ids = [row["metadata"] for row in rows]
        similarities = [row["similarity"] for row in rows]

        logger.info(f"Retrieved {len(chunks)} chunks for {pdf_name}")
        
        # Log top chunks for debugging
        if chunks:
            logger.info(f"Top chunks retrieved:")
            for i, (chunk, sim) in enumerate(zip(chunks[:2], similarities[:2]), 1):
                logger.info(f"  Chunk {i} (Similarity: {sim:.4f}): {chunk[:100]}...")
        else:
            logger.warning(f"No chunks found for query in {pdf_name}")

        return {
            "chunks": chunks,
            "ids": ids,
            "similarities": similarities
        }
        
    except Exception as e:
        logger.error(f"Error querying vector database: {str(e)}")
        return {"chunks": [], "ids": [], "similarities": []}
    
    finally:
        if conn:
            try:
                await asyncio.wait_for(conn.close(), timeout=2)
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

async def query_entitlement_policies(service_tag, region, ad_status, incident_status, cooling_status):
    """
    Query entitlement policies for both AccidentalDamage.pdf and DELLSW.pdf
    """
    query = f"accidental damage entitlement {ad_status} incident {incident_status} cooling period {cooling_status} {region} eligibility criteria"
    
    results = []
    for pdf_name in DOC_MAP["EntitlementAnalyzer"]:
        try:
            pdf_results = await asyncio.wait_for(
                query_vector_db(
                    pdf_name=pdf_name,
                    query=query,
                    k=3,
                    region=region,
                    table_name="entitlement_analyzer"
                ),
                timeout=15
            )
            if pdf_results and pdf_results.get('chunks'):
                for i, chunk in enumerate(pdf_results['chunks']):
                    results.append({
                        'text': chunk,
                        'source': pdf_name,
                        'similarity': pdf_results.get('similarities', [0])[i]
                    })
        except asyncio.TimeoutError:
            logger.warning(f"Timeout querying {pdf_name}")
            continue
    
    # Sort by similarity and return top 5
    results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    return results[:5]

async def query_damage_guidelines(damage_description, damage_type, vl_output):
    """
    Query damage assessment guidelines for both BiohazardPNP.pdf and IDENTIFYMONITORDAMAGE.pdf
    """
    query = f"damage assessment {damage_type} customer induced {damage_description} {vl_output} coverage guidelines"
    
    results = []
    for pdf_name in DOC_MAP["DamageAnalyzer"]:
        try:
            pdf_results = await asyncio.wait_for(
                query_vector_db(
                    pdf_name=pdf_name,
                    query=query,
                    k=3,
                    table_name="damage_analyzer"
                ),
                timeout=15
            )
            if pdf_results and pdf_results.get('chunks'):
                for i, chunk in enumerate(pdf_results['chunks']):
                    results.append({
                        'text': chunk,
                        'source': pdf_name,
                        'similarity': pdf_results.get('similarities', [0])[i]
                    })
        except asyncio.TimeoutError:
            logger.warning(f"Timeout querying {pdf_name}")
            continue
    
    # Sort by similarity and return top 5
    results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    return results[:5]

async def query_upload_instructions(region, language="English"):
    """
    Query upload instructions for VL.pdf
    """
    query = f"upload instructions image submission {region} {language} contact details procedures"
    
    try:
        pdf_results = await asyncio.wait_for(
            query_vector_db(
                pdf_name="VL.pdf",
                query=query,
                k=5,
                region=region,
                language=language,
                table_name="channel_agent"
            ),
            timeout=15
        )
        
        results = []
        if pdf_results and pdf_results.get('chunks'):
            for i, chunk in enumerate(pdf_results['chunks']):
                results.append({
                    'text': chunk,
                    'source': "VL.pdf",
                    'similarity': pdf_results.get('similarities', [0])[i]
                })
        
        return results
    except asyncio.TimeoutError:
        logger.warning("Timeout querying upload instructions")
        return []

def query_vector_db_sync(pdf_name, query, k=5, region=None, language=None, table_name=None):
    """
    Synchronous wrapper for query_vector_db with better timeout handling
    """
    import asyncio
    import concurrent.futures
    
    def run_async_query():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                asyncio.wait_for(
                    query_vector_db(pdf_name, query, k, region, language, table_name),
                    timeout=20
                )
            )
        except asyncio.TimeoutError:
            logger.error(f"Sync query timeout for {pdf_name}")
            return {"chunks": [], "ids": [], "similarities": []}
        finally:
            loop.close()
    
    try:
        # Run in thread with overall timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_query)
            return future.result(timeout=25)
    except concurrent.futures.TimeoutError:
        logger.error(f"Thread executor timeout for {pdf_name}")
        return {"chunks": [], "ids": [], "similarities": []}
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
        return {"chunks": [], "ids": [], "similarities": []}

async def test_rag_connection():
    """Test RAG database connection and retrieval"""
    logger.info("Testing RAG database connection...")
    
    try:
        # Test connection
        conn = await asyncio.wait_for(asyncpg.connect(DB_CONN), timeout=5)
        logger.info("✅ Database connection successful")
        
        # Test table existence
        for agent, table in TABLE_MAP.items():
            try:
                result = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                logger.info(f"✅ Table {table} exists with {result} records")
            except Exception as e:
                logger.error(f"❌ Error checking table {table}: {e}")
        
        await conn.close()
        
        # Test retrieval
        test_result = await asyncio.wait_for(
            query_vector_db("AccidentalDamage.pdf", "entitlement eligibility", k=2),
            timeout=10
        )
        if test_result and test_result.get('chunks'):
            logger.info(f"✅ RAG retrieval test successful: {len(test_result['chunks'])} chunks retrieved")
        else:
            logger.warning("⚠️ RAG retrieval test returned no chunks")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG test failed: {e}")
        return False

if __name__ == "__main__":
    # Run RAG tests
    import asyncio
    asyncio.run(test_rag_connection())