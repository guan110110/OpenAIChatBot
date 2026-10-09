"""
OpenSupport Web Server - FastAPI Native Customer Service Console.
零前端构建依赖，原生支持即开即用的高颜值智能客服 Web 工作台。
"""

import os
import sys
import webbrowser

# 防止 Windows GBK 终端下打印特殊字符/Emoji 报错
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 注入项目根目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opensupport.agent import CustomerServiceAgent
from opensupport.session import SessionManager

app = FastAPI(title="OpenSupport AI Console")
session_manager = SessionManager()
agent = CustomerServiceAgent(session_manager=session_manager)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "web_user_01"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenSupport - 智能客服 AI Agent 工作台</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        .chat-scroll::-webkit-scrollbar { width: 6px; }
        .chat-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 3px; }
    </style>
</head>
<body class="bg-slate-100 h-screen flex flex-col font-sans">

    <!-- 顶部导航 -->
    <header class="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-blue-500/20">
                <i class="fa-solid fa-headset"></i>
            </div>
            <div>
                <h1 class="text-lg font-bold text-slate-800">OpenSupport <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200 ml-1">AI Agent Console</span></h1>
                <p class="text-xs text-slate-500">通用智能客服框架 • 意图分流 | 槽位填充 | 业务办理 | 情绪转人工</p>
            </div>
        </div>
        <div class="flex items-center space-x-3">
            <span class="text-xs bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full border border-emerald-200 flex items-center">
                <span class="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                当前引擎: <b class="ml-1" id="engine-name">加载中...</b>
            </span>
            <button onclick="resetSession()" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1.5 rounded-lg border border-slate-300 transition">
                <i class="fa-solid fa-rotate-right mr-1"></i> 重置对话
            </button>
        </div>
    </header>

    <!-- 主体区域：左右分栏 -->
    <main class="flex-1 flex overflow-hidden max-w-7xl w-full mx-auto p-4 gap-4">

        <!-- 左侧：Agent 内部思考与决策看板 -->
        <aside class="w-80 bg-white rounded-2xl shadow-sm border border-slate-200 p-4 flex flex-col gap-4 overflow-y-auto">
            <div>
                <h2 class="text-sm font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center">
                    <i class="fa-solid fa-brain text-blue-500 mr-2"></i> Agent 决策监控看板
                </h2>
                <p class="text-xs text-slate-500">实时观察 AI 客服内部的状态机流转与决策逻辑。</p>
            </div>

            <!-- 1. 当前意图 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <div class="text-xs text-slate-500 mb-1">识别意图 (Intent)</div>
                <div id="badge-intent" class="inline-block px-2.5 py-1 rounded-md text-xs font-bold bg-slate-200 text-slate-700">
                    等待对话...
                </div>
            </div>

            <!-- 2. 情绪监控表盘 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-xs text-slate-500">客户愤怒指数 (Sentiment)</span>
                    <span id="sentiment-text" class="text-xs font-bold text-slate-700">1 / 5 (平静)</span>
                </div>
                <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div id="sentiment-bar" class="bg-emerald-500 h-full w-[20%] transition-all duration-300"></div>
                </div>
                <div class="text-[10px] text-slate-400 mt-1">≥4 分将自动生成工单并转接人工客服主管</div>
            </div>

            <!-- 3. 槽位状态机 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <div class="text-xs text-slate-500 mb-2">已收集槽位 (Slots)</div>
                <div id="slots-container" class="space-y-1.5 text-xs">
                    <div class="text-slate-400 italic">暂无槽位数据</div>
                </div>
            </div>

            <!-- 4. 工单记录 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200 flex-1">
                <div class="text-xs text-slate-500 mb-2 flex items-center justify-between">
                    <span>转人工工单 (Tickets)</span>
                    <span id="ticket-count" class="text-[10px] bg-red-100 text-red-600 font-bold px-1.5 py-0.5 rounded">0</span>
                </div>
                <div id="tickets-container" class="space-y-2 text-xs overflow-y-auto max-h-36">
                    <div class="text-slate-400 italic">当前未产生转接工单</div>
                </div>
            </div>

            <!-- 5. 快捷测试按钮 -->
            <div>
                <div class="text-xs font-bold text-slate-600 mb-2 flex items-center">
                    <i class="fa-solid fa-wand-magic-sparkles text-amber-500 mr-1.5"></i> 快捷测试用例 (一键点击)
                </div>
                <div class="grid grid-cols-1 gap-1.5">
                    <button onclick="quickSend('你们支持7天无理由退货吗？')" class="text-left text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-600 p-2 rounded-lg border border-slate-200 transition">
                        📘 <b>FAQ咨询</b>: 支持7天退换吗？
                    </button>
                    <button onclick="quickSend('帮我查下我的快递到哪了')" class="text-left text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-600 p-2 rounded-lg border border-slate-200 transition">
                        🔍 <b>槽位追问</b>: 查快递 (不给单号)
                    </button>
                    <button onclick="quickSend('单号是 ORD1001')" class="text-left text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-600 p-2 rounded-lg border border-slate-200 transition">
                        🎯 <b>补填单号</b>: 单号是 ORD1001
                    </button>
                    <button onclick="quickSend('我要申请退款，订单号是 ORD1002')" class="text-left text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-600 p-2 rounded-lg border border-slate-200 transition">
                        🔄 <b>退换业务</b>: 申请退款 ORD1002
                    </button>
                    <button onclick="quickSend('你们这什么垃圾服务！再不退钱我直接打12315投诉你们！')" class="text-left text-xs bg-red-50 hover:bg-red-100 text-red-700 p-2 rounded-lg border border-red-200 transition">
                        🚨 <b>暴怒测试</b>: 触发打分转人工工单
                    </button>
                </div>
            </div>
        </aside>

        <!-- 右侧：现代客服聊天对话框 -->
        <section class="flex-1 bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col overflow-hidden">
            <!-- 聊天记录区域 -->
            <div id="chat-messages" class="flex-1 p-6 overflow-y-auto chat-scroll space-y-4">
                <!-- 欢迎消息 -->
                <div class="flex items-start space-x-3">
                    <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs flex-shrink-0 shadow-sm">
                        <i class="fa-solid fa-headset"></i>
                    </div>
                    <div class="bg-slate-100 text-slate-800 p-3.5 rounded-2xl rounded-tl-none max-w-lg text-sm leading-relaxed border border-slate-200">
                        您好！我是官方旗舰店智能客服助理<b>小智</b> 😊<br><br>
                        我可以为您办理：<br>
                        • 📦 <b>订单与物流查询</b>（如“查下 ORD1001 的物流”）<br>
                        • 🔄 <b>退货与退款申请</b>（如“我想退款 ORD1002”）<br>
                        • 📘 <b>售后政策解答</b>（如“运费险规则、保修期”）<br><br>
                        请问今天有什么我可以协助您的吗？
                    </div>
                </div>
            </div>

            <!-- 输入框区域 -->
            <div class="p-4 border-t border-slate-200 bg-white">
                <form id="chat-form" onsubmit="sendMessage(event)" class="flex items-center space-x-2">
                    <input type="text" id="user-input" placeholder="输入您的问题，例如：'帮我查下我的快递到哪了'..." autocomplete="off"
                           class="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition">
                    <button type="submit" id="send-btn"
                            class="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-medium text-sm flex items-center space-x-1.5 shadow-md shadow-blue-500/20 transition">
                        <span>发送</span>
                        <i class="fa-solid fa-paper-plane text-xs"></i>
                    </button>
                </form>
            </div>
        </section>

    </main>

    <script>
        const sessionId = "web_user_" + Math.random().toString(36).substring(2, 8);

        // 页面初始化
        window.onload = async () => {
            const res = await fetch("/api/info");
            const data = await res.json();
            document.getElementById("engine-name").innerText = data.provider;
        };

        function quickSend(text) {
            document.getElementById("user-input").value = text;
            sendMessage(new Event('submit'));
        }

        async function sendMessage(e) {
            e.preventDefault();
            const input = document.getElementById("user-input");
            const text = input.value.trim();
            if (!text) return;

            input.value = "";
            appendMessage("user", text);

            const sendBtn = document.getElementById("send-btn");
            sendBtn.disabled = true;
            sendBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;

            try {
                const resp = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: text, session_id: sessionId })
                });
                const data = await resp.json();
                appendMessage("assistant", data.reply);
                updateDashboard(data.state);
            } catch (err) {
                appendMessage("assistant", "⚠️ 连接服务异常，请稍后重试。");
            } finally {
                sendBtn.disabled = false;
                sendBtn.innerHTML = `<span>发送</span><i class="fa-solid fa-paper-plane text-xs"></i>`;
            }
        }

        function appendMessage(role, content) {
            const container = document.getElementById("chat-messages");
            const div = document.createElement("div");
            div.className = "flex items-start space-x-3 " + (role === "user" ? "flex-row-reverse space-x-reverse" : "");

            const avatar = role === "user"
                ? `<div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white text-xs flex-shrink-0"><i class="fa-solid fa-user"></i></div>`
                : `<div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs flex-shrink-0"><i class="fa-solid fa-headset"></i></div>`;

            const bubbleClass = role === "user"
                ? "bg-blue-600 text-white rounded-tr-none shadow-md shadow-blue-500/10"
                : "bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200";

            div.innerHTML = `
                ${avatar}
                <div class="${bubbleClass} p-3.5 rounded-2xl max-w-lg text-sm leading-relaxed whitespace-pre-wrap">${content}</div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function updateDashboard(state) {
            // 1. 意图更新
            const intentBadge = document.getElementById("badge-intent");
            intentBadge.innerText = state.current_intent;
            intentBadge.className = "inline-block px-2.5 py-1 rounded-md text-xs font-bold " + 
                (state.current_intent === "HUMAN_TRANSFER" ? "bg-red-100 text-red-700" :
                 state.current_intent === "ORDER_QUERY" ? "bg-blue-100 text-blue-700" :
                 state.current_intent === "REFUND" ? "bg-purple-100 text-purple-700" : "bg-emerald-100 text-emerald-700");

            // 2. 情绪更新
            const score = state.sentiment_score;
            const sentimentBar = document.getElementById("sentiment-bar");
            const sentimentText = document.getElementById("sentiment-text");
            sentimentBar.style.width = (score * 20) + "%";
            sentimentBar.className = "h-full transition-all duration-300 " + 
                (score >= 4 ? "bg-red-500" : score >= 3 ? "bg-amber-500" : "bg-emerald-500");
            sentimentText.innerText = `${score} / 5 (${score >= 4 ? "极度愤怒" : score >= 3 ? "烦躁不满" : "平静友好"})`;

            // 3. 槽位更新
            const slotsContainer = document.getElementById("slots-container");
            const slots = state.slots || {};
            if (Object.keys(slots).length === 0) {
                slotsContainer.innerHTML = `<div class="text-slate-400 italic">暂无槽位数据</div>`;
            } else {
                slotsContainer.innerHTML = Object.entries(slots).map(([k, v]) => `
                    <div class="flex justify-between bg-white px-2 py-1 rounded border border-slate-200">
                        <span class="text-slate-500">${k}:</span>
                        <span class="font-bold text-slate-800">${v}</span>
                    </div>
                `).join("");
            }

            // 4. 工单更新
            const ticketContainer = document.getElementById("tickets-container");
            const tickets = state.tickets || [];
            document.getElementById("ticket-count").innerText = tickets.length;
            if (tickets.length > 0) {
                ticketContainer.innerHTML = tickets.map(t => `
                    <div class="bg-red-50 p-2 rounded border border-red-200 text-red-800">
                        <div class="font-bold flex justify-between">
                            <span>${t.ticket_id}</span>
                            <span class="text-[10px] bg-red-200 px-1 rounded">${t.status}</span>
                        </div>
                        <div class="text-[10px] text-slate-500 mt-1">${t.reason}</div>
                    </div>
                `).join("");
            }
        }

        async function resetSession() {
            window.location.reload();
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/info")
async def get_info():
    return {"provider": agent.llm_cfg["provider"]}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    reply, state = agent.process_message(req.message, session_id=req.session_id)
    return JSONResponse(content={
        "reply": reply,
        "state": state.model_dump()
    })

def main(host: str = "127.0.0.1", port: int = 8501):
    url = f"http://{host}:{port}"
    print(f"\n[OpenSupport] 智能客服 Web 控制台正在启动...")
    print(f"本地访问地址: {url}")
    print(f"正在尝试在浏览器中打开该页面...\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
