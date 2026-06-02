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

# 2. 상태 정의 (메세지-messages, 재시도횟수-iterations, AgentState)
class AgentState(TypedDict):
    # Annotated[ ... ] : 메타데이터 표기
    # 타입힌트 제시, operator.add 전달 -> 상태 업데이트 방식 명확하게 지정 
    # 덮어쓰지 말고, 기존 내용에 새로운 내용을 추가하라
    # 대화를 기억하는 방법을 => 누적하여 보관
    messages   : Annotated[ List[BaseMessage], operator.add ]
    # 재시도 회수, 리뷰등을 통해 수정 내용 발생시 최대 순환 수정 회수 제한 비교용
    iterations : int

# 3. LLM 정의 
llm = ChatBedrock( model_id = os.getenv('MODEL_ID'),
    client       = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION') ),
    model_kwargs = {"temperature":0.5}
)

# 4. 노드 정의 -> Agent 정의
#    함수형태로 통합 구성 (프럼프트, 랭체인 구성, 추론요청, 결과반환(생략) )
def coder_node(state:AgentState ):
    # 메세지 추출 (최초 사용자, 이전 노드의 출력)
    # 프럼프트 구성
    # 랭체인 구성 (프럼프트=>llm) -> 에이전트 실체
    # 추론 행위 요청 -> 실제 추론 행위 실행
    # 응답값 결과 처리 (대화 메세지 정리, 수정 시도 횟수 업데이트)
    pass

# 5. 조건부 엣지 정의

# 6. 그래프 구성

# 7. 실행
if __name__ == '__main__':
    pass