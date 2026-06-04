# llm_langchain_bedrock 프로젝트 이해 가이드

이 문서는 `llm_langchain_bedrock` 프로젝트를 처음부터 끝까지 이해하기 위해 필요한 구조, 개념, 실행 흐름, 핵심 기술을 정리한 학습용 문서입니다. 현재 저장소는 하나의 완성된 서비스라기보다, AWS Bedrock 기반 LLM 호출에서 시작해 LangChain, RAG, LangGraph, Tool Calling, A2A 패턴으로 확장해 보는 예제 프로젝트에 가깝습니다.

## 1. 프로젝트 한 줄 요약

이 프로젝트는 AWS Bedrock의 LLM을 LangChain으로 호출하고, Streamlit/FastAPI 채팅 앱, FAISS 기반 RAG, LangGraph 기반 에이전트 워크플로, 여러 LLM 에이전트가 협업하는 A2A 패턴을 단계적으로 실험합니다.

## 2. 전체 구조

```text
llm_langchain_bedrock/
├─ app.py                    # Streamlit 프론트엔드 채팅 화면
├─ server.py                 # FastAPI 백엔드 /chat API
├─ llm/__init__.py           # Bedrock LLM 클라이언트와 메뉴 추천 chain
├─ rag/
│  ├─ rag_test1.py           # 간단한 FAISS 벡터 검색 예제
│  ├─ rag_test2.py           # 텍스트 파일 로드, 청크 분할, FAISS 저장
│  ├─ rag_test3.py           # 저장된 FAISS 인덱스를 이용한 RAG chain
│  └─ data/                  # 해리 포터 줄거리 텍스트 데이터
├─ hp-story/
│  ├─ index.faiss            # rag_test2.py에서 생성한 FAISS 인덱스
│  └─ index.pkl              # FAISS 메타데이터/문서 저장 파일
├─ langgraph/
│  ├─ lg_test1.py            # 가장 단순한 StateGraph 예제
│  ├─ lg_test2.py            # LLM + ToolNode + 조건부 edge 예제
│  ├─ lg_test3.py            # MemorySaver 체크포인터를 붙인 그래프
│  ├─ rag_store.py           # 메뉴 추천용 인메모리 FAISS 검색 저장소
│  ├─ tools.py               # rag_search LangChain tool 정의
│  └─ lg_rag_agent.py        # RAG tool을 쓰는 LangGraph 에이전트 예제
├─ a2a/
│  ├─ a2a_langchain.py       # LangChain chain 조합으로 A2A 흉내
│  └─ a2a_langgraph.py       # LangGraph로 coder/reviewer 반복 협업 구현
├─ requirements.txt          # 주요 의존성
└─ readme.MD                 # 원본 설명 문서, 현재 일부 한글 인코딩이 깨져 있음
```

## 3. 가장 먼저 이해해야 할 실행 흐름

기본 앱 흐름은 다음과 같습니다.

```text
사용자
  ↓
app.py Streamlit 채팅 입력
  ↓ HTTP POST http://localhost:8000/chat
server.py FastAPI /chat
  ↓
llm.chain.invoke({"user_input": query})
  ↓
ChatPromptTemplate + FewShotChatMessagePromptTemplate
  ↓
AWS Bedrock ChatBedrockConverse
  ↓
응답을 JSON으로 반환
  ↓
Streamlit 화면에 출력
```

핵심은 `app.py`가 직접 LLM을 호출하지 않고, `server.py`의 `/chat` API를 호출한다는 점입니다. `server.py`는 `llm/__init__.py`에 정의된 `chain`을 호출합니다.

## 4. 실행에 필요한 환경 변수

프로젝트는 `.env`를 통해 Bedrock 관련 값을 읽습니다.

```env
AWS_REGION=us-east-1
MODEL_ID=사용할_Bedrock_모델_ID
AWS_BEARER_TOKEN_BEDROCK=필요한_경우_토큰
```

코드에서 실제로 반복적으로 쓰이는 값은 `AWS_REGION`, `MODEL_ID`입니다. `llm/__init__.py`는 `dotenv.load_dotenv()`로 환경 변수를 로드하고, `boto3.client("bedrock-runtime")`를 만든 뒤 `ChatBedrockConverse`에 연결합니다.

