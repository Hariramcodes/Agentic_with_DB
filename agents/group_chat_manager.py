from autogen import GroupChatManager, GroupChat
import logging
import re

logger = logging.getLogger(__name__)

class CustomGroupChat(GroupChat):
    """Custom GroupChat with proper speaker selection for retrieval agents and dual analyzer flow"""
    
    def select_speaker(self, last_speaker, selector):
        """Override the select_speaker method to implement custom logic for dual analyzer flow"""
        messages = self.messages
        total_messages = len(messages)
        
        # Debug info
        last_speaker_name = last_speaker.name if last_speaker else "None"
        
        # Get last message content safely
        last_message = ""
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                last_message = last_msg.get("content", "")
            else:
                last_message = str(last_msg)
        
        print(f"\n🔍 CUSTOM SPEAKER SELECTION")
        print(f"   Last speaker: {last_speaker_name}")
        print(f"   Total messages: {total_messages}")
        print(f"   Last message preview: {last_message[:100]}...")
        print(f"   Available agents: {[agent.name for agent in self.agents]}")
        
        # PRIORITY 1: Check for retrieval agent requests
        if "@" in last_message and "_RetrievalAgent:" in last_message:
            # Extract the retrieval agent name
            retrieval_pattern = r"@(\w+_RetrievalAgent):"
            retrieval_match = re.search(retrieval_pattern, last_message)
            if retrieval_match:
                retrieval_agent_name = retrieval_match.group(1)
                print(f"   🎯 RETRIEVAL REQUEST DETECTED: {retrieval_agent_name}")
                
                # Find the agent
                for agent in self.agents:
                    if agent.name == retrieval_agent_name:
                        print(f"   ✅ FOUND AND SELECTING: {retrieval_agent_name}")
                        return agent
                
                print(f"   ❌ Retrieval agent {retrieval_agent_name} not found!")
        
        # START: First message after initial scenario
        if total_messages == 1:
            for agent in self.agents:
                if agent.name == "UserProxyAgent":
                    print(f"   ✅ START: UserProxyAgent")
                    return agent
        
        # UserProxyAgent flow
        if last_speaker_name == "UserProxyAgent":
            print(f"   🔍 Analyzing UserProxy output...")
            
            # Check for VL_STATUS in all UserProxy messages
            all_user_messages = []
            for msg in messages:
                if isinstance(msg, dict) and msg.get('name') == 'UserProxyAgent':
                    all_user_messages.append(msg.get('content', ''))
            
            combined_text = " ".join(all_user_messages)
            
            if "VL_STATUS: NO_IMAGE_FOUND" in combined_text:
                for agent in self.agents:
                    if agent.name == "ChannelAgent":
                        print(f"   ✅ NO_IMAGE_FOUND → ChannelAgent")
                        return agent
            elif "VL_STATUS: IMAGE_FOUND" in combined_text:
                # NEW: For IMAGE_FOUND, we can start with either EntitlementAnalyzer or DamageAnalyzer
                # Check if either has already been called
                entitlement_called = any(
                    msg.get('name') == 'EntitlementAnalyzer' and 'ENTITLEMENT ANALYSIS COMPLETE' in msg.get('content', '')
                    for msg in messages if isinstance(msg, dict)
                )
                damage_called = any(
                    msg.get('name') == 'DamageAnalyzer' and 'DAMAGE ANALYSIS COMPLETE' in msg.get('content', '')
                    for msg in messages if isinstance(msg, dict)
                )
                
                if not entitlement_called and not damage_called:
                    # Neither called yet, start with EntitlementAnalyzer (you can change this order)
                    for agent in self.agents:
                        if agent.name == "EntitlementAnalyzer":
                            print(f"   ✅ IMAGE_FOUND → EntitlementAnalyzer (first)")
                            return agent
                elif entitlement_called and not damage_called:
                    # EntitlementAnalyzer done, call DamageAnalyzer
                    for agent in self.agents:
                        if agent.name == "DamageAnalyzer":
                            print(f"   ✅ EntitlementAnalyzer done → DamageAnalyzer")
                            return agent
                elif damage_called and not entitlement_called:
                    # DamageAnalyzer done, call EntitlementAnalyzer
                    for agent in self.agents:
                        if agent.name == "EntitlementAnalyzer":
                            print(f"   ✅ DamageAnalyzer done → EntitlementAnalyzer")
                            return agent
                else:
                    # Both called, go to DecisionOrchestrator
                    for agent in self.agents:
                        if agent.name == "DecisionOrchestrator":
                            print(f"   ✅ Both analyzers done → DecisionOrchestrator")
                            return agent
            else:
                print(f"   🔄 No VL_STATUS yet - continue UserProxy")
                return last_speaker
        
        # RetrievalAgent responses - return to requesting agent
        if "_RetrievalAgent" in last_speaker_name:
            requester_name = last_speaker_name.replace('_RetrievalAgent', '')
            for agent in self.agents:
                if agent.name == requester_name:
                    print(f"   ✅ {last_speaker_name} complete → {requester_name}")
                    return agent
        
        # EntitlementAnalyzer workflow
        if last_speaker_name == "EntitlementAnalyzer":
            print(f"   🎯 EntitlementAnalyzer workflow")
            
            # Check if analysis is complete
            if any(phrase in last_message for phrase in [
                "ENTITLEMENT ANALYSIS COMPLETE",
                "ENTITLEMENT DECISION:",
                "Ready for final decision making"
            ]):
                # Check if DamageAnalyzer has been called
                damage_called = any(
                    msg.get('name') == 'DamageAnalyzer' and 'DAMAGE ANALYSIS COMPLETE' in msg.get('content', '')
                    for msg in messages if isinstance(msg, dict)
                )
                
                if not damage_called:
                    for agent in self.agents:
                        if agent.name == "DamageAnalyzer":
                            print(f"   ✅ EntitlementAnalyzer complete → DamageAnalyzer")
                            return agent
                else:
                    for agent in self.agents:
                        if agent.name == "DecisionOrchestrator":
                            print(f"   ✅ Both analyzers complete → DecisionOrchestrator")
                            return agent
            
            # Check if waiting for retrieval
            if "@EntitlementAnalyzer_RetrievalAgent:" in last_message:
                print(f"   ⏳ Waiting for entitlement retrieval agent response...")
                for agent in self.agents:
                    if agent.name == "EntitlementAnalyzer_RetrievalAgent":
                        print(f"   ✅ Force selecting EntitlementAnalyzer_RetrievalAgent")
                        return agent
            
            print(f"   🔄 EntitlementAnalyzer continuing...")
            return last_speaker
        
        # NEW: DamageAnalyzer workflow
        if last_speaker_name == "DamageAnalyzer":
            print(f"   🎯 DamageAnalyzer workflow")
            
            # Check if analysis is complete
            if any(phrase in last_message for phrase in [
                "DAMAGE ANALYSIS COMPLETE",
                "DAMAGE DECISION:",
                "Ready for final decision making"
            ]):
                # Check if EntitlementAnalyzer has been called
                entitlement_called = any(
                    msg.get('name') == 'EntitlementAnalyzer' and 'ENTITLEMENT ANALYSIS COMPLETE' in msg.get('content', '')
                    for msg in messages if isinstance(msg, dict)
                )
                
                if not entitlement_called:
                    for agent in self.agents:
                        if agent.name == "EntitlementAnalyzer":
                            print(f"   ✅ DamageAnalyzer complete → EntitlementAnalyzer")
                            return agent
                else:
                    for agent in self.agents:
                        if agent.name == "DecisionOrchestrator":
                            print(f"   ✅ Both analyzers complete → DecisionOrchestrator")
                            return agent
            
            # Check if waiting for retrieval
            if "@DamageAnalyzer_RetrievalAgent:" in last_message:
                print(f"   ⏳ Waiting for damage retrieval agent response...")
                for agent in self.agents:
                    if agent.name == "DamageAnalyzer_RetrievalAgent":
                        print(f"   ✅ Force selecting DamageAnalyzer_RetrievalAgent")
                        return agent
            
            print(f"   🔄 DamageAnalyzer continuing...")
            return last_speaker
        
        # ChannelAgent workflow
        if last_speaker_name == "ChannelAgent":
            if any(phrase in last_message for phrase in [
                "Upload Instructions:",
                "CHANNEL AGENT ANALYSIS COMPLETE", 
                "Ready for final decision making"
            ]):
                for agent in self.agents:
                    if agent.name == "DecisionOrchestrator":
                        print(f"   ✅ ChannelAgent complete → DecisionOrchestrator")
                        return agent
            
            # Check if waiting for retrieval
            if "@ChannelAgent_RetrievalAgent:" in last_message:
                for agent in self.agents:
                    if agent.name == "ChannelAgent_RetrievalAgent":
                        print(f"   ✅ Force selecting ChannelAgent_RetrievalAgent")
                        return agent
                        
            print(f"   🔄 ChannelAgent continuing...")
            return None
        
        # DecisionOrchestrator ends conversation
        if last_speaker_name == "DecisionOrchestrator":
            print(f"   ✅ DecisionOrchestrator complete - CONVERSATION END")
            return None
        
        # Default: use the selector agent to decide
        print(f"   🔄 Unknown state - using selector agent")
        return selector.select_speaker(last_speaker, self)


