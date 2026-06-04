# llm_langchain_bedrock 프로젝트 이해 가이드

이 문서는 `llm_langchain_bedrock` 프로젝트를 처음 보는 신입 개발자가 전체 흐름을 따라가기 위한 로컬 학습 노트입니다.

현재 이 파일은 `.gitignore`에 등록되어 있어서 GitHub에는 올라가지 않습니다. 개인 학습 정리용으로만 사용합니다.

## 1. 프로젝트 한 줄 요약

이 프로젝트는 AWS Bedrock의 LLM을 LangChain으로 호출하는 기본 예제에서 시작해, Streamlit/FastAPI 채팅 앱, FAISS 기반 RAG, LangGraph 기반 에이전트, A2A 패턴, MCP 도구 서버 실험까지 확장해 보는 학습용 프로젝트입니다.

## 2. 현재 디렉터리 구조

```text
llm_langchain_bedrock/
├─ web/
│  ├─ app.py              # Streamlit 채팅 화면
│  └─ server.py           # FastAPI /chat 백엔드 API
├─ llm/
│  └─ __init__.py         # Bedrock LLM과 메뉴 추천 chain 생성
├─ rag/
│  ├─ rag_test1.py        # 간단한 FAISS 벡터 검색 실험
│  ├─ rag_test2.py        # 텍스트 로드, 분할, 임베딩, FAISS 저장
│  ├─ rag_test3.py        # 저장된 FAISS 인덱스를 이용한 RAG chain
│  └─ data/               # 해리 포터 줄거리 텍스트 데이터
├─ hp-story/
│  ├─ index.faiss         # FAISS 벡터 인덱스
│  └─ index.pkl           # FAISS 메타데이터
├─ langgraph/
│  ├─ lg_test1.py         # 가장 단순한 StateGraph 예제
│  ├─ lg_test2.py         # LLM + tool calling + ToolNode 예제
│  ├─ lg_test3.py         # MemorySaver 체크포인트 추가 예제
│  ├─ lg_rag_agent.py     # RAG tool을 사용하는 LangGraph 에이전트
│  ├─ rag_store.py        # RAG 검색용 벡터 저장소 구성
│  └─ tools.py            # LangChain tool 정의
├─ a2a/
│  ├─ a2a_langchain.py    # LangChain chain 조합 기반 A2A 실험
│  └─ a2a_langgraph.py    # LangGraph 기반 coder/reviewer 반복 실험
├─ mcp/
│  ├─ server.py           # FastMCP stdio 서버, 6개 tool 제공
│  ├─ client.py           # MCP 서버에 연결해 tool 목록 확인
│  ├─ mcp_tools_adapter.py # MCP tool 호출 테스트 어댑터
│  ├─ bedrock_mcp_agent.py # Bedrock + LangGraph + MCP tool 연결 실험 중
│  └─ readme.MD           # MCP 학습 메모
├─ requirements.txt
├─ readme.MD
└─ PROJECT_UNDERSTANDING_GUIDE.md
```

## 3. 큰 흐름 먼저 보기

기본 웹 앱 흐름은 다음과 같습니다.

```text
사용자
  ↓
web/app.py Streamlit 채팅 입력
  ↓ HTTP POST http://localhost:8000/chat
web/server.py FastAPI /chat
  ↓
llm.chain.invoke({"user_input": query})
  ↓
ChatPromptTemplate + FewShotChatMessagePromptTemplate
  ↓
AWS Bedrock ChatBedrockConverse
  ↓
응답 JSON 반환
  ↓
Streamlit 화면 출력
```

핵심은 `web/app.py`가 직접 LLM을 호출하지 않는다는 점입니다.

`web/app.py`는 화면 담당이고, `web/server.py`는 API 담당입니다. 실제 LLM 호출 흐름은 `llm/__init__.py`에 있는 `chain`이 담당합니다.

## 4. 주요 단어 쉽게 이해하기

`Streamlit`은 Python으로 웹 화면을 만드는 도구입니다. 이 프로젝트에서는 사용자가 질문을 입력하는 채팅 UI를 만듭니다.