주의할 점:

- Bedrock 모델 호출 권한이 AWS 계정에 있어야 합니다.
- 선택한 `MODEL_ID`가 해당 리전에서 사용 가능해야 합니다.
- 일부 예제는 모델 ID를 환경 변수 대신 코드에 직접 적어 둡니다.

## 5. 주요 의존성과 역할

`requirements.txt` 기준 핵심 패키지는 다음과 같습니다.

| 패키지 | 역할 |
| --- | --- |
| `fastapi` | 백엔드 API 서버 |
| `uvicorn` | FastAPI 실행 서버 |
| `streamlit` | 간단한 채팅 UI |
| `requests` | Streamlit에서 FastAPI로 HTTP 요청 |
| `boto3` | AWS Bedrock Runtime 클라이언트 생성 |
| `python-dotenv` | `.env` 환경 변수 로드 |
| `langchain-core` | Prompt, Runnable, OutputParser 등 LangChain 핵심 추상화 |
| `langchain-aws` | Bedrock용 LangChain 모델/임베딩 래퍼 |
| `langchain-community` | FAISS, TextLoader 등 커뮤니티 통합 |
| `faiss-cpu` | 로컬 벡터 검색 엔진 |
| `langchain` | LangChain 상위 패키지 |
| `langgraph` | 상태 그래프 기반 에이전트 워크플로 |

## 6. Bedrock + LangChain 기본 구조

`llm/__init__.py`가 기본 LLM 호출의 중심입니다.

핵심 구성은 다음 순서입니다.

1. `.env` 로드
2. `boto3.client(service_name="bedrock-runtime")` 생성
3. `ChatBedrockConverse` 생성
4. few-shot 예시 목록 구성
5. `ChatPromptTemplate`로 system/human/ai 메시지 템플릿 구성
6. `last_prompt | llm` 형태로 LCEL chain 생성

여기서 `|` 연산자는 LangChain Expression Language, 즉 LCEL의 파이프 연산입니다.

```python
chain = last_prompt | llm
```

이 뜻은 "사용자 입력을 프롬프트에 채운 다음, 그 결과를 LLM에 전달한다"입니다.

## 7. Prompt와 Few-shot의 의미

이 프로젝트의 기본 메뉴 추천 챗봇은 단순히 질문을 LLM에 던지지 않습니다. 먼저 시스템 역할과 예시 답변을 제공합니다.

- `system`: LLM의 역할을 지정합니다. 예: 식사 메뉴 추천 전문가
- `fewshot_samples`: 사용자의 상황별 입력과 추천 답변 예시
- `human`: 실제 사용자의 입력

Few-shot은 "이런 식으로 답하라"는 샘플을 모델에게 보여 주는 방식입니다. 모델을 새로 학습시키는 것은 아니고, 현재 요청 문맥 안에 예시를 넣어 답변 스타일과 판단 기준을 유도합니다.

## 8. FastAPI 백엔드

`server.py`는 매우 얇은 백엔드입니다.

주요 역할:

- `FastAPI` 앱 생성
- `UserRequest` Pydantic 모델로 요청 body 검증
- `/chat` POST API 제공
- `chain.invoke({"user_input": req.query})` 호출
- LLM 응답의 `content`를 JSON으로 반환

API 형태는 다음과 같습니다.

```http
POST /chat
Content-Type: application/json

{
  "query": "오늘 비 오는데 점심 메뉴 추천해줘"
}
```

응답 형태:

```json
{
  "response": "..."
}
```

## 9. Streamlit 프론트엔드

`app.py`는 채팅 UI 역할을 합니다.

핵심 개념:

- `st.session_state.messages`: 화면에 표시할 대화 기록 저장
- `st.chat_message(...)`: 사용자/assistant 말풍선 출력
- `st.chat_input(...)`: 채팅 입력창
- `requests.post(API_URL, json={"query": prompt})`: 백엔드 호출

