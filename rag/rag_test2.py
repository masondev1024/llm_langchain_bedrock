'''
- 대량의 말뭉치를 vectordb에 세팅, 구성
- 말뭉치 => 특정 크기 단위로 분할해서 처리 -> 단위:청크(어느 정도 덩어리/크기를 잡을지 관건->성능영향 미침) -> 토큰 제한

'''
# RAG , 백터디비에 자연어->토큰화->저장, 검색(유사도기반)
# 1. 모듈 가져오기
from langchain_community.vectorstores import FAISS # 백터디비
from langchain_aws import BedrockEmbeddings # 토크나이저
import boto3
from dotenv import load_dotenv
import os
# 대량의 문서 처리 기능 제공
from langchain_community.document_loaders import TextLoader # 텍스트로부터 로드
from langchain_text_splitters import RecursiveCharacterTextSplitter # 청크 단위?

# 2. 환경변수 로드
load_dotenv()

# 3. TextLoader를 통해서 ./data/*.txt => [ Document, Document, Document, Document, Document, Document, Document]
import glob
files = glob.glob('./rag/data/*.txt')
raw_docs = [ TextLoader(file, encoding='utf-8').load()[0]  for file in files ]
# [[Docu..  => [Docu...
print( len(raw_docs), type(raw_docs[0]) )


# 4. 텍스트 분할(특정 크기 단위(청크)) => 성능 고려하여 여러 차례 시도 => 최적의 크기 찾을 필요 있음
splitter = RecursiveCharacterTextSplitter( chunk_size      =512, # 원 텍스트에서 자르는 단위 (512토큰이면 자르기)
                                chunk_overlap   =100  # 문맥 유지를 위해 겹치는 구간
    )
splites = splitter.split_documents( raw_docs )
#print( f"총 청크수 : { len(splites) }")
#print( f"내용 : { splites[0] }")
#print( f"내용 : { splites[1] }")

# 4. 임베딩 (임베딩 모델 사용=> 학습 종료됨 것임, 학습시 사용된 다국어의 양 표현의 양으로 이해)
# 자연어 -> 토큰화(분절->백터화->패딩)
tokenizer = BedrockEmbeddings(  model_id        = "amazon.titan-embed-text-v2:0",#"amazon.titan-embed-text-v1", 
                                region_name     = os.getenv('AWS_REGION') )

# 5. 백터 디비에 토큰화된 내용 입력
vector_db = FAISS.from_documents( splites, tokenizer ) # 메모리 기반, 디비를 메모리에 로드

# 6. 백터 디비에 세팅된 내용을 저장 -> DAG를 기반으로 스케줄 단위로 갱신가능
vector_db.save_local('hp-story')

# 7. 검색 => 유사도 활용
docs = vector_db.similarity_search("해리포터의 친구")

# 8. 결과 확인 -> 유사도가 가장 높은 데이터 추출(디비에 저장된)
print( docs[0].page_content )
# docs -> 유사도순으로 나열된 데이터