# Changes made to ensure proper memory usage by the agent

from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from llama_index.embeddings.bedrock import BedrockEmbedding
from llama_index.core.memory import VectorMemory, ChatMemoryBuffer, SimpleComposableMemory
from llama_index.llms.bedrock import Bedrock
import boto3
import os
import time
import nest_asyncio

nest_asyncio.apply()

# Initialize Bedrock embeddings
embed_model = BedrockEmbedding(
    model_name='amazon.titan-embed-text-v2:0',
    region_name='us-east-1'
)

# Correctly initialize VectorMemory with default vector store
vector_memory = VectorMemory.from_defaults(
    embed_model=embed_model,
    retriever_kwargs={"similarity_top_k": 5},
)

# Initialize primary chat buffer memory
chat_memory_buffer = ChatMemoryBuffer.from_defaults()

# Combine memories using SimpleComposableMemory
composable_memory = SimpleComposableMemory(
    primary_memory=chat_memory_buffer,
    secondary_memory_sources=[vector_memory],
)

bedrock_client = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

# Define SQL execution function
def execute_sql(query: str):
    client = boto3.client('athena')
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': os.getenv('DATABASE_NAME')},
        ResultConfiguration={'OutputLocation': os.getenv('OUTPUT_LOCATION')}
    )
    query_execution_id = response['QueryExecutionId']

    while True:
        response = client.get_query_execution(QueryExecutionId=query_execution_id)
        if response['QueryExecution']['Status']['State'] in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)

    if response['QueryExecution']['Status']['State'] == 'SUCCEEDED':
        result = client.get_query_results(QueryExecutionId=query_execution_id)
        columns = [col['Name'] for col in result['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        rows = result['ResultSet']['Rows'][1:]
        data = [[item.get('VarCharValue', '') for item in row['Data']] for row in rows]
        return {'success': True, 'data': data}
    else:
        raise Exception(response['QueryExecution']['Status']['StateChangeReason'])

execute_sql_tool = FunctionTool.from_defaults(fn=execute_sql)

# Initialize the Bedrock LLM
llm = Bedrock(
    client=bedrock_client,
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)

# Adjusted context to guide agent clearly about memory
agent_context = """
You are a helpful assistant that can answer database-related queries. If the question is not directly related to the database or SQL,
you should explicitly retrieve the relevant information from your conversation memory.
use show tables to find the table names.
use describe table name to find the column names.
"""

# Initialize the ReAct agent properly
agent = ReActAgent(
    tools=[execute_sql_tool],
    llm=llm,
    memory=composable_memory,
    max_iterations=10,
    verbose=True,
    context=agent_context
)

# Agent interaction (example)
response = agent.chat("Give me the name of all the customers whose name starts with 'J'")
print(response)

# Follow-up question to test memory
response = agent.chat("tell me order ids placed by those customers")
print(response)
