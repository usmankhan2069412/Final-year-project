import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.abspath("."))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.chat import ChatService
from app.models.chatbot import Chatbot

def test_streaming():
    db = SessionLocal()
    try:
        chatbot = db.query(Chatbot).first()
        if not chatbot:
            print("No chatbot found")
            return

        print(f"Testing with chatbot_id={chatbot.id}, org_id={chatbot.org_id}")
        stream_gen = ChatService.get_rag_stream(
            db=db,
            org_id=chatbot.org_id,
            chatbot_id=chatbot.id,
            user_message="HI, how are you."
        )
        for chunk in stream_gen:
            print("YIELDED:", chunk)
    finally:
        db.close()

if __name__ == "__main__":
    test_streaming()
