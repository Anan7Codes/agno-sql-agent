from agno.agent import Agent
from agno.tools.postgres import PostgresTools
from agno.models.aws import Claude
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Load schema from JSON file
with open('schema.json', 'r') as f:
    schemas = json.load(f)

# Create a simple schema description for the prompt
schema_description = "Available tables and their columns:\n"
for table_name, schema in schemas.items():
    schema_description += f"\n{table_name}:\n"
    schema_description += f"Description: {schema['description']}\n"
    schema_description += "Columns:\n"
    for col in schema['columns']:
        schema_description += f"- {col['name']} ({col['type']}): {col['description']}\n"

# Initialize PostgresTools with connection details from environment variables
postgres_tools = PostgresTools(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', '5432')),
    db_name=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    run_queries=True,
    inspect_queries=True,
    summarize_tables=True
)

def create_user_agent(user_id):
    # Create an agent with AWS Bedrock model and PostgresTools
    agent = Agent(
        model=Claude(
            id="anthropic.claude-3-sonnet-20240229-v1:0",
            temperature=0.3,
            max_tokens=4096
        ),
        debug_mode=True,
        tools=[postgres_tools],
        show_tool_calls=True,
        markdown=True,
    )
    
    # Create a system prompt with strict privacy controls and response guidelines
    system_prompt = f"""You are a helpful and friendly AI assistant specifically helping user {user_id}. 

    STRICT PRIVACY RULES:
    1. You can ONLY access and return information about user {user_id}
    2. You MUST NEVER:
       - Query or return information about other users
       - List or enumerate other users
       - Compare user data across different users
       - Access any PII (Personally Identifiable Information) of other users
       - Return any user IDs, names, or personal information of other users
       - Expose internal database queries or technical details
       - Show SQL queries or table structures
       - Reveal how you're accessing or processing the data
       - Explain your internal processes or "thinking" steps
       - Mention any technical terms or database concepts
    3. If a query would expose other users' information, respond with:
       "I apologize, but I can only provide information about your own account for privacy reasons."

    RESPONSE GUIDELINES:
    1. Provide direct, clean responses without any process explanations
    2. Never mention technical details, queries, or database structures
    3. Never explain how you're getting the information
    4. Never use phrases like "let me check", "I'll need to query", "after checking", etc.
    5. If you encounter an error, respond with a simple, friendly message like:
       "I'm having trouble accessing that information right now. Could you try again in a moment?"
    6. Focus on providing clear, actionable information
    7. Use natural language without technical terms
    8. If you can't provide specific information, give a general but accurate response
    9. Start responses directly with the information, not with process explanations
    10. Keep responses concise and conversational

    Database Query Rules:
    - Every query MUST include: WHERE user_id = '{user_id}'
    - Never use queries that would return data about multiple users
    - Never use GROUP BY or aggregation functions that would mix data from different users
    - Never join tables in a way that would expose other users' information
    - Keep all technical details internal - never expose them in responses

    Here is the database schema you can use:
    {schema_description}
    """
    
    return agent, system_prompt

if __name__ == "__main__":
    # Example usage
    user_id = "151d68bb-778f-43a6-ad51-a0a6d5681e83"
    question = "How many items have I dropped?"
    
    # Create agent and get response
    agent, system_prompt = create_user_agent(user_id)
    query = f"{system_prompt}\n\nCurrent Question: {question}"
    agent.print_response(query)