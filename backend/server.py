from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
import uuid
from context import prompt
import boto3
from botocore.exceptions import ClientError
import json
from datetime import datetime
from pathlib import Path
# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

client = OpenAI()

# Memory storage configuration
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET = os.getenv("S3_BUCKET", "")
MEMORY_DIR = os.getenv("MEMORY_DIR", "../memory")

# Initialize S3 client if needed
if USE_S3:
    s3_client = boto3.client("s3")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str
    timestamp: str

# Memory management
def get_memory_path(session_id: str) -> str:
    return f"{session_id}.json"

def load_conversation(session_id: str) -> List[Dict]:
    """Load conversation history form storage. Option local/S3"""
    if USE_S3:
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=get_memory_path(session_id))
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return []
            raise

    else:
        #  Local file storage
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

def save_conversation(session_id: str, messages: List[Dict]):
    """Save conversation history to storage"""
    if USE_S3:
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=get_memory_path(session_id),
                Body=json.dumps(messages, indent=2),
                ContentType="application/json",
            )
        except:
            os.makedirs(MEMORY_DIR, exist_ok=True)
            file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))
            with open(file_path, "w") as f:
                json.dump(messages, f, indent=2)

    else:
        # Local file storage
        os.makedirs(MEMORY_DIR, exist_ok=True)
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))
        with open(file_path, "w") as f:
            json.dump(messages, f, indent=2)


@app.get("/")
async def root():
    return {
        "message": "AI chatbot",
        "memory_enabled": True,
        "storage": "S3" if USE_S3 else "local",
        "ai_model": "OPEN AI"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "use_s3": USE_S3,
        "opan_ai_model": "gpt-4o-mini"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        conversation = load_conversation(session_id)

        # Only pass role/content to the model
        messages = [{"role": "system", "content": prompt()}]
        for msg in conversation:
            messages.append({"role": msg.get("role", "assistant"), "content": msg.get("content", "")})

        # Add current message
        messages.append({"role": "user", "content": request.message})

        # Call OpenAI api
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        assistant_response = response.choices[0].message.content

        # Update conversation history
        now_iso = datetime.utcnow().isoformat() + "Z"
        conversation.append({"role": "user", "content": request.message, "timestamp": now_iso})
        conversation.append({"role": "assistant", "content": assistant_response, "timestamp": datetime.utcnow().isoformat() + "Z"})

        save_conversation(session_id, conversation)

        return ChatResponse(
            response=assistant_response,
            session_id=session_id
        )

    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    """List all conversation sessions"""
    sessions = []
    if USE_S3:
        try:
            resp = s3_client.list_objects_v2(Bucket=S3_BUCKET)
            for obj in resp.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".json"):
                    session_id = Path(key).stem
                    conv = load_conversation(session_id)
                    created_ts = None
                    last_ts = None
                    if conv:
                        # Find first with timestamp and last with timestamp if available
                        for m in conv:
                            if m.get("timestamp"):
                                created_ts = m["timestamp"]
                                break
                        for m in reversed(conv):
                            if m.get("timestamp"):
                                last_ts = m["timestamp"]
                                break
                    sessions.append({
                        "session_id": session_id,
                        "message_count": len(conv),
                        "last_message": conv[-1]["content"] if conv else None,
                        "created_at": created_ts,
                        "last_message_timestamp": last_ts,
                    })
        except ClientError:
            pass
    else:
        for file_path in Path(MEMORY_DIR).glob("*.json"):
            session_id = file_path.stem
            with open(file_path, "r", encoding="utf-8") as f:
                conversation = json.load(f)
                created_ts = None
                last_ts = None
                if conversation:
                    for m in conversation:
                        if m.get("timestamp"):
                            created_ts = m["timestamp"]
                            break
                    for m in reversed(conversation):
                        if m.get("timestamp"):
                            last_ts = m["timestamp"]
                            break
                # Fallback to file times if no timestamps present
                if not created_ts:
                    try:
                        created_ts = datetime.utcfromtimestamp(file_path.stat().st_ctime).isoformat() + "Z"
                    except Exception:
                        created_ts = None
                if not last_ts:
                    try:
                        last_ts = datetime.utcfromtimestamp(file_path.stat().st_mtime).isoformat() + "Z"
                    except Exception:
                        last_ts = None

                sessions.append({
                    "session_id": session_id,
                    "message_count": len(conversation),
                    "last_message": conversation[-1]["content"] if conversation else None,
                    "created_at": created_ts,
                    "last_message_timestamp": last_ts,
                })
    return {"sessions": sessions}


@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Retrieve conversation history"""
    try:
        conversation = load_conversation(session_id)
        return {"session_id": session_id, "messages": conversation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

 
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
