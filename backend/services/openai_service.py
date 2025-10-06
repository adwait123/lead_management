"""
OpenAI Service
Handles all OpenAI API interactions for chat completions and prompt generation
"""

import os
import openai
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        """Initialize OpenAI service with API key from environment"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.available = False
        else:
            openai.api_key = self.api_key
            self.available = True

    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.available

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate chat completion using OpenAI API

        Args:
            messages: List of message objects with 'role' and 'content'
            model: OpenAI model to use
            temperature: Creativity level (0-1)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt to prepend

        Returns:
            Dict with response, usage info, and metadata
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="OpenAI service is not available. Please check API key configuration."
            )

        try:
            # Prepare messages with system prompt if provided
            formatted_messages = []

            if system_prompt:
                formatted_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # Add conversation messages
            formatted_messages.extend(messages)

            # Make API call using old API format
            response = openai.ChatCompletion.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                "response": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason,
                "success": True,
                "error": None
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "response": None,
                "model": model,
                "usage": None,
                "finish_reason": None,
                "success": False,
                "error": str(e)
            }

    async def generate_prompt_from_summary(
        self,
        summary: str,
        agent_type: str = "customer_service",
        industry: str = "general",
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Generate a detailed agent prompt from a brief summary

        Args:
            summary: Brief description of what the agent should do
            agent_type: Type of agent (customer_service, sales, support, etc.)
            industry: Industry context (home_services, healthcare, etc.)
            model: OpenAI model to use

        Returns:
            Dict with generated prompt and metadata
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="OpenAI service is not available. Please check API key configuration."
            )

        # Create a comprehensive prompt generation request
        system_prompt = f"""You are an expert AI prompt engineer specializing in creating detailed, effective prompts for AI customer service agents.

Given a brief summary, create a comprehensive, professional prompt that includes:

1. **Role Definition**: Clear identity and purpose
2. **Personality Traits**: Professional, helpful tone appropriate for {industry}
3. **Core Responsibilities**: What the agent should accomplish
4. **Communication Style**: How to interact with customers
5. **Tools & Commands**: Include relevant slash commands like /appointment, /transfer, /bailout, /knowledge
6. **Guidelines**: Best practices and do's/don'ts
7. **Example Interactions**: Brief examples of how to handle common scenarios

The prompt should be detailed enough to guide an AI agent's behavior but concise enough to be practical.

Industry Context: {industry}
Agent Type: {agent_type}

Format the response as a complete, ready-to-use system prompt."""

        user_prompt = f"Create a detailed AI agent prompt based on this summary: {summary}"

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            return {
                "generated_prompt": response.choices[0].message.content,
                "summary": summary,
                "agent_type": agent_type,
                "industry": industry,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "success": True,
                "error": None
            }

        except Exception as e:
            logger.error(f"Prompt generation error: {str(e)}")
            return {
                "generated_prompt": None,
                "summary": summary,
                "agent_type": agent_type,
                "industry": industry,
                "model": model,
                "usage": None,
                "success": False,
                "error": str(e)
            }

    async def generate_scenario_prompt(
        self,
        scenario_description: str,
        business_context: Optional[Dict[str, Any]] = None,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Generate a complete agent prompt from a basic scenario description

        Args:
            scenario_description: Basic description of the scenario
            business_context: Optional business details (name, services, etc.)
            model: OpenAI model to use

        Returns:
            Dict with generated prompt, suggested tools, and metadata
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="OpenAI service is not available. Please check API key configuration."
            )

        # Build context for better prompt generation
        context_info = ""
        if business_context:
            context_info = f"""
Business Context:
- Business Name: {business_context.get('name', 'Not specified')}
- Industry: {business_context.get('industry', 'Not specified')}
- Services: {business_context.get('services', 'Not specified')}
- Target Customers: {business_context.get('target_customers', 'General customers')}
"""

        system_prompt = f"""You are an expert AI agent designer. Create a comprehensive agent prompt for the given scenario.

{context_info}

Your response should include:

