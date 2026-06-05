'''
MCP Server 와 통신
MCP에서 정의한 Tool을 Langchain/LangGraph 용 Tool로 변환 처리
LLM이 해당 도구에 대한 이해와, 사용 판단에 정확한 정보를 제공
'''
# 1. 모듈 가져오기
import asyncio
from typing import Optional
import sys
from mcp import ClientSession, StdioServerParameters # 커넥션 담당
from mcp.client.stdio import stdio_client # 입력, 출력을 가진 클라이언트
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model


# 2. MCPToolAdapter
class MCPToolAdapter:
    '''MCP Server와 통신. Langchain/LangGraph Tool로 변환 제공'''
    # 생성자
    def __init__(self, server_script: str = 'server.py'):
        self.server_script  = server_script
        self.mcp_tools      = [] # mcp Tool
        self.tools          = [] # MCP 서버에게 툴 목록 가져와서 저장
        self.read_stream    = None # 입력 스트림
        self.write_stream   = None # 출력 스트림
        self.session: Optional[ClientSession] = None # 세선 멤버변수 -> 여러 함수에서 사용하겠다.
        self._studio_context = None # 입출력에 관련한 내부적 프로세스 접근을 위한 컨텍스트
        pass
    # 초기화
    async def initialize( self ):
        '''MCP Server 연결, Tool 로드'''
        # MCP Server 접속시 필요한 정보 세팅
        server_params = StdioServerParameters(
            command= sys.executable,
            args= [self.server_script],
            env     = None
        )
        # 메세지가 오염 되면 => 출력을 sys.std
        print('MCP 서버 연결중..')
        try:
            # 입력, 출력, 세션등, 여러 함수에서 사용한다면 with x
            # MCP 서버를 접속할 때 사용하는 내부 컨텍스트 객체
            self._studio_context = stdio_client(server_params)
            # 내부 함수를 강제로 호출(내가 원하는 시점에 처리)
            stdio_tuple = await self._studio_context.__aenter__() 
            # 입력/출력 스트림 획득
            if isinstance( stdio_tuple, tuple):
                self.read_stream, self.write_stream = stdio_tuple
            else:
                self.read_stream = stdio_tuple
                self.write_stream = stdio_tuple

            # 세션 획득 => Tool을 가져올수 있음
            # JSON RPC 2.0 기준 상호 통신할 수 있는 논리적인 
            self.session = ClientSession(self.read_stream, self.write_stream)
            # 실제 활성화를 위해 직접 호출
            await self.session.__aenter__()
            # 세션 초기화
            await self.session.initialize()
            # MCP 서버에게 Tool 목록 요청
            res = await self.session.list_tools()
            self.mcp_tools = res.tools
            print(f'MCP 서버로부터 {len(self.mcp_tools)}개의 Tool 로드됨')

            return self

        except Exception as e : 
            print('MCP Server 연결 실패',e)
            raise
    # MCP tool -> langchain/langgraph tool 변환
    def create_langchain_tools(self) -> list:
        langchain_tools = list()

        # 툴 순회
        for mcp_tool in self.mcp_tools:
            # 툴 이름
            tool_name = mcp_tool.name
            tool_description = mcp_tool.description
            print( tool_name, tool_description )
            # 툴 설명
            pass

        return langchain_tools

    async def cleanup(self):
        '''입력/출력 스트림, 세션등 지원 해제(개발자 관리)'''
        # 세션이 존재하면 -> 세션 종료
        try:
            if self.session:
                await self.session.__aexit__(None,None,None)
        except Exception as e:
            print('세션 종료 에러',e)
        # 컨텍스트가 존재하면 -> 입력/출력 스트림 종료
        try:
            if self._studio_context:
                await self._studio_context.__aexit__(None,None,None)
        except Exception as e:
            print('입력/출력 스트림 종료 에러',e)

# 4. 테스트
if __name__ == '__main__':
    # 단위 테스트
    async def test():
        adapter = MCPToolAdapter('server.py')
        # 초기화
        await adapter.initialize()

        # MCP tool -> langchain/langgraph tool 변환
        tools = adapter.create_langchain_tools()

        # 해제
        await adapter.cleanup()
    
    asyncio.run(test())
    pass