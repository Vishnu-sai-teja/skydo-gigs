import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not APIFY_TOKEN:
    raise ValueError("APIFY_TOKEN missing.")

openai_model = LiteLlm(
    model='openai/gpt-4o-mini',
    api_key=OPENAI_API_KEY,
)

geospatial_agent = LlmAgent(
    model=openai_model,
    name='geospatial_analyst_agent', 
    instruction="""
    You are a geospatial and data assistant. 
    Your goal is to:
    1. Extract location data, reviews, and business details from Google Maps using Apify.
    2. Read and analyze Excel files using the Excel MCP tool.
    
    Use the provided tools to fetch real-time data or analyze local datasets when asked.

    - The excel file is located at: `/Users/vishnu.nagabandi/Documents/sage/skydo/gig_agent/dataset/dataset.xlsx`
    - When reading from the Excel file, you must specify the sheet name.
        - Available sheet names: `restaurents`, `fastfood`, `collages`, `malls`, `tech_parks`
    - You can also specify a range of cells to read (e.g., "A1:J21"). If not specified, the tool will read the first paging range.
    """,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@negokaz/excel-mcp-server"],
                    env=None,
                ),
                initialization_timeout=60.0,
            ),
        )
    ],
    output_key="potential_test_set"
)

recommendation_agent = LlmAgent(
    model=openai_model,
    name='recommendation_agent',
    instruction="""
    You are a helpful recommendation assistant.
    Your goal is to analyze the data provided in the `potential_test_set` and recommend the top 3 options based on:
    1. User preferences (if provided).
    2. Ratings and reviews.
    3. Relevance to the query.

    Provide a summary of why you chose these 3 options.
    Here is the potential testset : {potential_test_set}
    """,
)

root_agent = SequentialAgent(
    name='root_agent',
    sub_agents=[geospatial_agent, recommendation_agent],
    description="""
    This agent answers all questions about gig workers, especially those looking for jobs.

    You are a master orchestrator agent. Your primary role is to coordinate between the 'geospatial_analyst_agent' and the 'recommendation_agent' to answer user queries.
    First, use the 'geospatial_analyst_agent' to gather relevant data, such as location details, reviews, business information, or to read from the provided Excel dataset.
    Then, pass the gathered information to the 'recommendation_agent' to provide a well-reasoned recommendation based on the data.
    Ensure the final output is a clear, concise recommendation that addresses the user's initial query.
    """
)





# Test query to verify
# print(root_agent.run("Find top 3 rated coffee shops in Indiranagar, Bangalore"))