현재 앱은 `http://localhost:8000/chat`을 고정 URL로 호출하므로, Streamlit을 실행하기 전에 FastAPI 서버가 먼저 떠 있어야 합니다.

실행 순서:

```bash
uvicorn server:app --reload --port 8000
streamlit run app.py
```

## 10. RAG 전체 개념

RAG는 Retrieval-Augmented Generation의 약자입니다. 모델이 원래 알고 있는 지식만으로 답하지 않고, 외부 문서나 사내 데이터에서 관련 정보를 검색한 뒤 그 검색 결과를 프롬프트에 넣어 답하게 하는 구조입니다.

이 프로젝트에서 RAG는 다음 흐름으로 구현됩니다.

```text
원본 텍스트
  ↓
문서 로드
  ↓
청크 분할
  ↓
BedrockEmbeddings로 벡터화
  ↓
FAISS에 저장
  ↓
사용자 질문도 벡터화
  ↓
유사한 청크 검색
  ↓
검색 결과를 context로 프롬프트에 삽입
  ↓
LLM이 context 기반으로 답변
```

## 11. RAG 예제별 역할

### rag/rag_test1.py

가장 단순한 벡터 검색 예제입니다.

- 문자열 리스트를 직접 준비합니다.
- `BedrockEmbeddings`로 임베딩합니다.
- `FAISS.from_texts(...)`로 벡터 DB를 만듭니다.
- `similarity_search(...)`로 유사 문장을 검색합니다.

이 파일은 "벡터 DB가 무엇인지" 이해하기 위한 최소 예제입니다.

### rag/rag_test2.py

문서 기반 벡터 DB 생성 예제입니다.

- `rag/data/*.txt` 파일을 읽습니다.
- `TextLoader`로 텍스트 문서를 `Document` 객체로 만듭니다.
- `RecursiveCharacterTextSplitter`로 문서를 청크 단위로 나눕니다.
- `FAISS.from_documents(...)`로 벡터 DB를 만듭니다.
- `vector_db.save_local("hp-story")`로 로컬에 저장합니다.

`hp-story/index.faiss`, `hp-story/index.pkl`은 이 단계의 결과물입니다.

### rag/rag_test3.py

저장된 벡터 DB를 실제 RAG chain으로 사용하는 예제입니다.

구성 요소:

- `FAISS.load_local(...)`: 저장된 벡터 DB 로드
- `vector_db.as_retriever(search_kwargs={"k": 3})`: 상위 3개 관련 문서 검색
- `format_docs(...)`: 검색된 문서를 하나의 문자열 context로 합치기
- `ChatPromptTemplate.from_template(...)`: context와 사용자 질문을 넣는 프롬프트
- `RunnablePassthrough`: 사용자 질문을 그대로 다음 단계에 전달
- `StrOutputParser`: LLM 응답을 문자열로 파싱

핵심 chain:

```python
rag_chain = (
    {"context": retriever | format_docs, "user_input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

이 구조를 이해하면 LangChain에서 RAG가 어떻게 조립되는지 큰 그림이 잡힙니다.

## 12. FAISS와 Embedding

Embedding은 텍스트를 숫자 벡터로 바꾸는 과정입니다. 의미가 비슷한 문장은 벡터 공간에서도 가까운 위치에 놓이도록 만드는 것이 목표입니다.

FAISS는 이런 벡터들을 저장하고, 어떤 질문 벡터와 가장 가까운 벡터를 빠르게 찾는 검색 엔진입니다.

이 프로젝트에서는 임베딩 모델로 주로 다음을 사용합니다.

```python
BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
```

중요한 구분:

- LLM 모델: 답변을 생성합니다.
- Embedding 모델: 검색을 위해 텍스트를 벡터로 바꿉니다.
- Vector DB: 벡터를 저장하고 유사도를 검색합니다.

## 13. LangGraph 기본 개념

LangGraph는 LLM 앱의 흐름을 그래프로 구성하는 라이브러리입니다. 단순 chain은 보통 한 방향 파이프라인에 가깝지만, 그래프는 조건 분기, 반복, 도구 사용, 메모리, 다중 에이전트 흐름에 더 적합합니다.

핵심 용어:

| 용어 | 의미 |
| --- | --- |
| State | 노드들이 공유하는 상태/메모리 |
| Node | 하나의 작업 단위. 함수, LLM 호출, tool 실행 등이 될 수 있음 |
| Edge | 한 노드에서 다음 노드로 이동하는 규칙 |
| Conditional Edge | 상태나 LLM 응답에 따라 다음 노드를 다르게 고르는 규칙 |
| START/END | 그래프 시작과 종료 지점 |
| compile | 정의한 그래프를 실행 가능한 앱으로 변환 |

## 14. LangGraph 예제별 역할

### langgraph/lg_test1.py

가장 작은 그래프 예제입니다.

```text
T1(add_prefix) → T2(add_suffix) → END
```

`CustomState`라는 `TypedDict`를 상태로 사용하고, 각 노드는 상태를 받아 새 상태를 반환합니다.

이 파일에서 배워야 할 것은 다음입니다.

- `StateGraph(CustomState)`
- `add_node`
- `set_entry_point`
- `add_edge`
- `compile`
- `app.invoke(...)`

### langgraph/lg_test2.py

LLM이 도구를 사용할 수 있는지 판단하는 예제입니다.

흐름:

```text
START
  ↓
