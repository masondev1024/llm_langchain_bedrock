'''
- 에이전트 => 그래프상 노드
- 에이전트 워크플로우 : 작성->리뷰->체크->수정작성->리뷰->체크... 
    - 엣지 구성(규칙, 시작, 종료) : 
       - 특정 횟수를 초과하면 종료, 
       - 시작 노드 지정
       - PASS 후 종료
       - FAIL이면 다시 작성 -> 순환구조, 2개의 노드로 구성 완료 -> 신입 개발자 에이전트의 진화 (기억만 하면)
- 아킥텍쳐
    - Langgraph
    - State : 대화 내용, 수정 횟수 저장하는 공유 메모리
    - Node
        - Coder Node    : 상태(메모리)를 읽고 코드 신규 생성/수정
        - Reviewer Node : 코드를 검증하고 Pass/Fail 판정(리뷰 내용 전달)
    - Edge
        - entry_point      : Coder Node
        - node_dir         : Coder Node -> Reviewer Node
        - Conditional Edge : Reviewer Node를 타겟, Reviewer의 판정에 따라 Coder Node 갈지, End 갈지 결정

'''
# 1. 모듈가져오기
import boto3
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import Annotated, List, TypedDict
import operator # 수정 요청한 회수 계산을 위한 처리 => 리액트의 리듀서의 기능 담당(참고)
import dotenv
import os

dotenv.load_dotenv()

# 2. 상태 정의

# 3. LLM 정의 

# 4. 노드 정의 -> Agent 정의

# 5. 조건부 엣지 정의

# 6. 그래프 구성

# 7. 실행
if __name__ == '__main__':
    pass