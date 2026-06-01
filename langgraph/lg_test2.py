'''
TOOL 사용, LLM 적용
'''
# 1. 모듈 가져오기
from langgraph.graph import StateGraph, END, MessagesState, START
from typing import TypedDict
from langchain_core.tools import tool            # 툴 정의할때 사용 데코레이터용
from langchain_core.messages import HumanMessage # 사용자의 메세지 형태 편하게 구성
from langchain_aws import ChatBedrock, ChatBedrockConverse # AWS bedrock llm 호출시 사용
from langgraph.prebuilt import ToolNode, tools_condition   # 툴 -> 노드로 변환, 조건부 툴적용
from dotenv import load_dotenv
import os
import boto3

# 2. 환경변수 로드
load_dotenv()

# 3. LLM 추론용 객체 생성(전역변수)
#    모델별로 ChatBedrock or ChatBedrockConverse 교체 적용
llm = ChatBedrock(model  = os.getenv['MODEL_ID'], 
                  client = boto3.client( 'bedrock-runtime', region_name=os.getenv('AWS_REGION') ) 
                )

# 4. 툴 준비