chatbot
  ↓ 조건부 판단
  ├─ 도구 필요 없음 → END
  └─ 도구 필요 → tools → chatbot → ...
```

핵심 요소:

- `@tool`로 `multiply(a, b)` 도구 정의
- `llm.bind_tools(tools)`로 LLM에 도구 목록 등록
- `ToolNode(tools)`로 도구 실행 노드 생성
- `tools_condition`으로 LLM 응답에 tool call이 있는지 판단

### langgraph/lg_test3.py

`lg_test2.py`에 메모리를 추가한 버전입니다.

핵심 추가점:

```python
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "user-1"}}
```

`thread_id`를 기준으로 대화 상태를 이어 받을 수 있습니다. 단, `MemorySaver`는 메모리 기반이므로 프로그램이 종료되면 사라지는 단기 기억입니다.

### langgraph/rag_store.py와 langgraph/tools.py

`rag_store.py`는 메뉴 추천용 간단한 인메모리 벡터 DB입니다. 식당명, 메뉴, 특징, 가격 정보가 들어간 문자열을 FAISS에 저장하고, `search_stores(query, k=2)`로 관련 메뉴를 검색합니다.

`tools.py`는 이 검색 기능을 LangChain tool로 감쌉니다.

```python
@tool
def rag_search(cate: str) -> str:
    ...
```

즉, LLM이 필요하다고 판단하면 `rag_search` 도구를 호출해 사내/로컬 메뉴 데이터를 검색할 수 있게 만드는 구조입니다.

### langgraph/lg_rag_agent.py

RAG tool을 LangGraph 에이전트 안에 연결한 예제입니다.

흐름:

```text
사용자 입력
  ↓
thinking 노드
  ↓
tool call이 있나?
  ├─ 없음 → END
  └─ 있음 → tool 노드에서 rag_search 실행
          ↓
        final_answer 노드
          ↓
        END
```

이 파일은 "LLM이 필요할 때 검색 도구를 사용하고, 검색 결과를 바탕으로 최종 답변을 생성한다"는 에이전트형 RAG의 핵심 아이디어를 보여 줍니다.

## 15. Tool Calling 이해하기

Tool Calling은 LLM이 외부 함수를 직접 실행하는 것이 아니라, "이 함수를 이런 인자로 호출해야 한다"는 구조화된 요청을 만드는 방식입니다. 실제 실행은 LangChain/LangGraph 쪽의 `ToolNode`나 직접 작성한 코드가 담당합니다.

이 프로젝트의 대표 도구:

- `multiply(a, b)`: 계산 도구 예제
- `rag_search(cate)`: 메뉴 데이터 검색 도구

중요한 점:

- LLM은 도구의 이름, 설명, 인자 타입을 보고 도구 사용 여부를 판단합니다.
- 도구 사용이 필요한 모델과 아닌 모델의 동작이 다를 수 있습니다.
- 도구 호출 결과를 다시 LLM에 넣어 최종 답변을 만들 수 있습니다.

## 16. A2A 구조

A2A는 Agent-to-Agent의 약자입니다. 한 LLM 호출이 모든 일을 처리하는 대신, 역할이 다른 에이전트들이 순서대로 결과를 주고받으며 작업 품질을 높이는 패턴입니다.

이 프로젝트에서는 코드 작성 예제로 A2A를 설명합니다.

### a2a/a2a_langchain.py

LangChain chain 세 개를 만듭니다.

- `developer_agent`: 요청을 받아 초안 코드 작성
- `reviewer_agent`: 초안 코드를 검토하고 `PASS` 또는 피드백 반환
- `refiner_agent`: 피드백을 반영해 코드 수정

흐름:

```text
요청
  ↓
