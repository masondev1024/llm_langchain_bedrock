'''
bedrock 을 이용한 llm 호출 코드
'''
# 1. 모듈
import os
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

# 2. 환경변수 로드
load_dotenv()
print( os.getenv('AWS_REGION') )
print( os.getenv('MODEL_ID') )
print( os.getenv('AWS_BEARER_TOKEN_BEDROCK') )

# 3. LLM 클라이언트 생성
bedrock_client = boto3.client(
  service_name = 'bedrock-runtime',
  region_name  = os.getenv('AWS_REGION')
)