import json
import enum

class ConversationStatus(str, enum.Enum):
    ONGOING = "ongoing"

try:
    print("Dumping enum:", json.dumps({"status": ConversationStatus.ONGOING}))
except Exception as e:
    print("Error:", e)
