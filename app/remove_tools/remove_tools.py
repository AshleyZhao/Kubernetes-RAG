import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Load environment variables from a .env file
load_dotenv(override=True)

# Get credentials from environment variables
ai_foundry_endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
action_agent_id = os.getenv("ACTION_AGENT_ID")

if not ai_foundry_endpoint or not action_agent_id:
    print("Please set the AZURE_AI_FOUNDRY_ENDPOINT and ACTION_AGENT_ID environment variables.")
    exit()

# Initialize the Azure AI Project Client
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=ai_foundry_endpoint)

try:
    # Get the existing action agent
    agent = project.agents.get_agent(action_agent_id)

    # Set the agent's tool definitions to an empty list
    agent.tool_definitions = []
    updated_agent = project.agents.update_agent(agent)

    print(f"Successfully removed all tools from agent '{updated_agent.name}'.")
    print("The agent is now configured without any callable tools.")

except Exception as e:
    print(f"An error occurred while removing tools from the agent: {e}")
