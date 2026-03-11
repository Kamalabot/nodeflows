import anyio
import traceback
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

async def main():
    print("Testing connection to http://127.0.0.1:3001/sse")
    try:
        async with streamable_http_client("http://127.0.0.1:3001/sse") as (read_stream, write_stream, get_session_id):
            print("Connected transport!")
            
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("Session initialized!")
                
                tools = await session.list_tools()
                print(f"Tools loaded: {len(tools.tools)}")
                
    except Exception as e:
        print(f"Connection failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    anyio.run(main)
