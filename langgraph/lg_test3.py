'''
랭그래프 - 단기기억을 위해 메모리 추가
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
# 메모리 관련
from langgraph.checkpoint.memory import MemorySaver # 단기기억용, 프로그램 종료되면 삭제

# 2. 메모리 생성 -> 현재는 RAM에 저장, 실제는 => 물리적 백터디비
memory = MemorySaver()