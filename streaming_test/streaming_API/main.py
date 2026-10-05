from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import time
import asyncio
from typing import Generator, AsyncGenerator

app = FastAPI(title="Streaming API Demo")

"""
浏览器为了减少页面重排重绘、提升渲染性能，对普通文本文档（`text/plain`、`text/html`）有一个内部缓冲阈值（通常 1~4 KB 不等，不同浏览器有差异）：

- 收到的数据量没到阈值时，不会刷新页面显示，会先存在缓冲区里
- 直到数据攒够、或者响应结束，才会一次性渲染到页面上


测试的接口都远低于浏览器的缓冲阈值，所以浏览器会一直攒到响应结束，一次性全部显示出来，看起来就像 “不是流式”。



直接用curl命令行测试，就能看到服务端是逐块输出的，证明服务端的流式是正常的，只是浏览器做了缓冲。
curl -N http://127.0.0.1:8000/stream/basic
curl -N http://127.0.0.1:8000/stream/ai
curl -N http://127.0.0.1:8000/stream/file


以下在浏览器/控制台都可以看到效果：
curl -N http://127.0.0.1:8000/stream/sse

"""

# 基础同步流式输出（文本逐行推送）
def generate_text() -> Generator[str, None, None]:
    """同步生成器：逐行产出文本块"""
    lines = [
        "这是第1行流式数据\n",
        "这是第2行流式数据\n",
        "这是第3行流式数据\n",
        "流式传输结束\n"
    ]
    for line in lines:
        yield line
        time.sleep(1) 

@app.get("/stream/basic")
def stream_basic():
    """基础流式接口：同步生成器逐行返回文本"""
    return StreamingResponse(
        generate_text(),
        media_type="text/plain"
    )

# 异步流式输出
async def generate_ai_text() -> AsyncGenerator[str, None]:
    """异步生成器：模拟大模型逐字输出的打字效果"""
    full_text = "这是一段模拟大模型流式输出的文本，每个字会逐个推送到前端。"
    for char in full_text:
        yield char
        await asyncio.sleep(0.1)  # 模拟模型推理的生成间隔

@app.get("/stream/ai")
async def stream_ai():
    """AI风格流式接口：异步逐字返回文本"""
    return StreamingResponse(
        generate_ai_text(),
        media_type="text/plain"
    )

# 大文件流式下载 
def stream_large_file(file_path: str) -> Generator[bytes, None, None]:
    """分块读取文件，每次只加载一小块到内存"""
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):  # 每次读取 1MB
            yield chunk

@app.get("/stream/file")
def stream_file():
    """大文件流式下载接口"""
    file_path = r"C:\Users\Administrator\Desktop\研究生科研\面试\五维数据\streaming_API\test_file.txt"
    return StreamingResponse(
        stream_large_file(file_path),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=test_file.txt"}
    )

# SSE 标准服务器推送事件 
# 前端可通过 EventSource 原生接收，用于实时消息推送
async def sse_events() -> AsyncGenerator[str, None]:
    count = 0
    while True:
        count += 1
        # SSE 协议固定格式：data: 内容\n\n
        yield f"data: 实时推送消息 {count}\n\n"
        await asyncio.sleep(1)

@app.get("/stream/sse")
async def stream_sse():
    """SSE 流式事件接口"""
    return StreamingResponse(
        sse_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
