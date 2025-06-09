import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.user_proxy import create_user_proxy
from agents.entitlement_analyzer import create_entitlement_analyzer
from agents.channel_agent import create_channel_agent
from agents.damage_analyzer import create_damage_analyzer
from agents.decision_orchestrator import create_decision_orchestrator
from agents.retrieval_agent import (
    create_entitlement_retrieval_agent, 
    create_channel_retrieval_agent,
    create_damage_retrieval_agent
)
from agents.group_chat_manager import create_group_chat_manager
from config.llm_config import llm_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the Dell support workflow"""
    logger.info("🚀 STARTING DELL SUPPORT WORKFLOW")
    
    # Sample scenario for testing - you can change this
    user_input = """Scenario details:
1. Service Tag: AXBYCZ6
2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days - so AD WO cannot be created
5. VL Model Output: VL Model did not detect any image, no data found or image not in proper format
6. Region: Australia
7. Damage Description: dropped the system"""
    
    logger.info(f"📋 Scenario: {user_input}")
    
    # IMPORTANT: Let's clarify the AD Entitlement status
    # The scenario says "has entitlement for Accidental damage or the same expired"
    # This is ambiguous - let's make it clear it's EXPIRED for testing
    
    print("\n📌 CLARIFICATION: Interpreting 'AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired' as EXPIRED status\n")
    
    # Create agents
    user_proxy = create_user_proxy(llm_config)
    
    # Create all agents including the new DamageAnalyzer
    entitlement_analyzer = create_entitlement_analyzer(llm_config)
    entitlement_retrieval = create_entitlement_retrieval_agent()
    
    # NEW: Add DamageAnalyzer and its retrieval agent
    damage_analyzer = create_damage_analyzer(llm_config, user_input)
    damage_retrieval = create_damage_retrieval_agent()
    
    channel_agent = create_channel_agent(llm_config)
    channel_retrieval = create_channel_retrieval_agent()
    
    decision_orchestrator = create_decision_orchestrator(llm_config)
    
    # Agent list - ORDER MATTERS for the group chat flow
    agents = [
        user_proxy,
        entitlement_analyzer,
        entitlement_retrieval,
        damage_analyzer,
        damage_retrieval,
        channel_agent,
        channel_retrieval,
        decision_orchestrator
    ]
    
    # Verify agent list
    agent_names = [agent.name for agent in agents]
    logger.info(f"✅ Agent list: {agent_names}")
    
    # Create group chat manager
    manager = create_group_chat_manager(agents, llm_config)
    
    logger.info("🎯 Starting conversation - Expected flow for IMAGE_FOUND scenario:")
    logger.info("   1. UserProxy → Analyzes scenario, determines VL_STATUS")
    logger.info("   2. EntitlementAnalyzer → Requests retrieval")
    logger.info("   3. EntitlementAnalyzer_RetrievalAgent → Fetches chunks")
    logger.info("   4. EntitlementAnalyzer → Analyzes with chunks")
    logger.info("   5. DamageAnalyzer → Requests retrieval")
    logger.info("   6. DamageAnalyzer_RetrievalAgent → Fetches chunks")
    logger.info("   7. DamageAnalyzer → Analyzes with chunks")
    logger.info("   8. DecisionOrchestrator → Makes final decision")
    
    # Start the conversation
    try:
        result = user_proxy.initiate_chat(
            manager,
            message=user_input,
            max_turns=25  # Increased for more complex flow
        )
        
        # Log conversation summary
        total_turns = len(manager.groupchat.messages)
        final_speaker = manager.groupchat.messages[-1].get('name', 'Unknown') if manager.groupchat.messages else 'None'
        
        logger.info("✅ CONVERSATION COMPLETED")
        print(f"\n📊 CONVERSATION SUMMARY:")
        print(f"   Total turns: {total_turns}")
        print(f"   Total messages: {len(manager.groupchat.messages)}")
        print(f"   Final speaker: {final_speaker}")
        
        # Check if retrieval was called for both agents
        entitlement_retrieval_called = any(
            "EntitlementAnalyzer_RetrievalAgent" in msg.get('name', '') and "Retrieved chunks:" in msg.get('content', '')
            for msg in manager.groupchat.messages 
            if isinstance(msg, dict)
        )
        
        damage_retrieval_called = any(
            "DamageAnalyzer_RetrievalAgent" in msg.get('name', '') and "Retrieved chunks:" in msg.get('content', '')
            for msg in manager.groupchat.messages 
            if isinstance(msg, dict)
        )
        
        if entitlement_retrieval_called:
            print(f"   ✅ EntitlementAnalyzer retrieval was properly called")
        else:
            print(f"   ❌ WARNING: EntitlementAnalyzer retrieval was NOT called!")
        
        if damage_retrieval_called:
            print(f"   ✅ DamageAnalyzer retrieval was properly called")
        else:
            print(f"   ❌ WARNING: DamageAnalyzer retrieval was NOT called!")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Conversation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()