developer_agent
  ↓
reviewer_agent
  ├─ PASS → 종료
  └─ 피드백 → refiner_agent → 최종 코드
```

이 방식은 단순하지만 반복 루프가 구조화되어 있지는 않습니다.

### a2a/a2a_langgraph.py

LangGraph로 coder/reviewer 반복 루프를 구현합니다.

상태:

- `messages`: 대화/작업 기록
- `iterations`: 반복 횟수

노드:

- `coder`: 코드 작성 또는 수정
- `reviewer`: 코드 검토

조건:

- 리뷰 결과에 `PASS`가 있으면 종료
- 반복 횟수가 3회 이상이면 종료
- 그 외에는 다시 `coder`로 돌아감

흐름:

```text
coder
  ↓
reviewer
  ↓ 조건 판단
  ├─ PASS → END
  ├─ iterations >= 3 → END
  └─ FAIL → coder
```

이 예제는 LangGraph가 반복, 조건 분기, 상태 누적이 필요한 A2A 작업에 적합하다는 점을 보여 줍니다.

## 17. 반드시 알아야 할 기술 개념 목록

이 프로젝트를 완전히 이해하려면 아래 개념들을 순서대로 잡는 것이 좋습니다.

1. HTTP API 기본
   - Streamlit은 UI, FastAPI는 API 서버입니다.
   - JSON 요청/응답 구조를 이해해야 `app.py`와 `server.py` 연결이 보입니다.

2. AWS Bedrock
   - AWS에서 제공하는 Foundation Model 호출 서비스입니다.
   - `boto3`로 `bedrock-runtime` 클라이언트를 만들고, LangChain의 Bedrock 래퍼가 이를 사용합니다.

3. LangChain Prompt
   - `ChatPromptTemplate`은 system/user/assistant 메시지 템플릿을 구성합니다.
   - Few-shot prompt는 답변 스타일과 판단 패턴을 예시로 유도합니다.

4. LCEL
   - `prompt | llm | parser` 같은 파이프라인 문법입니다.
   - 각 단계가 Runnable로 연결됩니다.

5. Embedding
   - 텍스트를 의미 벡터로 변환합니다.
   - 생성 모델이 아니라 검색용 모델입니다.

6. Vector DB와 FAISS
   - 벡터를 저장하고 유사도 검색을 수행합니다.
   - RAG에서 "관련 문서 찾기"를 담당합니다.

7. Text Splitter
   - 긴 문서를 적절한 크기의 청크로 나눕니다.
   - chunk size와 overlap은 검색 품질에 큰 영향을 줍니다.

8. Retriever
   - Vector DB를 검색 인터페이스로 감싼 것입니다.
   - `k` 값은 몇 개의 관련 문서를 가져올지 결정합니다.

9. RAG Prompt
   - 검색 결과를 `context`에 넣고, 질문을 함께 전달합니다.
   - "문서에 없으면 모른다고 답하라" 같은 규칙을 system/prompt에 넣을 수 있습니다.

10. Tool Calling
    - LLM이 외부 함수 사용 필요성을 판단하고 호출 요청을 생성합니다.
    - 실제 함수 실행은 애플리케이션 코드가 담당합니다.

11. LangGraph StateGraph
    - 상태, 노드, 엣지로 워크플로를 표현합니다.
    - 조건 분기와 반복이 필요한 LLM 앱에 적합합니다.

12. Checkpointer/Memory
    - 그래프 실행 간 상태를 이어 가는 장치입니다.
    - 현재 예제의 `MemorySaver`는 프로그램 종료 시 사라지는 단기 메모리입니다.

13. A2A
    - 역할이 다른 에이전트가 결과를 주고받는 구조입니다.
    - coder/reviewer/refiner처럼 작업을 분리할 수 있습니다.

## 18. 파일별 학습 순서 추천

처음부터 이해하려면 아래 순서가 가장 자연스럽습니다.

1. `requirements.txt`
   - 프로젝트가 어떤 기술 스택을 쓰는지 먼저 확인합니다.

2. `llm/__init__.py`
   - Bedrock LLM, prompt, few-shot, chain의 기본 구조를 이해합니다.

3. `server.py`
   - 백엔드 API가 LLM chain을 어떻게 호출하는지 봅니다.

4. `app.py`
   - 사용자의 채팅 입력이 API로 어떻게 전달되는지 봅니다.

5. `rag/rag_test1.py`
   - 벡터 검색의 최소 단위를 이해합니다.

6. `rag/rag_test2.py`
   - 문서를 청크로 나누고 FAISS 인덱스를 저장하는 과정을 이해합니다.

7. `rag/rag_test3.py`
   - retriever와 prompt를 결합해 RAG chain을 만드는 법을 이해합니다.

8. `langgraph/lg_test1.py`
   - LangGraph의 상태/노드/엣지 기본 문법을 익힙니다.

9. `langgraph/lg_test2.py`
   - LLM tool calling과 조건부 edge를 이해합니다.

10. `langgraph/lg_test3.py`
    - thread별 memory/checkpoint 개념을 이해합니다.

11. `langgraph/rag_store.py`, `langgraph/tools.py`, `langgraph/lg_rag_agent.py`
    - RAG 검색을 tool로 만들고 에이전트 그래프에 연결하는 흐름을 봅니다.

12. `a2a/a2a_langchain.py`, `a2a/a2a_langgraph.py`
    - 다중 에이전트 협업 패턴을 chain 방식과 graph 방식으로 비교합니다.

## 19. 현재 코드에서 주의해야 할 점

1. 원본 README와 일부 주석은 한글 인코딩이 깨져 있습니다.
   - 코드 자체의 구조는 읽을 수 있지만 설명 주석은 일부 의미 파악이 어렵습니다.
   - 문서는 코드 구조와 import/function/chain/graph 정의를 기준으로 작성했습니다.

2. 일부 예제는 실험용이므로 실행 환경에 따라 바로 실행되지 않을 수 있습니다.
   - Python 문법 파싱은 통과하지만, 실제 실행에는 Bedrock 권한, `.env`, 모델 ID, AWS 리전 설정이 필요합니다.
   - `langgraph/lg_rag_agent.py`, `langgraph/rag_store.py`처럼 주석과 문자열의 한글이 깨져 보이는 파일은 의미 파악이 어려울 수 있습니다.

3. `FAISS.load_local(..., allow_dangerous_deserialization=True)`는 신뢰할 수 있는 로컬 파일에만 사용해야 합니다.
   - pickle 역직렬화가 포함되므로 외부에서 받은 인덱스 파일에는 위험할 수 있습니다.

4. `llm/__init__.py`는 환경 변수를 `print`합니다.
   - `AWS_BEARER_TOKEN_BEDROCK` 같은 민감 정보가 콘솔에 노출될 수 있으므로 실제 서비스에서는 제거해야 합니다.

5. `app.py`의 API URL이 고정되어 있습니다.
   - 로컬 개발에는 간단하지만 운영 환경에서는 환경 변수로 분리하는 편이 안전합니다.

6. 현재 예제들은 테스트 코드가 없습니다.
   - 학습용으로는 충분하지만, 서비스화하려면 API 테스트, RAG 검색 테스트, LangGraph 분기 테스트가 필요합니다.

## 20. 이 프로젝트의 핵심 아키텍처 관점

이 저장소는 다음 네 단계로 발전하는 구조입니다.

### 1단계: 단순 LLM 앱

```text
Prompt → LLM → Answer
```

해당 파일:

- `llm/__init__.py`
- `server.py`
- `app.py`

### 2단계: RAG 앱

```text
Question → Retriever → Context + Question → LLM → Answer
```

해당 파일:

- `rag/rag_test1.py`
- `rag/rag_test2.py`
- `rag/rag_test3.py`

### 3단계: Tool 사용 에이전트

```text
Question → LLM 판단 → Tool 호출 여부 결정 → Tool 실행 → LLM 최종 답변
```

해당 파일:

- `langgraph/lg_test2.py`
- `langgraph/lg_test3.py`
- `langgraph/tools.py`
- `langgraph/lg_rag_agent.py`

### 4단계: A2A / 다중 에이전트

```text
Agent A 생성 → Agent B 검토 → 조건에 따라 반복/종료
```

해당 파일:

- `a2a/a2a_langchain.py`
- `a2a/a2a_langgraph.py`

## 21. 학습 체크리스트

아래 질문에 답할 수 있으면 이 프로젝트의 핵심은 거의 이해한 것입니다.

- `app.py`와 `server.py`는 각각 어떤 책임을 가지는가?
- `server.py`가 호출하는 `chain`은 어디에서 만들어지는가?
- `ChatPromptTemplate`와 `FewShotChatMessagePromptTemplate`는 각각 왜 필요한가?
- `ChatBedrock`과 `ChatBedrockConverse`는 어떤 역할을 하는가?
- RAG에서 embedding 모델과 LLM 모델은 왜 구분되는가?
- `rag_test2.py`에서 chunk size와 overlap은 왜 중요한가?
- `rag_test3.py`의 `retriever | format_docs`는 어떤 의미인가?
- LangGraph에서 State, Node, Edge는 각각 무엇인가?
- `tools_condition`은 무엇을 기준으로 다음 노드를 결정하는가?
- `MemorySaver`와 `thread_id`는 왜 같이 쓰이는가?
- `rag_search`는 일반 함수와 무엇이 다른가?
- A2A에서 reviewer가 `PASS`를 반환하는 것이 왜 종료 조건이 되는가?
- LangChain chain 방식과 LangGraph 방식은 언제 각각 적합한가?

## 22. 실행 명령 요약

가상환경과 패키지 설치:

```bash
python -m venv llm_venv
llm_venv\Scripts\activate
pip install -r requirements.txt
```

백엔드 실행:

```bash
uvicorn server:app --reload --port 8000
```

프론트엔드 실행:

```bash
streamlit run app.py
```

RAG 인덱스 생성:

```bash
python rag/rag_test2.py
```

RAG chain 실행:

```bash
python rag/rag_test3.py
```

LangGraph 기본 예제:

```bash
python langgraph/lg_test1.py
python langgraph/lg_test2.py
python langgraph/lg_test3.py
```

A2A 예제:

```bash
python a2a/a2a_langchain.py
python a2a/a2a_langgraph.py
```

## 23. 결론

이 프로젝트의 중심은 "LLM을 그냥 호출하는 코드"에서 출발해 "검색을 붙이고, 도구를 붙이고, 상태 그래프와 다중 에이전트로 확장하는 과정"입니다.

가장 중요한 이해 포인트는 다음 세 가지입니다.

1. LangChain은 LLM 호출, prompt, retriever, parser를 조립하는 파이프라인 도구입니다.
2. RAG는 LLM이 모르는 외부 데이터를 검색해 prompt에 넣어 답변 품질과 사실성을 높이는 구조입니다.
3. LangGraph는 조건 분기, 반복, tool calling, memory, A2A처럼 복잡한 LLM 워크플로를 상태 그래프로 표현하는 도구입니다.

이 세 가지 축을 잡으면 `llm_langchain_bedrock` 저장소의 각 파일은 독립적인 예제가 아니라, Bedrock 기반 LLM 애플리케이션을 점점 더 실전형 구조로 확장하는 학습 경로로 보입니다.
