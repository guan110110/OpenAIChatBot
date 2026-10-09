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
    <title>OpenSupport - 经典在线客服</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        .chat-scroll::-webkit-scrollbar { width: 5px; }
        .chat-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 9999px; }
        .chat-scroll::-webkit-scrollbar-thumb:hover { background-color: #94a3b8; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="bg-slate-200/90 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:16px_16px] min-h-screen flex items-center justify-center p-0 sm:p-4 font-sans text-slate-800 antialiased overflow-hidden">

    <!-- 经典独立客服聊天窗体 (Classic Window Card) -->
    <div id="chat-window" class="w-full sm:max-w-[480px] h-screen sm:h-[730px] sm:max-h-[96vh] bg-white sm:rounded-3xl shadow-2xl border border-slate-300/80 flex flex-col overflow-hidden relative transition-all duration-300">

        <!-- 经典窗口顶栏 (Window Header) -->
        <header class="bg-white/95 backdrop-blur border-b border-slate-200 px-4 py-3 flex items-center justify-between flex-shrink-0 z-10">
            <div class="flex items-center space-x-2.5">
                <!-- Mac风格装饰窗口红黄绿圆点 (仅桌面端显示) -->
                <div class="hidden sm:flex items-center space-x-1.5 mr-1">
                    <span class="w-2.5 h-2.5 rounded-full bg-rose-400 inline-block"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
                </div>

                <!-- 客服头像与在线状态 -->
                <div class="relative">
                    <div class="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-xs shadow-sm">
                        <i class="fa-solid fa-headset text-sm"></i>
                    </div>
                    <span class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white animate-pulse"></span>
                </div>

                <!-- 客服名称与信息 -->
                <div>
                    <div class="flex items-center space-x-1.5">
                        <h1 class="font-bold text-slate-800 text-sm tracking-tight">官方旗舰店 · 在线客服</h1>
                    </div>
                    <p class="text-[11px] text-slate-400 flex items-center">
                        <span class="text-emerald-600 font-medium">● 在线</span>
                        <span class="mx-1">•</span>
                        <span>工号: 8016 (小智)</span>
                    </p>
                </div>
            </div>

            <!-- 右侧窗口操作按钮栏 -->
            <div class="flex items-center space-x-1">
                <!-- 切换宽屏/小窗模式 -->
                <button onclick="toggleWindowMode()" id="btn-toggle-mode" title="切换经典小窗 / 宽屏模式"
                        class="text-xs text-slate-500 hover:text-slate-800 hover:bg-slate-100 p-1.5 rounded-lg border border-transparent hover:border-slate-200 transition">
                    <i id="expand-icon" class="fa-solid fa-expand text-xs"></i>
                </button>

                <!-- 监控抽屉按钮 -->
                <button onclick="toggleDrawer()" title="查看 Agent 内部决策看板"
                        class="text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-2.5 py-1.5 rounded-lg border border-blue-200 flex items-center transition font-medium">
                    <i class="fa-solid fa-brain mr-1"></i>
                    <span>监控</span>
                    <span id="drawer-slot-badge" class="hidden ml-1 w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                </button>

                <!-- 重置对话 -->
                <button onclick="resetSession()" title="清空并重启对话"
                        class="text-xs text-slate-500 hover:text-slate-800 hover:bg-slate-100 p-1.5 rounded-lg border border-transparent hover:border-slate-200 transition">
                    <i class="fa-solid fa-rotate-right text-xs"></i>
                </button>
            </div>
        </header>

        <!-- 经典服务保障公告条 -->
        <div class="bg-blue-50/80 border-b border-blue-100/70 px-4 py-1.5 text-[11px] text-blue-700 flex items-center justify-between flex-shrink-0">
            <span class="flex items-center truncate">
                <i class="fa-solid fa-shield-halved text-blue-500 mr-1.5 text-xs"></i>
                <span>官方正品保障 • 7天无理由退换 • AI 智能服务中</span>
            </span>
            <span id="engine-name" class="font-mono text-[10px] text-blue-600 bg-blue-100/80 px-1.5 py-0.5 rounded flex-shrink-0 ml-2">加载中...</span>
        </div>

        <!-- 聊天消息流区域 (Classic Bubble Canvas) -->
        <div id="chat-messages" class="flex-1 bg-slate-50 overflow-y-auto px-3.5 py-4 chat-scroll space-y-4">
            <!-- 时间分割线 -->
            <div class="text-center my-1">
                <span class="text-[10px] bg-slate-200/70 text-slate-500 px-2.5 py-0.5 rounded-full font-sans">今天</span>
            </div>

            <!-- 客服欢迎消息 -->
            <div class="flex items-start space-x-2.5">
                <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs flex-shrink-0 shadow-sm mt-0.5">
                    <i class="fa-solid fa-headset text-xs"></i>
                </div>
                <div class="bg-white text-slate-800 p-3.5 rounded-2xl rounded-tl-xs max-w-[85%] text-xs sm:text-sm leading-relaxed border border-slate-200/80 shadow-xs">
                    <p class="font-medium text-slate-900 mb-1.5">您好！我是官方智能客服助理 😊</p>
                    <p class="text-slate-600 mb-2.5">已为您开启 7×24 小时极速答疑，请问有什么可以帮您？</p>
                    <div class="space-y-1.5 text-xs text-slate-600 bg-slate-50/80 p-2.5 rounded-xl border border-slate-100">
                        <div class="flex items-center space-x-1.5">
                            <span>📦</span><span><b>订单物流</b>：查询包裹位置、承运轨迹</span>
                        </div>
                        <div class="flex items-center space-x-1.5">
                            <span>🔄</span><span><b>退换业务</b>：在线极速申请退款、退货</span>
                        </div>
                        <div class="flex items-center space-x-1.5">
                            <span>📘</span><span><b>售后咨询</b>：质保期限、运费险条款</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 经典快捷问答横向滑动胶囊栏 -->
        <div class="bg-slate-50 border-t border-slate-200/70 px-3 py-2 flex items-center space-x-1.5 overflow-x-auto no-scrollbar flex-shrink-0">
            <button onclick="quickSend('帮我查下订单 ORD1001 的物流')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 text-[11px] px-2.5 py-1 rounded-full border border-slate-200 shadow-xs transition">
                📦 查单号 ORD1001
            </button>
            <button onclick="quickSend('我要申请退款，订单号是 ORD1002')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 text-[11px] px-2.5 py-1 rounded-full border border-slate-200 shadow-xs transition">
                🔄 申请退款 ORD1002
            </button>
            <button onclick="quickSend('你们支持7天无理由退货吗？')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 text-[11px] px-2.5 py-1 rounded-full border border-slate-200 shadow-xs transition">
                📘 7天无理由退货
            </button>
            <button onclick="quickSend('帮我查下我的快递到哪了')" class="flex-shrink-0 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 text-slate-600 text-[11px] px-2.5 py-1 rounded-full border border-slate-200 shadow-xs transition">
                🔍 模糊查件
            </button>
            <button onclick="quickSend('服务太差了，再不解决我直接打12315投诉！')" class="flex-shrink-0 bg-white hover:bg-red-50 hover:text-red-600 hover:border-red-300 text-slate-600 text-[11px] px-2.5 py-1 rounded-full border border-slate-200 shadow-xs transition">
                🚨 投诉转人工
            </button>
        </div>

        <!-- 经典底部输入面板 (Classic Input Area) -->
        <div class="bg-white border-t border-slate-200 p-3 flex-shrink-0">
            <!-- 经典迷你工具栏 -->
            <div class="flex items-center justify-between text-slate-400 text-xs mb-2 px-1">
                <div class="flex items-center space-x-3">
                    <button onclick="insertEmoji('😊')" title="表情" class="hover:text-amber-500 transition"><i class="fa-regular fa-face-smile"></i></button>
                    <button onclick="insertEmoji('👍')" title="点赞" class="hover:text-blue-500 transition"><i class="fa-regular fa-thumbs-up"></i></button>
                    <button onclick="insertEmoji('❓')" title="疑问" class="hover:text-indigo-500 transition"><i class="fa-solid fa-circle-question"></i></button>
                    <span class="text-slate-200">|</span>
                    <button onclick="insertText('ORD1001')" class="text-[10px] text-slate-500 hover:text-blue-600 font-mono transition">#ORD1001</button>
                    <button onclick="insertText('ORD1002')" class="text-[10px] text-slate-500 hover:text-blue-600 font-mono transition">#ORD1002</button>
                </div>
                <span class="text-[10px] text-slate-400 hidden sm:inline">Enter 发送</span>
            </div>

            <!-- 输入表单 -->
            <form id="chat-form" onsubmit="sendMessage(event)" class="flex items-center space-x-2">
                <input type="text" id="user-input" placeholder="输入您的问题，如“查下订单 ORD1001”..." autocomplete="off"
                       class="flex-1 bg-slate-100/90 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-slate-800 placeholder-slate-400 outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition">
                <button type="submit" id="send-btn"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center space-x-1.5 shadow-sm shadow-blue-500/20 transition disabled:opacity-50 flex-shrink-0">
                    <span>发送</span>
                    <i class="fa-solid fa-paper-plane text-xs"></i>
                </button>
            </form>
        </div>

        <!-- 右侧滑出式 Agent 监控抽屉 (Collapsible Inspector Drawer) -->
        <div id="drawer-backdrop" onclick="toggleDrawer()" class="absolute inset-0 bg-slate-900/30 backdrop-blur-xs z-20 hidden transition-opacity opacity-0"></div>

        <aside id="agent-drawer" class="absolute top-0 right-0 bottom-0 w-72 sm:w-80 bg-white shadow-2xl z-30 transform translate-x-full transition-transform duration-300 ease-in-out flex flex-col border-l border-slate-200">
            <!-- 抽屉头部 -->
            <div class="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
                <div class="flex items-center space-x-2">
                    <div class="w-6 h-6 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs">
                        <i class="fa-solid fa-brain"></i>
                    </div>
                    <div>
                        <h2 class="text-xs font-bold text-slate-800">Agent 内部决策监控</h2>
                        <p class="text-[9px] text-slate-500">状态机与槽位实时追踪</p>
                    </div>
                </div>
                <button onclick="toggleDrawer()" class="w-6 h-6 rounded text-slate-400 hover:text-slate-600 flex items-center justify-center transition">
                    <i class="fa-solid fa-xmark text-sm"></i>
                </button>
            </div>

            <!-- 抽屉内容区 -->
            <div class="flex-1 overflow-y-auto p-3.5 space-y-3.5 text-xs">
                <!-- 1. 当前意图 -->
                <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                    <div class="text-[10px] text-slate-500 mb-1 flex items-center justify-between">
                        <span>当前意图 (Intent)</span>
                        <span id="intent-code" class="text-[9px] font-mono text-slate-400">WAITING</span>
                    </div>
                    <div id="badge-intent" class="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-slate-200 text-slate-700">
                        等待对话...
                    </div>
                </div>

                <!-- 2. 情绪监控表盘 -->
                <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-[10px] text-slate-500">客户愤怒指数 (Sentiment)</span>
                        <span id="sentiment-text" class="text-[11px] font-bold text-slate-700">1 / 5 (平静)</span>
                    </div>
                    <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                        <div id="sentiment-bar" class="bg-emerald-500 h-full w-[20%] transition-all duration-300"></div>
                    </div>
                    <div class="text-[9px] text-slate-400 mt-1">≥4 分将自动生成工单转接人工</div>
                </div>

                <!-- 3. 已收集槽位 -->
                <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                    <div class="text-[10px] text-slate-500 mb-1.5">已收集槽位 (Slots)</div>
                    <div id="slots-container" class="space-y-1">
                        <div class="text-slate-400 italic text-[11px]">暂无槽位数据</div>
                    </div>
                </div>

                <!-- 4. 工单记录 -->
                <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                    <div class="text-[10px] text-slate-500 mb-1.5 flex items-center justify-between">
                        <span>转人工工单 (Tickets)</span>
                        <span id="ticket-count" class="text-[9px] bg-red-100 text-red-600 font-bold px-1.5 py-0.5 rounded">0</span>
                    </div>
                    <div id="tickets-container" class="space-y-1.5">
                        <div class="text-slate-400 italic text-[11px]">当前未产生工单</div>
                    </div>
                </div>

                <!-- 5. 思考过程 -->
                <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/80">
                    <div class="text-[10px] text-slate-500 mb-1 flex items-center">
                        <i class="fa-solid fa-lightbulb text-amber-500 mr-1 text-[10px]"></i>
                        <span>思考过程 (Thought)</span>
                    </div>
                    <div id="thought-trace" class="text-[11px] text-slate-600 bg-white p-2 rounded border border-slate-200 leading-relaxed min-h-[40px]">
                        等待交互...
                    </div>
                </div>
            </div>
        </aside>

    </div>

    <script>
        const sessionId = "web_user_" + Math.random().toString(36).substring(2, 8);
        let drawerOpen = false;
        let isWideMode = false;

        // 页面初始化
        window.onload = async () => {
            const res = await fetch("/api/info");
            const data = await res.json();
            document.getElementById("engine-name").innerText = data.provider;
        };

        // 切换经典独立小窗与宽屏模式
        function toggleWindowMode() {
            isWideMode = !isWideMode;
            const win = document.getElementById("chat-window");
            const icon = document.getElementById("expand-icon");
            if (isWideMode) {
                win.classList.remove("sm:max-w-[480px]", "sm:h-[730px]", "sm:rounded-3xl");
                win.classList.add("sm:max-w-4xl", "sm:h-[860px]", "sm:rounded-2xl");
                icon.className = "fa-solid fa-compress text-xs";
            } else {
                win.classList.remove("sm:max-w-4xl", "sm:h-[860px]", "sm:rounded-2xl");
                win.classList.add("sm:max-w-[480px]", "sm:h-[730px]", "sm:rounded-3xl");
                icon.className = "fa-solid fa-expand text-xs";
            }
        }

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

        function insertEmoji(emoji) {
            const input = document.getElementById("user-input");
            input.value += emoji;
            input.focus();
        }

        function insertText(text) {
            const input = document.getElementById("user-input");
            input.value = "查订单 " + text;
            input.focus();
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
                sendBtn.innerHTML = `<span>发送</span><i class="fa-solid fa-paper-plane text-xs"></i>`;
            }
        }

        function appendMessage(role, content, state) {
            const container = document.getElementById("chat-messages");
            const div = document.createElement("div");
            div.className = "flex items-start space-x-2.5 " + (role === "user" ? "flex-row-reverse space-x-reverse" : "");

            const avatar = role === "user"
                ? `<div class="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs flex-shrink-0 shadow-sm mt-0.5"><i class="fa-solid fa-user"></i></div>`
                : `<div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs flex-shrink-0 shadow-sm mt-0.5"><i class="fa-solid fa-headset text-xs"></i></div>`;

            const bubbleClass = role === "user"
                ? "bg-blue-600 text-white rounded-2xl rounded-tr-xs shadow-xs"
                : "bg-white text-slate-800 rounded-2xl rounded-tl-xs border border-slate-200/80 shadow-xs";

            let metaTag = "";
            if (role === "assistant" && state) {
                const slots = Object.keys(state.slots || {}).map(k => `${k}:${state.slots[k]}`).join(" ");
                metaTag = `
                    <div class="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                        <span class="flex items-center">
                            <span class="w-1.5 h-1.5 rounded-full bg-blue-500 mr-1"></span>意图: ${state.current_intent}
                            ${slots ? `<span class="ml-1.5 font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-600">${slots}</span>` : ""}
                        </span>
                        <button onclick="toggleDrawer()" class="text-blue-500 hover:text-blue-700 transition">详情 →</button>
                    </div>
                `;
            }

            div.innerHTML = `
                ${avatar}
                <div class="${bubbleClass} p-3 sm:p-3.5 max-w-[85%] text-xs sm:text-sm leading-relaxed whitespace-pre-wrap">${content}${metaTag}</div>
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
            intentBadge.className = "inline-block px-2 py-0.5 rounded text-[11px] font-bold " + 
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
                slotsContainer.innerHTML = `<div class="text-slate-400 italic text-[11px]">暂无槽位数据</div>`;
                slotBadge.classList.add("hidden");
            } else {
                slotsContainer.innerHTML = Object.entries(slots).map(([k, v]) => `
                    <div class="flex justify-between bg-white px-2 py-1 rounded border border-slate-200">
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
                    <div class="bg-red-50 p-2 rounded border border-red-200 text-red-800 text-[11px]">
                        <div class="font-bold flex justify-between">
                            <span>${t.ticket_id}</span>
                            <span class="text-[9px] bg-red-200 px-1 rounded">${t.status}</span>
                        </div>
                        <div class="text-[10px] text-slate-500 mt-0.5">${t.reason}</div>
                    </div>
                `).join("");
            } else {
                ticketContainer.innerHTML = `<div class="text-slate-400 italic text-[11px]">当前未产生工单</div>`;
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