`FastAPI`는 Python으로 API 서버를 만드는 도구입니다. 이 프로젝트에서는 `/chat` 주소로 질문을 받고 LLM 응답을 돌려줍니다.

`HTTP POST`는 클라이언트가 서버로 데이터를 보내는 방식입니다. 사용자의 질문을 서버로 전달할 때 사용합니다.

`JSON`은 서버와 클라이언트가 데이터를 주고받는 형식입니다.

```json
{
  "query": "오늘 점심 메뉴 추천해줘"
}
```

`LangChain`은 프롬프트, LLM, 출력 처리 등을 체인처럼 연결할 수 있게 도와주는 라이브러리입니다.

`AWS Bedrock`은 AWS에서 제공하는 LLM 호출 플랫폼입니다. Bedrock 안의 Claude, Gemma, Llama, Titan 같은 모델을 사용할 수 있습니다.

`boto3`는 Python에서 AWS 서비스를 호출하는 SDK입니다.

`RAG`는 Retrieval Augmented Generation의 약자입니다. 먼저 문서에서 관련 내용을 검색하고, 그 검색 결과를 LLM에게 같이 넣어 답변 품질을 높이는 방식입니다.

`LangGraph`는 LLM 작업 흐름을 그래프 형태로 구성하는 도구입니다. 노드, 엣지, 상태를 이용해 에이전트 흐름을 만듭니다.

`MCP`는 Model Context Protocol입니다. LLM이 외부 도구를 표준화된 방식으로 사용할 수 있게 해주는 프로토콜입니다.

## 5. 환경 변수

프로젝트 루트에 `.env` 파일을 두고 다음 값을 사용합니다.

```env
AWS_REGION=us-east-1
MODEL_ID=사용할_Bedrock_모델_ID
AWS_BEARER_TOKEN_BEDROCK=필요한_경우_토큰
```

코드에서 반복적으로 쓰는 값은 주로 `AWS_REGION`, `MODEL_ID`입니다.

주의할 점:

- `.env`는 `.gitignore`에 들어 있어서 GitHub에 올라가지 않습니다.
- 선택한 `MODEL_ID`가 해당 AWS 리전에서 사용 가능해야 합니다.
- AWS 계정에 Bedrock 모델 호출 권한이 있어야 합니다.

## 6. web/app.py: 화면 담당

`web/app.py`는 Streamlit 화면입니다.

역할:

- 채팅 UI를 보여줍니다.
- 사용자의 입력을 받습니다.
- `http://localhost:8000/chat`으로 POST 요청을 보냅니다.
- 서버 응답을 받아 화면에 표시합니다.
- 이전 대화 내용은 `st.session_state.messages`에 저장합니다.

중요한 코드 흐름:

```python
res = req.post(API_URL, json={"query": prompt})
result = res.json().get("response")
```

여기서 `API_URL`은 FastAPI 서버 주소입니다.

```python
API_URL = "http://localhost:8000/chat"
```

## 7. web/server.py: API 담당

`web/server.py`는 FastAPI 백엔드입니다.

역할:

- `/chat` API를 제공합니다.
- 요청 JSON에서 `query` 값을 받습니다.
- `llm.chain.invoke({"user_input": req.query})`를 호출합니다.
- LLM 응답을 JSON으로 반환합니다.

핵심 코드:

```python
@app.post("/chat")
async def chat(req: UserRequest):
    response = chain.invoke({"user_input": req.query})
    return {"response": response.content}
```

여기서 `UserRequest`는 요청 데이터 모양을 정의합니다.

```python
class UserRequest(BaseModel):
    query: str
```

## 8. llm/__init__.py: LLM chain 담당

`llm/__init__.py`는 Bedrock 모델과 프롬프트를 연결해 `chain`을 만듭니다.

흐름:

1. `.env` 로드
2. `boto3.client("bedrock-runtime")` 생성
3. `ChatBedrockConverse` 생성
4. few-shot 예시 구성
5. `ChatPromptTemplate` 생성
6. `last_prompt | llm` 형태로 chain 생성

핵심 코드:

```python
llm = ChatBedrockConverse(
    client=bedrock_client,
    model_id=os.getenv("MODEL_ID"),
    max_tokens=512,
    temperature=0.7,
)

chain = last_prompt | llm
```

