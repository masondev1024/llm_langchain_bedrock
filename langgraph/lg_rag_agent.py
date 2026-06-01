'''
식사 추천
    - RAG 활용 -> 툴로 차용하여 활용 : @tool => rag 활용( 백터 디비 활용)
        - 환각 형상 방지(할루시네이션)
            - 존재하지 않는 것을 있는 것처럼 창작하여 답변
        - 내부 데이터 접근 불가
            - LLM 관점에서 private한 데이터는 모름
            - 보안 이슈 
        - 최신 정보 부재 (LLM이 모르는 정보)
        
    - 전체 의사결정 구조 
        - 랭그래프 활용
    - 필요시 부분적으로 랭체인 고려
        - 프럼프트 => LLM 추론 : 랭체인으로 묶어서 하나의 단위(노드)로 구성 가능함
    - 프럼프트
        - fewshot 활용
'''
# 1. 모듈 가져오기
from langgraph.graph import StateGraph, END 
from typing import TypedDict, List               # 커스텀 공유메모리(그래프상 노드가 공유하는) [ {}, {}, .. ]
from langchain_core.tools import tool            # 툴 정의할때 사용 데코레이터용
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_aws import ChatBedrockConverse
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
import os
import boto3
# rag 추가
from tools import rag_search                       # rag 도구를 외부에 구성, 커스텀

# 환경변수 로드
load_dotenv()

# LLM 모델 구성 ChatBedrockConverse
llm = ChatBedrockConverse(  model       = os.getenv('MODEL_ID'), 
                            max_tokens  = 1000,
                            temperature = 0.5,                            
                            region_name = os.getenv('AWS_REGION')
                        ) 

# 툴 등록한 LLM 모델 획득
tools = [ rag_search ]
llm_with_tools = llm.bind_tools( tools )

# 퓨샷 프럼프트 구성
examples        = []
example_format  = ChatPromptTemplate.from_messages()
few_shot_prompt = FewShotChatMessagePromptTemplate()
final_prompt    = ChatPromptTemplate.from_messages([
    # 1. 페르소나
    (),
    # 2. 퓨샷 샘플
    few_shot_prompt
    # 3. 사용자 질문
    ()
])
