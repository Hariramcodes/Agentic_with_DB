#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import the main workflow
from main import DellSupportWorkflow, TEST_SCENARIOS
from utils.rag_utils import test_rag_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkflowTester:
    """Comprehensive workflow tester"""
    
    def __init__(self):
        self.workflow = DellSupportWorkflow()
        self.test_results = {}
    
    async def test_rag_system(self):
        """Test RAG database connectivity"""
        logger.info("🧪 TESTING RAG SYSTEM")
        logger.info("=" * 60)
        
        try:
            success = await test_rag_connection()
            if success:
                logger.info("✅ RAG system test PASSED")
                return True
            else:
                logger.error("❌ RAG system test FAILED")
                return False
        except Exception as e:
            logger.error(f"❌ RAG system test ERROR: {e}")
            return False
    
    async def test_individual_agents(self):
        """Test individual agent responses"""
        logger.info("\n🧪 TESTING INDIVIDUAL AGENTS")
        logger.info("=" * 60)
        
        test_scenario = TEST_SCENARIOS["IMAGE_FOUND"]
        agent_tests = {}
        
        try:
            # Test UserProxy
            logger.info("\n1. Testing UserProxy...")
            user_response = self.workflow.safe_generate_reply(
                self.workflow.agents['user_proxy'],
                [{"content": test_scenario, "role": "user"}]
            )
            agent_tests['UserProxy'] = "PASS" if user_response and len(user_response) > 50 else "FAIL"
            logger.info(f"UserProxy: {agent_tests['UserProxy']} - {user_response[:100]}...")
            
            # Test EntitlementAnalyzer