`|` 연산자는 LangChain Expression Language, 즉 LCEL입니다.

```text
prompt | llm
```

이라는 코드는 “프롬프트를 만든 뒤 그 결과를 LLM에게 전달한다”는 뜻입니다.

## 9. ChatBedrockConverse는 언제 쓰나

`ChatBedrockConverse`는 AWS Bedrock의 Converse API를 LangChain에서 쉽게 쓰게 해주는 클래스입니다.

사용 목적:

- Bedrock 모델을 채팅형 LLM으로 사용합니다.
- LangChain chain 안에서 Bedrock 모델을 호출합니다.
- 여러 Bedrock 모델의 대화형 호출 방식을 비교적 표준화된 형태로 다룹니다.

처음 배울 때는 이렇게 기억하면 됩니다.

```text
ChatBedrockConverse = Bedrock에 있는 채팅 모델을 LangChain chain에 연결하는 LLM 객체
```

`ChatBedrock`과 `ChatBedrockConverse`는 둘 다 Bedrock 모델 호출용입니다. `ChatBedrockConverse`는 Bedrock의 Converse API 쪽에 맞춘 더 표준화된 채팅 호출 래퍼라고 보면 됩니다.

## 10. Pylance 경고와 model/model_id

VS Code Pylance에서 다음 경고가 보일 수 있습니다.

```text
Argument missing for parameter "model"
No parameter named "model_id"
```

이것은 주로 타입 검사 경고입니다. 실제 설치된 `langchain-aws` 런타임에서는 `model_id`와 `model`이 alias 관계로 동작할 수 있습니다.

경고를 줄이고 싶으면 다음처럼 `model=`을 사용할 수 있습니다.

```python
llm = ChatBedrockConverse(
    client=bedrock_client,
    model=os.getenv("MODEL_ID"),
)
```

또는 현재 프로젝트에는 `.vscode/settings.json`에 일부 Pylance 진단을 끄는 설정이 들어 있습니다.

```json
{
  "python.analysis.diagnosticSeverityOverrides": {
    "reportCallIssue": "none",
    "reportUnusedCoroutine": "none"
  }
}
```

## 11. RAG 폴더 이해

`rag/`는 문서 검색 기반 답변을 실험하는 폴더입니다.

흐름:

```text
텍스트 문서
  ↓
문서 로드
  ↓
청크 분할
  ↓
BedrockEmbeddings로 벡터화
  ↓
FAISS에 저장
  ↓
질문이 들어오면 관련 문서 검색
  ↓
검색 결과를 LLM 프롬프트에 함께 전달
```

파일별 역할:

- `rag_test1.py`: FAISS 검색을 간단히 확인합니다.
- `rag_test2.py`: 텍스트 파일을 읽고 FAISS 인덱스를 만듭니다.
- `rag_test3.py`: 저장된 FAISS 인덱스를 불러와 RAG chain을 실행합니다.
- `rag/data/`: 검색 대상 텍스트 데이터입니다.
- `hp-story/`: 생성된 FAISS 인덱스 저장 위치입니다.

## 12. LangGraph 폴더 이해

`langgraph/`는 에이전트 흐름을 그래프로 구성하는 연습입니다.

기본 개념:

- `State`: 그래프 전체에서 공유되는 데이터입니다.
- `Node`: 하나의 작업 단위입니다.
- `Edge`: 다음에 어느 노드로 갈지 정하는 연결입니다.
- `Conditional Edge`: 조건에 따라 다른 노드로 이동하는 연결입니다.

주요 파일:

- `lg_test1.py`: 가장 단순한 그래프 흐름
- `lg_test2.py`: LLM이 도구 사용 여부를 판단하고 `ToolNode`로 이동하는 흐름
- `lg_test3.py`: `MemorySaver`로 대화 상태를 저장하는 흐름
- `lg_rag_agent.py`: RAG 검색 도구를 사용하는 에이전트 흐름
- `tools.py`: `@tool`로 LangChain tool을 정의하는 파일

`bind_tools`는 LLM에게 “이런 도구들을 사용할 수 있다”고 알려주는 메서드입니다.

