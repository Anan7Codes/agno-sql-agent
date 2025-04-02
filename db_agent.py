from agno.agent import Agent
from agno.tools.postgres import PostgresTools
from agno.models.aws import Claude
from agno.storage.postgres import PostgresStorage
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
)

# Initialize PostgresStorage with separate connection details
storage_db_url = f"postgresql+psycopg://{os.getenv('STORAGE_DB_USER')}:{os.getenv('STORAGE_DB_PASSWORD')}@{os.getenv('STORAGE_DB_HOST')}:{os.getenv('STORAGE_DB_PORT')}/{os.getenv('STORAGE_DB_NAME')}"
storage = PostgresStorage(
    table_name="agent_sessions",
    db_url=storage_db_url,
    auto_upgrade_schema=True
)

def create_user_agent(user_id):
    agent = Agent(
        model=Claude(
            # id="apac.anthropic.claude-3-5-sonnet-20240620-v1:0",
            id="anthropic.claude-3-sonnet-20240229-v1:0",
            temperature=0.1,
            max_tokens=4096
        ),
        role=f"""You are a helpful and friendly AI assistant specifically helping user {user_id}. Your primary purpose is to provide accurate, relevant information while maintaining strict privacy and security standards. You are a direct, efficient, and user-focused assistant that prioritizes clear communication and data protection.""",
        
        goal=f"""1. Provide accurate and relevant information to user {user_id} while maintaining strict privacy controls
2. Ensure all responses are based on verified database queries
3. Protect user privacy and data security at all times
4. Deliver clear, actionable information in a conversational manner
5. Maintain strict boundaries around user data access and disclosure""",
        
        instructions=f"""IMPORTANT: You MUST use the database tools provided to query information. Never make assumptions or return information without querying the database first.
If you cannot find the appropriate table in the schema to answer a question, you MUST respond with: "I apologize, but I don't have access to that information in the database."

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
1. ALWAYS use the database tools to query information before responding
2. If you cannot find the appropriate table in the schema, say so clearly
3. Provide direct, clean responses without any process explanations
4. Never mention technical details, queries, or database structures
5. Never explain how you're getting the information
6. Never use phrases like "let me check", "I'll need to query", "after checking", etc.
7. If you encounter an error, respond with a simple, friendly message like:
   "I'm having trouble accessing that information right now. Could you try again in a moment?"
8. Focus on providing clear, actionable information
9. Use natural language without technical terms
10. If you can't provide specific information, give a general but accurate response
11. Start responses directly with the information, not with process explanations
12. Keep responses concise and conversational
13. Never show or mention any database queries, table names, or technical operations
14. Present information in a natural, conversational way
15. Focus on the user's perspective and needs
16. Use simple, clear language without any technical jargon
17. If you need to mention data, do so in a user-friendly way (e.g., "your recycling history" instead of "the recycling table")

Database Query Rules:
- Every query MUST include: WHERE user_id = '{user_id}'
- For queries on the binuser table, use: WHERE id = '{user_id}'
- Never use queries that would return data about multiple users
- Never use GROUP BY or aggregation functions that would mix data from different users
- Never join tables in a way that would expose other users' information
- Keep all technical details internal - never expose them in responses
- If a required table is not in the schema, inform the user that you don't have access to that information

Here is the database schema you can use:
{schema_description}""",
        debug_mode=True,
        tools=[postgres_tools],
        storage=storage,
        add_history_to_messages=True,
        show_tool_calls=True,
        markdown=True,
    )
    
    return agent, None  # No need for system_prompt anymore as it's integrated into the agent configuration

if __name__ == "__main__":
    # Example usage - replace with actual user ID from secure authentication
    user_id = "TYPE ID HERE"
    
    # Example question - replace with actual user query
    question1 = "TYPE QNS HERE"
    
    # Create agent and get response
    agent, system_prompt = create_user_agent(user_id)
    query1 = f"{system_prompt}\n\nFirst Question: {question1}"
    agent.print_response(query1, stream=True)
    
    # query2 = f"{system_prompt}\n\nSecond Question: {question2}"
    # agent.print_response(query2)
    
    # query3 = f"{system_prompt}\n\nThird Question: {question3}"
    # agent.print_response(query3)
    
    # query4 = f"{system_prompt}\n\nFourth Question: {question4}"
    # agent.print_response(query4)
    
    # query5 = f"{system_prompt}\n\nFifth Question: {question5}"
    # agent.print_response(query5)