class PureGroupChatManager(GroupChatManager):
    def __init__(self, groupchat, llm_config=None):
        super().__init__(
            groupchat=groupchat, 
            llm_config=llm_config,
            max_consecutive_auto_reply=30,
            human_input_mode="NEVER",
            is_termination_msg=lambda x: False
        )
        logger.info("Created PURE GroupChatManager with custom speaker selection")


def create_group_chat_manager(agents, llm_config):
    """Create enhanced group chat manager for dynamic workflow"""
    
    print(f"🔧 Creating CustomGroupChat with proper speaker selection")
    print(f"   👥 Agents: {[agent.name for agent in agents]}")
    
    logger.info(f"✅ Agent list: {[agent.name for agent in agents]}")
    
    # Create custom groupchat
    groupchat = CustomGroupChat(
        agents=agents,
        messages=[],
        max_round=40,  # Increased for dual analyzer flow
        speaker_selection_method="auto",  # This will use our overridden select_speaker
        allow_repeat_speaker=True,
        max_retries_for_selecting_speaker=5,
        enable_clear_history=False
    )
    
    manager = PureGroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config
    )
    
    print(f"   ✅ CustomGroupChat configured with overridden select_speaker method")
    print(f"   ✅ Max rounds: {groupchat.max_round}")
    
    return manager