```python
llm_with_tools = llm.bind_tools(tools)
```

Pylance에서 `bind_tools`에 빨간 줄이 뜨는 경우는 보통 `self.llm = None`처럼 타입이 애매하게 시작해서, Pylance가 “이 값이 None일 수도 있다”고 판단하기 때문입니다.

## 13. A2A 폴더 이해

`a2a/`는 Agent to Agent 패턴을 실험합니다.

`a2a_langchain.py`는 LangChain chain 세 개를 연결합니다.

```text
developer_agent
  ↓ 코드 초안 작성
reviewer_agent
  ↓ 리뷰 또는 PASS
refiner_agent
  ↓ 리뷰 반영 후 최종 코드 작성
```

`a2a_langgraph.py`는 같은 흐름을 LangGraph로 구성합니다.

```text
coder node
  ↓
reviewer node
  ↓ 조건 확인
  ├─ PASS 또는 반복 횟수 초과 → 종료
  └─ FAIL → coder node로 돌아가 재작성
```

이 파일에서 배울 포인트:

- `TypedDict`로 AgentState 정의
- `messages`에 대화 기록 누적
- `iterations`로 반복 횟수 제한
- `add_conditional_edges`로 분기 처리

## 14. MCP 폴더 이해

`mcp/`는 Model Context Protocol 실험 폴더입니다.

현재 핵심 흐름은 `stdio` 기반입니다.

```text
client.py 실행
  ↓
client가 server.py를 자식 프로세스로 실행
  ↓
표준입출력으로 MCP 메시지 교환
  ↓
tool 목록 조회 또는 tool 호출
```

중요한 점은 `mcp/server.py`를 HTTP 서버처럼 미리 켜두는 구조가 아니라는 것입니다.

현재 `mcp/server.py`는 다음 방식으로 실행됩니다.

```python
mcp.run(transport="stdio")
```

즉 `client.py`가 `server.py`를 직접 실행해 통신합니다.

## 15. mcp/server.py: MCP tool 서버

`mcp/server.py`는 `FastMCP`로 6개 tool을 제공합니다.

제공 tool:

- `add(a, b)`: 두 숫자를 더합니다.
- `get_time()`: 현재 시간을 반환합니다.
- `save_note(note_id, note_content)`: 메모를 저장합니다.
- `list_note()`: 저장된 메모 목록을 조회합니다.
- `delete_note(note_id)`: 메모를 삭제합니다.
- `rag_search(query)`: 저장된 메모에서 검색어와 맞는 내용을 찾습니다.

tool 등록은 `@mcp.tool()` 데코레이터로 합니다.

```python
@mcp.tool()
def add(a: float, b: float) -> str:
    ...
```

## 16. mcp/client.py와 실행 위치

`mcp/client.py`는 MCP 서버에 연결해 tool 목록을 확인합니다.

중요한 실행 명령:

```powershell
cd C:\Users\Dell3571\Projects\llm_langchain_bedrock\mcp
..\llm_venv\Scripts\python.exe client.py
```

왜 `mcp` 폴더에서 실행해야 하나?

`client.py` 기본값이 다음과 같기 때문입니다.

```python
def __init__(self, server_script: str = "server.py"):
```

즉 현재 작업 디렉터리에서 `server.py`를 찾습니다. 프로젝트 루트에서 실행하면 `mcp/server.py`가 아니라 루트의 `server.py`를 찾으려고 해서 실패할 수 있습니다.

## 17. mcp/mcp_tools_adapter.py

`mcp_tools_adapter.py`는 `client.py`보다 더 많은 테스트를 합니다.

역할:

- MCP 서버에 연결합니다.
- tool 목록을 출력합니다.
- `add`, `get_time`, `save_note`, `list_note`, `delete_note` 등을 실제 호출합니다.
- tool 호출 결과를 출력합니다.

이 파일은 “MCP 서버와 tool 호출이 제대로 되는지 확인하는 테스트 클라이언트”로 보면 됩니다.

## 18. mcp/bedrock_mcp_agent.py

`bedrock_mcp_agent.py`는 아직 완성된 실행 앱이라기보다 실험 중인 파일입니다.

목표:

