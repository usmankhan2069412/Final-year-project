from typing import Optional

def get_initial_handoff_message(language: Optional[str]) -> str:
    """Returns the message used when a conversation is first escalated to a human agent."""
    if language == "urdu":
        return "میں آپ کی درخواست کو کسٹمر سپورٹ ایجنٹ کو منتقل کر رہا ہوں۔ ہماری ٹیم جلد ہی آپ سے رابطہ کرے گی۔"
    elif language == "english":
        return "I am transferring your request to a support agent. Someone from our team will contact you shortly."
    else:
        return "Main aap ki request support agent ko transfer kar raha hoon. Thodi der mein humari team aap se rabta karegi."

def get_escalated_wait_message(language: Optional[str]) -> str:
    """Returns the message used when a user sends a message to an already escalated conversation."""
    if language == "urdu":
        return "سپورٹ ایجنٹ آپ کے پیغام کا جائزہ لے رہے ہیں اور جلد ہی جواب دیں گے۔"
    elif language == "english":
        return "A support agent is reviewing your message and will respond shortly."
    else:
        return "Support agent aap ke message ka jaiza le rahe hain aur jald hi jawab denge."
