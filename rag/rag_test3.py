'''
- 저장된 백터 디비 로드
- llm을 이용 추론 -> 프럼프트에 rag를 이용한 검색 증강용 데이터 추가하여 추론 진행
    - 프럼프트 ( 질의 + rag 검색결과 )
- 랭체인의 체인 구성
'''
# 1. 모듈 가져오기
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import boto3
from dotenv import load_dotenv
import os
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough  # 질문 검색과 사용자 질문 세팅등 동시작업
from langchain_core.output_parsers import StrOutputParser # llm응답 파싱=>문자열만 추출

# 2. 환경변수 로드
load_dotenv()

# 3. 임베딩 모델 로드
tokenizer = BedrockEmbeddings(  model_id        = "amazon.titan-embed-text-v2:0",#"amazon.titan-embed-text-v1", 
                                region_name     = os.getenv('AWS_REGION') )

# 4. 저장된 디비 파일을 기반으로 로드
vector_db = FAISS.load_local('hp-story', tokenizer, allow_dangerous_deserialization=True)

# 5. LLM 클라이언트 생성
bedrock_client = boto3.client(
  service_name = 'bedrock-runtime',
  region_name  = os.getenv('AWS_REGION')
)

# 6. llm 생성
llm = ChatBedrock(
      client   = bedrock_client,
      model_id = 'openai.gpt-oss-120b-1:0', # 편의상 직접 세팅
      model_kwargs = {
        "max_tokens" : 500,
        "temperature": 0.7
      }
)

# 7. prompt 구성