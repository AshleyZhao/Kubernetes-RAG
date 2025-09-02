import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
import uuid
import sys
import os
from kubernetes_tools import list_kubernetes_pods, restart_all_pods

from dotenv import load_dotenv
import os
load_dotenv(override=True) # take environment variables from .env.
ai_foundry_endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
ai_agent_id = os.getenv("AI_AGENT_ID")

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Initialize the Azure AI Project Client
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=ai_foundry_endpoint)

# Update the op_agent with tools
op_agent_id = os.getenv("OP_AGENT_ID")
op_agent = project.agents.get_agent(op_agent_id)

op_agent.tools = [list_kubernetes_pods, restart_all_pods]
op_agent.update(op_agent)
op_agent = project.agents.get_agent(op_agent_id)

# Get the agent from your project
agent = project.agents.get_agent(ai_agent_id)

# Dictionary to store thread IDs for each session
sessions = {}

# A simple regex pattern to find and remove the citations
CITATION_PATTERN = re.compile(r'【\d+:\d+†source】')

def format_agent_response(response_text):
    """
    Formats the raw text from the agent into readable HTML.
    This function handles paragraphs and code blocks.
    """
    # First, remove the citation tags
    formatted_text = CITATION_PATTERN.sub('', response_text)

    # Find and handle code blocks
    code_block_pattern = re.compile(r'```(.*?)```', re.DOTALL)
    parts = code_block_pattern.split(formatted_text)
    
    formatted_html = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # This is a code block
            # The strip() removes leading/trailing whitespace from the code block
            # and the first line of the language tag (e.g., `shell`).
            code_content = part.strip().split('\n', 1)[-1]
            formatted_html.append(f'<pre><code>{code_content}</code></pre>')
        else:
            # This is plain text, format into paragraphs
            paragraphs = part.strip().split('\n\n')
            for p in paragraphs:
                if p:
                    # Replace single newlines with <br> for line breaks within a paragraph
                    p = p.replace('\n', '<br>')
                    formatted_html.append(f'<p>{p}</p>')

    return ''.join(formatted_html)


@app.route('/chat', methods=['POST'])
def chat():
    """
    Handles a new user message, sends it to the agent, and returns the response.
    """
    data = request.get_json()
    user_message = data.get('message')
    session_id = data.get('session_id')
    
    if not user_message or not session_id:
        return jsonify({'error': 'Message or Session ID not provided'}), 400

    try:
        # Check if a thread already exists for this session
        if session_id not in sessions:
            print(f"Creating new thread for session: {session_id}")
            thread = project.agents.threads.create()
            sessions[session_id] = thread.id

        thread_id = sessions[session_id]
        
        # Add the user's message to the thread
        project.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Run the agent and get the response
        run = project.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=agent.id
        )

        if run.status == "failed":
            print(f"Run failed: {run.last_error}")
            return jsonify({'response': 'Sorry, the agent run failed. Please try again.'})
        
        # Get the latest message, which is the full assistant response
        messages = project.agents.messages.list(thread_id=thread_id, order=ListSortOrder.DESCENDING)
        
        # Format the text of the latest assistant message
        agent_response = "No response from agent."
        for message in messages:
            if message.role == "assistant" and message.text_messages:
                agent_response = format_agent_response(message.text_messages[0].text.value)
                break
        
        return jsonify({'response': agent_response})
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@app.route('/delete_thread', methods=['POST'])
def delete_thread():
    """
    Deletes the agent thread associated with a session ID.
    """
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'message': 'Session ID not found'}), 404

    try:
        thread_id = sessions.pop(session_id)
        project.agents.threads.delete(thread_id)
        print(f"Deleted thread with ID: {thread_id} for session: {session_id}")
        return jsonify({'message': 'Thread deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting thread: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

if __name__ == '__main__':
    # You can change the port if needed.
    app.run(host='0.0.0.0', port=5000)