1. **Complete System Prompt**: A detailed, ready-to-use prompt that defines the agent's role, personality, and behavior
2. **Recommended Tools**: List of slash commands that would be useful (/appointment, /transfer, /bailout, /knowledge)
3. **Key Personality Traits**: Suggested traits (professional, friendly, efficient, etc.)
4. **Communication Mode**: Voice, text, or both
5. **Sample Interactions**: 2-3 example conversations

Format your response as JSON with these keys:
- "system_prompt": The complete prompt text
- "recommended_tools": Array of tool names
- "personality_traits": Array of trait names
- "communication_mode": "voice", "text", or "both"
- "sample_interactions": Array of interaction examples
- "suggested_business_hours": Default business hours if applicable
- "emergency_handling": How to handle urgent/emergency situations

Make the prompt comprehensive but practical for real-world use."""

        user_prompt = f"Create a complete AI agent setup for this scenario: {scenario_description}"

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )

            # Try to parse the JSON response
            try:
                generated_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw content
                generated_data = {
                    "system_prompt": response.choices[0].message.content,
                    "recommended_tools": ["/appointment", "/transfer", "/bailout", "/knowledge"],
                    "personality_traits": ["professional", "helpful"],
                    "communication_mode": "both",
                    "sample_interactions": [],
                    "suggested_business_hours": "9 AM - 5 PM",
                    "emergency_handling": "Transfer to emergency team"
                }

            return {
                "scenario_description": scenario_description,
                "generated_data": generated_data,
                "business_context": business_context,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "success": True,
                "error": None
            }

        except Exception as e:
            logger.error(f"Scenario prompt generation error: {str(e)}")
            return {
                "scenario_description": scenario_description,
                "generated_data": None,
                "business_context": business_context,
                "model": model,
                "usage": None,
                "success": False,
                "error": str(e)
            }

    async def analyze_tools_needed(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Analyze a prompt and suggest which tools should be configured

        Args:
            prompt: The agent prompt to analyze
            model: OpenAI model to use

        Returns:
            Dict with suggested tools and configuration recommendations
        """
        if not self.is_available():
            return {
                "suggested_tools": ["/appointment", "/transfer", "/bailout", "/knowledge"],
                "tool_priorities": {"high": [], "medium": [], "low": []},
                "success": False,
                "error": "OpenAI service not available"
            }

        system_prompt = """Analyze the given AI agent prompt and recommend which tools should be configured based on the agent's role and responsibilities.

Available tools:
- /appointment: For booking/scheduling appointments
- /transfer: For transferring to human agents or teams
- /bailout: For ending conversations with proper disposition
- /knowledge: For accessing business information and FAQs

Respond with JSON containing:
- "suggested_tools": Array of recommended tool names
- "tool_priorities": Object with "high", "medium", "low" arrays
- "reasoning": Brief explanation for each tool recommendation"""

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this prompt: {prompt}"}
                ],
                temperature=0.3,
                max_tokens=500
            )

            try:
                analysis = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = {
                    "suggested_tools": ["/appointment", "/transfer", "/bailout", "/knowledge"],
                    "tool_priorities": {
                        "high": ["/appointment", "/transfer"],
                        "medium": ["/bailout"],
                        "low": ["/knowledge"]
                    },
                    "reasoning": "Standard tool set for customer service agents"
                }

            return {
                **analysis,
                "success": True,
                "error": None
            }

        except Exception as e:
            logger.error(f"Tool analysis error: {str(e)}")
            return {
                "suggested_tools": ["/appointment", "/transfer", "/bailout", "/knowledge"],
                "tool_priorities": {"high": [], "medium": [], "low": []},
                "success": False,
                "error": str(e)
            }

# Global service instance - lazy initialization to avoid startup errors
openai_service = None

def get_openai_service():
    global openai_service
    if openai_service is None:
        try:
            openai_service = OpenAIService()
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            # Create a mock service that gracefully handles failures
            openai_service = type('MockOpenAIService', (), {
                'is_available': lambda: False,
                'available': False
            })()
    return openai_service