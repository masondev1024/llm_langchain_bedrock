'''
MCP 1.27.2
외부 도구를 구현한 MCP 서버, FastMCP를 이용하여 간결하게 구성
'''

# 1. 모듈 가져오기
import sys
import logging
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 2. 로깅 설정
#    출력값 섞이면 불편 => stderr 출력 조정
logging.basicConfig(
    level  = logging.INFO,
    format = '[MCP Server] %(levelname)s: %(message)s',
    stream = sys.stderr
)
logger = logging.getLogger(__name__)

# 3. MCP 서버 설정
mcp = FastMCP('6ToolsMCPServer')
logger.info('MCPServer 구성 중...')


# 4. 인메모리 -> 메모/임시데이터를 저장할 tool 용도로 dict 형태로 저장관리용 -> 기본 구성 x
note_memory = dict()


# 5. 툴 구현 (외부에 특정 리소스, s/w, 기타 등등), 편의상 간단한 기능 구성, 6개
## Tool 1 : add (두수 더하기) -> 함수 구성, 타입 힌트 명시, 함수 주석
@mcp.tool()
def add(a: float, b: float) -> str:
    """두 개의 숫자를 더합니다."""
    result = a + b
    logger.info(f'Tool 1 add 호출: {a} + {b} = {result} ')
    return f'계산 결과: {a} + {b} = {result}'

## Tool 2 : get_time 서버측 현재시간
@mcp.tool()
def get_time() -> str:
    """서버의 현재 시간을 조회합니다."""
    cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f'현재시간: {cur_time}'

# CRUD 도구
## Tool 3 : save_note 메모 저장
@mcp.tool()
def save_note(note_id: str, note_content: str) -> str:
    '''
    메모를 인메모리 저장소에 저장합니다.
    Args:
        note_id: 메모의 고유 ID, 키값
        note_content: 메모 내용
    
    returns:
        저장 완료 메세지
    '''
    # 방어코드
    if not note_id or not note_content: # 내용 or id 없을 때
        logger.warning('필수 파라미터 누락')
        return "Fail: 필수 파라미터 누락"
    # 저장처리
    note_memory[note_id] = {
        "content" : note_content,
        "created_at" : datetime.now().isoformat()
    }
    # 로깅
    logger.info(f'save_note 호출: note_id = {note_id}')
    # 변환
    return f"메모 저장 완료: {note_id}"

## Tool 4 : list_note 메모 목록 조회
@mcp.tool()
def list_note() -> str:
    '''
    저장된 모든 메모의 목록을 조회합니다.
    Returns:
        메모 ID와 생성일이 포함된 문자열 목록
    '''
    logger.info('list_note 호출')
    if not note_memory:
        return "저장된 메모가 없습니다."
    # 존재하면 => 하나의 말뭉치로 구성 반환 (컨셉)
    lines = ["[메모 목록]"]
    for note_id, content in note_memory.items():
        lines.append(f"- ID: {note_id} (생성일: {content['created_at']})")
    return "\n".join(lines)

## Tool 5 : delete_note 메모 삭제
@mcp.tool()
def delete_note(note_id: str) -> str:  # Str -> str 타입 힌트 오류 수정
    '''
    특정 ID의 메모를 삭제합니다.
    Args:
        note_id: 메모의 고유 ID, 키값
    Returns:
        삭제 처리 결과 메시지 (기존 주석의 '현재 시간 문자열' 오류 수정)
    '''
    logger.info(f'delete_note 호출: note_id = {note_id}')
    if note_id in note_memory:
        del note_memory[note_id]
        return f"메모 삭제 완료: {note_id}"
    else:
        logger.warning(f'삭제 실패 (ID 없음): {note_id}')
        return f"Fail: 존재하지 않는 메모 ID입니다. ({note_id})"
    
## Tool 6 : rag_search 검색증강
@mcp.tool()
def rag_search(query: str) -> str:
    '''
    저장된 메모 데이터 중에서 검색어와 매칭되는 내용을 찾아 반환합니다. (간이 RAG)
    Args:
        query: 검색할 키워드 문자열
    Returns:
        매칭된 메모 결과 문자열
    '''
    logger.info(f'rag_search 호출: query = {query}')
    if not note_memory:
        return "검색할 데이터베이스(메모)가 비어 있습니다."
        
    results = []
    for nid, info in note_memory.items():
        # 대소문자 구분 없이 키워드 매칭 수행
        if query.lower() in info['content'].lower() or query.lower() in nid.lower():
            results.append(f"[ID: {nid}] {info['content']}")
            
    if not results:
        return f"'{query}'에 대한 검색 결과가 없습니다."
        
    return f"'{query}' 검색 결과 ({len(results)}건):\n" + "\n---\n".join(results)

 
# 6. 서버 가동
if __name__ == "__main__":
    # FastMCP는 run() 실행 시 기본적으로 실시간 표준 입출력(Stdio) 통신 방식으로 서버를 시작합니다.
    logger.info('MCPServer 가동 중...')
    logger.info('STDIO 모드로 가동 중...')
    mcp.run(transport="stdio")

