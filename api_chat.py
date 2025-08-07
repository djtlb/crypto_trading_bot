from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

app = FastAPI()

# Allow CORS for web chat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory message store (for demo)
chat_history: List[dict] = []

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Store message
            chat_history.append({"from": "user", "message": data})
            # Echo or forward to trader logic here
            reply = f"Trader received: {data}"
            chat_history.append({"from": "trader", "message": reply})
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        pass

@app.get("/chat/history")
def get_history():
    return chat_history

if __name__ == "__main__":
    print("🚀 Starting Chat API Server on port 8001...")
    uvicorn.run(
        "api_chat:app", 
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
