from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import boto3
import os
from dotenv import load_dotenv
import time
import pandas as pd

load_dotenv()

os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
os.environ['AWS_REGION_NAME'] = os.getenv('AWS_REGION_NAME')


class ExecuteSqlQueryTool(BaseTool):
    """Execute a SQL query and return the results."""
    name: str = "ExecuteSqlQueryTool"
    description: str = "Execute a SQL query and return the results."
    def _run(self, query: str) -> str:
        """Execute the SQL query and return the results."""
        client = boto3.client('athena')
        response = client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': os.getenv('DATABASE_NAME')
            },
            ResultConfiguration={
                'OutputLocation': os.getenv('OUTPUT_LOCATION')
            }
        )
        query_execution_id = response['QueryExecutionId']
        while True:
            response = client.get_query_execution(QueryExecutionId=query_execution_id)
            if response['QueryExecution']['Status']['State'] in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(1)

        if response['QueryExecution']['Status']['State'] == 'SUCCEEDED':
            result = client.get_query_results(QueryExecutionId=query_execution_id)
            # Extract column names
            column_info = result['ResultSet']['ResultSetMetadata']['ColumnInfo']
            columns = [col['Name'] for col in column_info]
            
            # Extract rows
            rows = result['ResultSet']['Rows'][1:]  # Skip the header row
            data = []
            for row in rows:
                data.append([item.get('VarCharValue', '') for item in row['Data']])
                    
            # Convert to a pandas DataFrame
            #df = pd.DataFrame(data, columns=columns)
            return {'success': True, 'data': data}
        else:
            raise Exception(response['QueryExecution']['Status']['StateChangeReason'])  
       
    