```text
Bedrock LLM
  +
LangGraph workflow
  +
MCP tools
```

를 합쳐서 “LLM이 MCP tool을 사용할 수 있는 에이전트”를 만드는 것입니다.

현재 구현된 내용:

- `BedrockMCPAgent` 클래스 뼈대
- Bedrock `ChatBedrock` 초기화
- `StateGraph(MessagesState)` 기반 그래프 구성 시작
- `ToolNode(self.tools)` 추가
- `bind_tools(self.tools)` 사용 시도

아직 주의할 점:

- `_init_llm`이 `async def`인데 `initialize()` 안에서는 `await` 없이 호출되고 있습니다.
- `self.tools`를 MCP 서버에서 가져오는 로직이 아직 연결되지 않았습니다.
- `call_agent`, 조건부 함수의 종료 반환 등이 아직 완성되지 않았습니다.
- 따라서 학습/구현 중인 파일로 보고, 런타임 완성본으로 의존하면 안 됩니다.

## 19. 실행 명령 정리

FastAPI 서버 실행:

```powershell
cd C:\Users\Dell3571\Projects\llm_langchain_bedrock
.\llm_venv\Scripts\python.exe -m uvicorn web.server:app --reload --port 8000
```

Streamlit 앱 실행:

```powershell
cd C:\Users\Dell3571\Projects\llm_langchain_bedrock
.\llm_venv\Scripts\python.exe -m streamlit run web\app.py
```

MCP client 실행:

```powershell
cd C:\Users\Dell3571\Projects\llm_langchain_bedrock\mcp
..\llm_venv\Scripts\python.exe client.py
```

MCP tool adapter 실행:

```powershell
cd C:\Users\Dell3571\Projects\llm_langchain_bedrock\mcp
..\llm_venv\Scripts\python.exe mcp_tools_adapter.py
```

## 20. 자주 헷갈린 지점

`uvicorn server:app`은 현재 구조에서는 주의해야 합니다.

`web/server.py`를 실행하려면 루트에서 다음처럼 실행합니다.

```powershell
.\llm_venv\Scripts\python.exe -m uvicorn web.server:app --reload --port 8000
```

`mcp` 폴더 안에서 `uvicorn server:app`을 실행하면 `mcp/server.py`를 읽습니다. 그런데 `mcp/server.py`에는 `app`이 아니라 `mcp = FastMCP(...)`가 있으므로 `Attribute "app" not found` 오류가 납니다.

MCP stdio 서버는 FastAPI 서버처럼 브라우저나 HTTP 포트에 직접 띄우는 서버가 아닙니다. client가 server를 자식 프로세스로 실행해서 통신합니다.

Pylance 빨간 줄은 실제 실행 오류와 다를 수 있습니다. 특히 LangChain, Pydantic, Bedrock 래퍼는 동적 필드/alias를 많이 쓰기 때문에 타입체커가 못 따라가는 경우가 있습니다.

## 21. 현재 학습 순서 추천

처음부터 다시 복습한다면 다음 순서가 좋습니다.

1. `web/app.py`, `web/server.py`로 프론트와 백엔드 흐름 이해
2. `llm/__init__.py`로 `ChatPromptTemplate`, few-shot, `ChatBedrockConverse`, LCEL chain 이해
3. `rag/rag_test2.py`, `rag/rag_test3.py`로 RAG 흐름 이해
4. `langgraph/lg_test1.py`로 StateGraph 기본 이해
5. `langgraph/lg_test2.py`, `lg_test3.py`로 tool calling과 memory 이해
6. `a2a/a2a_langchain.py`, `a2a/a2a_langgraph.py`로 agent 협업 패턴 이해
7. `mcp/server.py`, `mcp/client.py`, `mcp_tools_adapter.py`로 MCP stdio tool 서버 이해
8. `mcp/bedrock_mcp_agent.py`로 Bedrock + LangGraph + MCP 통합 실험 진행

## 22. 한 문장으로 기억하기

```text
이 프로젝트는 Bedrock LLM 호출을 중심에 두고, LangChain chain, RAG 검색, LangGraph 에이전트, A2A 협업, MCP tool 사용까지 단계적으로 확장해 보는 학습용 저장소다.
```
