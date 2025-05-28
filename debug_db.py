import asyncpg
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONN = "postgresql://postgres:myragpw@localhost:5432/ragdb2"

# Agent-to-table mapping
TABLE_MAP = {
    "ChannelAgent": "channel_agent",
    "EntitlementAnalyzer": "entitlement_analyzer",
    "DamageAnalyzer": "damage_analyzer"
}

async def check_database():
    try:
        conn = await asyncpg.connect(DB_CONN)
        logger.info("Connected to database")

        # Check vector extension
        ext = await conn.fetchval("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        print(f"Vector extension enabled: {ext}")
        if not ext:
            print("Warning: 'vector' extension missing")

        # Check table existence
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        table_names = [row['table_name'] for row in tables]
        print("Existing tables:", table_names)
        expected_tables = list(TABLE_MAP.values())
        for table in expected_tables:
            if table not in table_names:
                print(f"Warning: '{table}' table missing")

        # Inspect each agent table
        for agent, table_name in TABLE_MAP.items():
            if table_name not in table_names:
                continue
            print(f"\nInspecting table: {table_name} (Agent: {agent})")
            
            # Get distinct PDFs
            pdfs = await conn.fetch(f"SELECT DISTINCT metadata->>'pdf_name' AS pdf_name FROM {table_name}")
            pdf_list = [row['pdf_name'] for row in pdfs]
            print(f"PDFs in {table_name}: {pdf_list}")

            # Check chunks and metadata for each PDF
            for pdf_name in pdf_list:
                doc_count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM {table_name} WHERE metadata->>'pdf_name' = $1", pdf_name
                )
                print(f"\nTotal chunks for {pdf_name} in {table_name}: {doc_count}")
                rows = await conn.fetch(
                    f"SELECT text, metadata FROM {table_name} WHERE metadata->>'pdf_name' = $1", pdf_name
                )
                print(f"Contents for {pdf_name} (All chunks):")
                if rows:
                    for i, row in enumerate(rows, 1):
                        metadata = row['metadata']
                        print(f"Chunk {i}:")
                        print(f"  Text: {row['text'][:200]}...")
                        print(f"  Metadata: {metadata}")
                else:
                    print(f"No chunks found for {pdf_name} in {table_name}.")

            # Check French/France content for VL.pdf in channel_agent
            if table_name == "channel_agent" and "VL.pdf" in pdf_list:
                query = f"""
                    SELECT text, metadata
                    FROM {table_name}
                    WHERE metadata->>'pdf_name' = 'VL.pdf'
                    AND (text ILIKE '%French%' OR text ILIKE '%France%')
                """
                print(f"\nExecuting query: {query}")
                french_rows = await conn.fetch(query)
                print("France/French-related chunks in VL.pdf:")
                if french_rows:
                    for i, row in enumerate(french_rows, 1):
                        print(f"French Chunk {i}:")
                        print(f"  Text: {row['text']}")
                        print(f"  Metadata: {row['metadata']}")
                else:
                    print("No France/French-related content found in VL.pdf.")

                # Check WhatsApp content
                query = f"""
                    SELECT text, metadata
                    FROM {table_name}
                    WHERE metadata->>'pdf_name' = 'VL.pdf'
                    AND text ILIKE '%WhatsApp%'
                """
                print(f"\nExecuting query: {query}")
                whatsapp_rows = await conn.fetch(query)
                print("WhatsApp-related chunks in VL.pdf:")
                if whatsapp_rows:
                    for i, row in enumerate(whatsapp_rows, 1):
                        print(f"WhatsApp Chunk {i}:")
                        print(f"  Text: {row['text']}")
                        print(f"  Metadata: {row['metadata']}")
                else:
                    print("No WhatsApp-related content found in VL.pdf.")

        # Check total chunks across all tables
        total_chunks = 0
        for table_name in expected_tables:
            if table_name in table_names:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                total_chunks += count
        print(f"\nTotal chunks across all tables: {total_chunks}")

        await conn.close()
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        print(f"Error checking database: {e}")

async def check_ollama():
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        print(f"\nOllama server status: {response.status_code}")
        if response.status_code == 200:
            print(f"Available models: {response.json().get('models', [])}")
    except Exception as e:
        print(f"Error checking Ollama: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_database())
    asyncio.run(check_ollama())