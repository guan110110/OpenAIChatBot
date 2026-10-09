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
    <title>OpenSupport - 极简智能客服</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        .chat-scroll::-webkit-scrollbar { width: 5px; }
        .chat-scroll::-webkit-scrollbar-thumb { background-color: #e2e8f0; border-radius: 9999px; }
        .chat-scroll::-webkit-scrollbar-thumb:hover { background-color: #cbd5e1; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="bg-slate-50 h-screen flex flex-col font-sans text-slate-800 antialiased overflow-hidden">

    <!-- 极简顶部导航栏 -->
    <header class="bg-white/90 backdrop-blur border-b border-slate-200/80 px-6 py-3 flex items-center justify-between z-10">
        <div class="flex items-center space-x-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
                <i class="fa-solid fa-headset text-sm"></i>
            </div>
            <div>
                <div class="flex items-center space-x-2">
                    <h1 class="font-bold text-slate-800 text-sm tracking-tight">OpenSupport</h1>
                    <span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse"></span> 在线
                    </span>
                </div>
                <p class="text-[11px] text-slate-400">官方智能客服助理 • 极简模式</p>
            </div>
        </div>

        <div class="flex items-center space-x-2">
            <!-- 引擎标识 -->
            <span class="hidden sm:inline-flex items-center text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-lg border border-slate-200">
                <i class="fa-solid fa-microchip text-slate-400 mr-1.5 text-[11px]"></i>
                <span id="engine-name" class="font-medium">加载中...</span>
            </span>

            <!-- 决策监控抽屉触发按钮 -->
            <button onclick="toggleDrawer()" class="text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg border border-blue-200 flex items-center transition font-medium">
                <i class="fa-solid fa-brain mr-1.5"></i>
                <span>Agent 监控</span>
                <span id="drawer-slot-badge" class="hidden ml-1.5 w-2 h-2 rounded-full bg-blue-600"></span>
            </button>

            <!-- 重置按钮 -->
            <button onclick="resetSession()" title="清空对话记录" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 p-2 rounded-lg border border-slate-200 transition">
                <i class="fa-solid fa-rotate-right"></i>
            </button>
        </div>
    </header>

    <!-- 极简主体对话区 (居中流线型) -->
    <main class="flex-1 flex flex-col max-w-3xl w-full mx-auto overflow-hidden relative">

        <!-- 对话流消息容器 -->
        <div id="chat-messages" class="flex-1 overflow-y-auto px-4 py-6 chat-scroll space-y-5">
            <!-- 欢迎卡片 -->
            <div class="flex items-start space-x-3">
                <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs flex-shrink-0 shadow-sm mt-0.5">
                    <i class="fa-solid fa-headset"></i>
                </div>
                <div class="bg-white text-slate-800 p-4 rounded-2xl rounded-tl-sm max-w-lg text-sm leading-relaxed border border-slate-200/90 shadow-sm">
                    <p class="font-medium text-slate-900 mb-2">您好！我是官方智能客服助理 😊</p>
                    <p class="text-slate-600 mb-3">我可以为您提供以下服务：</p>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-600">
                        <div class="bg-slate-50 p-2 rounded-lg border border-slate-100 flex items-center space-x-2">
                            <span>📦</span><span><b>订单与物流查询</b></span>
                        </div>
                        <div class="bg-slate-50 p-2 rounded-lg border border-slate-100 flex items-center space-x-2">
                            <span>🔄</span><span><b>退换货与退款申请</b></span>
                        </div>
                        <div class="bg-slate-50 p-2 rounded-lg border border-slate-100 flex items-center space-x-2">
                            <span>📘</span><span><b>售后退换政策解答</b></span>
                        </div>
                        <div class="bg-slate-50 p-2 rounded-lg border border-slate-100 flex items-center space-x-2">
                            <span>🚨</span><span><b>情绪感知与人工转接</b></span>
                        </div>
                    </div>
                    <p class="text-slate-400 text-xs mt-3">您可以直接在下方输入问题，或点击快捷胶囊进行体验。</p>
                </div>
            </div>
        </div>

        <!-- 底部输入操作区 -->
        <div class="p-4 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent">
            <!-- 极简快捷胶囊横条 (横向滑动) -->
            <div class="flex items-center space-x-2 overflow-x-auto no-scrollbar pb-2.5 text-xs text-slate-600">
                <span class="text-slate-400 text-[11px] flex-shrink-0 flex items-center mr-1">
                    <i class="fa-solid fa-sparkles text-amber-500 mr-1"></i>快捷问答:
                </span>
                <button onclick="quickSend('帮我查下订单 ORD1001 的物流')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 px-3 py-1 rounded-full border border-slate-200 shadow-xs transition">
                    📦 查单号 ORD1001
                </button>
                <button onclick="quickSend('我要申请退款，订单号是 ORD1002')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 px-3 py-1 rounded-full border border-slate-200 shadow-xs transition">
                    🔄 申请退款 ORD1002
                </button>
                <button onclick="quickSend('你们支持7天无理由退货吗？')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 px-3 py-1 rounded-full border border-slate-200 shadow-xs transition">
                    📘 支持7天退换吗？
                </button>
                <button onclick="quickSend('帮我查下我的快递到哪了')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 px-3 py-1 rounded-full border border-slate-200 shadow-xs transition">
                    🔍 查物流 (未带单号)
                </button>
                <button onclick="quickSend('你们怎么回事？！东西全坏了，再不退钱我直接打12315投诉你们！')" class="flex-shrink-0 bg-white hover:bg-red-50 hover:text-red-600 hover:border-red-300 text-slate-600 px-3 py-1 rounded-full border border-slate-200 shadow-xs transition">
                    🚨 暴怒转人工测试
                </button>
            </div>

            <!-- 输入卡片 -->
            <form id="chat-form" onsubmit="sendMessage(event)" class="bg-white border border-slate-300/80 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/15 rounded-2xl p-2 pl-4 flex items-center shadow-sm transition">
                <input type="text" id="user-input" placeholder="输入您的问题，如“查下订单 ORD1001”或咨询售后政策..." autocomplete="off"
                       class="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 outline-none">
                <button type="submit" id="send-btn"
                        class="w-9 h-9 rounded-xl bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center transition shadow-sm shadow-blue-500/20 disabled:opacity-50">
                    <i class="fa-solid fa-paper-plane text-xs"></i>
                </button>
            </form>
            <div class="text-[11px] text-slate-400 text-center mt-2 flex items-center justify-center space-x-2">
                <span>OpenSupport AI Agent</span>
                <span>•</span>
                <span>极简客服模式</span>
            </div>
        </div>

    </main>

    <!-- 右侧滑出式 Agent 监控抽屉 (Collapsible Inspector Drawer) -->
    <div id="drawer-backdrop" onclick="toggleDrawer()" class="fixed inset-0 bg-slate-900/30 backdrop-blur-xs z-40 hidden transition-opacity opacity-0"></div>

    <aside id="agent-drawer" class="fixed top-0 right-0 bottom-0 w-80 sm:w-96 bg-white shadow-2xl z-50 transform translate-x-full transition-transform duration-300 ease-in-out flex flex-col border-l border-slate-200">
        <!-- 抽屉头部 -->
        <div class="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
            <div class="flex items-center space-x-2">
                <div class="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs">
                    <i class="fa-solid fa-brain"></i>
                </div>
                <div>
                    <h2 class="text-sm font-bold text-slate-800">Agent 内部决策监控</h2>
                    <p class="text-[10px] text-slate-500">实时状态机流转与执行轨迹</p>
                </div>
            </div>
            <button onclick="toggleDrawer()" class="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 flex items-center justify-center transition">
                <i class="fa-solid fa-xmark text-sm"></i>
            </button>
        </div>

        <!-- 抽屉内容区 -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            <!-- 1. 当前意图 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                <div class="text-[11px] text-slate-500 mb-1 flex items-center justify-between">
                    <span>当前意图 (Intent)</span>
                    <span id="intent-code" class="text-[10px] font-mono text-slate-400">WAITING</span>
                </div>
                <div id="badge-intent" class="inline-block px-2.5 py-1 rounded-md text-xs font-bold bg-slate-200 text-slate-700">
                    等待对话...
                </div>
            </div>

            <!-- 2. 情绪监控表盘 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                <div class="flex justify-between items-center mb-1.5">
                    <span class="text-[11px] text-slate-500">客户愤怒指数 (Sentiment)</span>
                    <span id="sentiment-text" class="text-xs font-bold text-slate-700">1 / 5 (平静)</span>
                </div>
                <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div id="sentiment-bar" class="bg-emerald-500 h-full w-[20%] transition-all duration-300"></div>
                </div>
                <div class="text-[10px] text-slate-400 mt-1">≥4 分将自动生成工单并转接人工主管</div>
            </div>

            <!-- 3. 已收集槽位 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                <div class="text-[11px] text-slate-500 mb-2">已收集槽位 (Slots)</div>
                <div id="slots-container" class="space-y-1.5">
                    <div class="text-slate-400 italic">暂无槽位数据</div>
                </div>
            </div>

            <!-- 4. 工单记录 -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                <div class="text-[11px] text-slate-500 mb-2 flex items-center justify-between">
                    <span>转人工工单 (Tickets)</span>
                    <span id="ticket-count" class="text-[10px] bg-red-100 text-red-600 font-bold px-1.5 py-0.5 rounded">0</span>
                </div>
                <div id="tickets-container" class="space-y-2">
                    <div class="text-slate-400 italic">当前未产生转接工单</div>
                </div>
            </div>

            <!-- 5. Agent 思考过程 (Thought Trace) -->
            <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                <div class="text-[11px] text-slate-500 mb-1.5 flex items-center">
                    <i class="fa-solid fa-lightbulb text-amber-500 mr-1 text-xs"></i>
                    <span>决策思考过程 (Thought)</span>
                </div>
                <div id="thought-trace" class="text-[11px] text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed min-h-[50px]">
                    等待系统处理...
                </div>
            </div>
        </div>

        <div class="p-3 border-t border-slate-200 bg-slate-50 text-center">
            <span class="text-[11px] text-slate-400">点击页面空白处可随时收起抽屉</span>
        </div>
    </aside>

    <script>
        const sessionId = "web_user_" + Math.random().toString(36).substring(2, 8);
        let drawerOpen = false;

        // 页面初始化
        window.onload = async () => {
            const res = await fetch("/api/info");
            const data = await res.json();
            document.getElementById("engine-name").innerText = data.provider;
        };

        function toggleDrawer() {
            drawerOpen = !drawerOpen;
            const drawer = document.getElementById("agent-drawer");
            const backdrop = document.getElementById("drawer-backdrop");

            if (drawerOpen) {
                backdrop.classList.remove("hidden");
                setTimeout(() => backdrop.classList.remove("opacity-0"), 10);
                drawer.classList.remove("translate-x-full");
                drawer.classList.add("translate-x-0");
            } else {
                backdrop.classList.add("opacity-0");
                drawer.classList.remove("translate-x-0");
                drawer.classList.add("translate-x-full");
                setTimeout(() => backdrop.classList.add("hidden"), 300);
            }
        }

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
                appendMessage("assistant", data.reply, data.state);
                updateDashboard(data.state);
            } catch (err) {
                appendMessage("assistant", "⚠️ 连接服务异常，请稍后重试。");
            } finally {
                sendBtn.disabled = false;
                sendBtn.innerHTML = `<i class="fa-solid fa-paper-plane text-xs"></i>`;
            }
        }

        function appendMessage(role, content, state) {
            const container = document.getElementById("chat-messages");
            const div = document.createElement("div");
            div.className = "flex items-start space-x-3 " + (role === "user" ? "flex-row-reverse space-x-reverse" : "");

            const avatar = role === "user"
                ? `<div class="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs flex-shrink-0 shadow-sm mt-0.5"><i class="fa-solid fa-user"></i></div>`
                : `<div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs flex-shrink-0 shadow-sm mt-0.5"><i class="fa-solid fa-headset"></i></div>`;

            const bubbleClass = role === "user"
                ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm shadow-sm"
                : "bg-white text-slate-800 rounded-2xl rounded-tl-sm border border-slate-200/90 shadow-sm";

            let metaTag = "";
            if (role === "assistant" && state) {
                const slots = Object.keys(state.slots || {}).map(k => `${k}:${state.slots[k]}`).join(" ");
                metaTag = `
                    <div class="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                        <span class="flex items-center">
                            <i class="fa-solid fa-tag text-[10px] mr-1 text-slate-300"></i>意图: ${state.current_intent}
                            ${slots ? `<span class="ml-2 font-mono bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200/60">${slots}</span>` : ""}
                        </span>
                        <button onclick="toggleDrawer()" class="text-blue-500 hover:text-blue-700 text-[10px] transition">查看思考轨迹 →</button>
                    </div>
                `;
            }

            div.innerHTML = `
                ${avatar}
                <div class="${bubbleClass} p-4 max-w-lg text-sm leading-relaxed whitespace-pre-wrap">${content}${metaTag}</div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function updateDashboard(state) {
            // 1. 意图更新
            const intentBadge = document.getElementById("badge-intent");
            const intentCode = document.getElementById("intent-code");
            intentBadge.innerText = state.current_intent;
            intentCode.innerText = state.current_intent;
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
            const slotBadge = document.getElementById("drawer-slot-badge");
            const slots = state.slots || {};
            const slotKeys = Object.keys(slots);
            if (slotKeys.length === 0) {
                slotsContainer.innerHTML = `<div class="text-slate-400 italic">暂无槽位数据</div>`;
                slotBadge.classList.add("hidden");
            } else {
                slotsContainer.innerHTML = Object.entries(slots).map(([k, v]) => `
                    <div class="flex justify-between bg-white px-2.5 py-1.5 rounded-lg border border-slate-200">
                        <span class="text-slate-500">${k}:</span>
                        <span class="font-bold text-slate-800 font-mono">${v}</span>
                    </div>
                `).join("");
                slotBadge.classList.remove("hidden");
            }

            // 4. 工单更新
            const ticketContainer = document.getElementById("tickets-container");
            const tickets = state.tickets || [];
            document.getElementById("ticket-count").innerText = tickets.length;
            if (tickets.length > 0) {
                ticketContainer.innerHTML = tickets.map(t => `
                    <div class="bg-red-50 p-2.5 rounded-lg border border-red-200 text-red-800">
                        <div class="font-bold flex justify-between">
                            <span>${t.ticket_id}</span>
                            <span class="text-[10px] bg-red-200 px-1 rounded">${t.status}</span>
                        </div>
                        <div class="text-[10px] text-slate-500 mt-1">${t.reason}</div>
                    </div>
                `).join("");
            } else {
                ticketContainer.innerHTML = `<div class="text-slate-400 italic">当前未产生转接工单</div>`;
            }

            // 5. 思考过程更新
            const thoughtTrace = document.getElementById("thought-trace");
            if (state.last_thought) {
                thoughtTrace.innerText = state.last_thought;
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
