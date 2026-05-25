import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.bots import router as bots_router
from app.api.v1.models import router as models_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.messaging import router as messaging_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

# 🗄️ Auto-create database tables on startup if they don't exist
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 🌐 CORS Middleware Configuration
# Allows the React/Vite frontend (running on other localhost ports) to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ Global Database Exception Handler
# Prevents backend from crashing on db connection failures and keeps details out of the API response
@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    # Log the real error securely on the server side so developers can diagnose it
    logger.error("Database connection or query execution failure: %s", str(exc), exc_info=True)
    
    # Return a clean, safe, and structured 503 response to the frontend client
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database service is temporarily unavailable. Please verify that the database server is running and connection credentials in your .env file are correct."
        }
    )

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(bots_router, prefix=f"{settings.API_V1_STR}", tags=["bots"])
app.include_router(models_router, prefix=f"{settings.API_V1_STR}/models", tags=["models"])
app.include_router(knowledge_router, prefix=f"{settings.API_V1_STR}/knowledge", tags=["knowledge"])
app.include_router(messaging_router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])

from app.api.v1.analytics import router as analytics_router
from app.api.v1.agents import router as agents_router

app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(agents_router, prefix=f"{settings.API_V1_STR}/agents", tags=["agents"])

from app.api.v1.channels import router as channels_router
from app.api.v1.deployments import router as deployments_router
from app.api.v1.billing import router as billing_router
from app.api.v1.team import router as team_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.notifications import router as notifications_router

app.include_router(channels_router, prefix=f"{settings.API_V1_STR}/channels", tags=["channels"])
app.include_router(deployments_router, prefix=f"{settings.API_V1_STR}/deployments", tags=["deployments"])
app.include_router(billing_router, prefix=f"{settings.API_V1_STR}")
app.include_router(team_router, prefix=f"{settings.API_V1_STR}")
app.include_router(api_keys_router, prefix=f"{settings.API_V1_STR}")
app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}")


from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.analytics_aggregation import run_nightly_aggregation

@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run daily aggregation at 12:05 AM (00:05) every day
    scheduler.add_job(run_nightly_aggregation, "cron", hour=0, minute=5)
    scheduler.start()
    logger.info("APScheduler initialized and started nightly aggregation task.")


@app.get("/")
def root():
    return {"message": "Welcome to Aina AI Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/widget.js", include_in_schema=False)
def widget_script():
    script = """
(function () {
  var config = window.AinaConfig || {};
  if (!config.deploymentId || document.getElementById("aina-widget-root")) return;

  var apiBaseUrl = config.apiBaseUrl || "";
  var root = document.createElement("div");
  root.id = "aina-widget-root";
  root.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:2147483647;font-family:Inter,system-ui,sans-serif";

  var panel = document.createElement("div");
  panel.style.cssText = "display:none;width:320px;max-width:calc(100vw - 40px);height:420px;margin-bottom:12px;border:1px solid #ddd;border-radius:16px;background:#fff;box-shadow:0 16px 48px rgba(0,0,0,.18);overflow:hidden";

  var header = document.createElement("div");
  header.textContent = config.name || "Aina Bot";
  header.style.cssText = "padding:14px 16px;background:" + (config.primaryColor || "#1c1c1e") + ";color:#fff;font-weight:700";

  var messages = document.createElement("div");
  messages.style.cssText = "height:295px;overflow:auto;padding:14px;font-size:13px;line-height:1.45;background:#f7f7f8";

  var form = document.createElement("form");
  form.style.cssText = "display:flex;gap:8px;padding:10px;border-top:1px solid #eee";
  var input = document.createElement("input");
  input.placeholder = "Type a message...";
  input.style.cssText = "flex:1;border:1px solid #ddd;border-radius:10px;padding:10px;outline:none";
  var send = document.createElement("button");
  send.textContent = "Send";
  send.type = "submit";
  send.style.cssText = "border:0;border-radius:10px;padding:0 12px;background:" + (config.primaryColor || "#1c1c1e") + ";color:#fff;font-weight:700";
  form.appendChild(input);
  form.appendChild(send);

  var launcher = document.createElement("button");
  launcher.textContent = "Chat";
  launcher.style.cssText = "float:right;border:0;border-radius:999px;padding:14px 18px;background:" + (config.primaryColor || "#1c1c1e") + ";color:#fff;font-weight:700;box-shadow:0 10px 30px rgba(0,0,0,.2);cursor:pointer";

  function addMessage(role, text) {
    var node = document.createElement("div");
    node.textContent = text;
    node.style.cssText = "margin:8px 0;padding:10px 12px;border-radius:12px;white-space:pre-wrap;" + (role === "user" ? "background:#1c1c1e;color:#fff;margin-left:40px" : "background:#fff;color:#1c1c1e;margin-right:40px");
    messages.appendChild(node);
    messages.scrollTop = messages.scrollHeight;
  }

  var conversationId = null;
  launcher.onclick = function () {
    panel.style.display = panel.style.display === "none" ? "block" : "none";
  };
  form.onsubmit = function (event) {
    event.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    addMessage("user", text);
    fetch(apiBaseUrl + "/api/v1/chat/public/deployments/" + config.deploymentId + "/message", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text, conversation_id: conversationId})
    }).then(function (res) {
      if (!res.ok) throw new Error("Chat request failed");
      return res.json();
    }).then(function (data) {
      conversationId = data.conversation_id;
      addMessage("bot", data.response || "I could not generate a response.");
    }).catch(function () {
      addMessage("bot", "Sorry, the chatbot is unavailable right now.");
    });
  };

  panel.appendChild(header);
  panel.appendChild(messages);
  panel.appendChild(form);
  root.appendChild(panel);
  root.appendChild(launcher);
  document.body.appendChild(root);
  addMessage("bot", "Hi! How can I help you today?");
})();
"""
    return Response(content=script, media_type="application/javascript")
