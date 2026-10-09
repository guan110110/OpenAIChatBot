<div align="center">

# 🎧 OpenSupport

**通用、开箱即用的现代化智能客服 AI Agent 框架**  
*A Universal, Production-Ready Customer Service AI Agent Framework with Intent Routing, Slot Filling & Human Escalation.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/WebUI-FastAPI%20Native-009688.svg)](https://fastapi.tiangolo.com)
[![Free Model Ready](https://img.shields.io/badge/LLM-GLM--4--Flash%20(Free)%20%7C%20DeepSeek%20%7C%20Ollama%20%7C%20Mock-success.svg)](#-大模型支持与免费方案)

[English](#english-overview) | [简体中文](#-为什么设计-opensupport)

</div>

---

## 💡 为什么设计 OpenSupport？

许多开源的“AI 客服”项目往往只是一个简单的“Prompt 聊天套壳”，在真实业务中面临诸多痛点：
* ❌ **无法主动追问**：用户说“查下我的快递”，模型报错缺少单号，而不是主动询问“请问您的订单号是多少？”
* ❌ **缺少意图分流**：将常见政策答疑、业务办理（查单/退款）和客户投诉混在一起，容易产生幻觉或乱调工具。
* ❌ **缺乏情绪兜底**：遇到极度愤怒、扬言投诉消协的客户，仍然机械回复，导致客诉激化。

**OpenSupport 为解决真实业务而生。**  
它将 **意图路由分类**、**多轮状态机（槽位填充）**、**轻量 RAG 知识检索**、**真实业务工具链** 和 **情绪风控转人工** 完美整合，且**零重型中间件依赖**。

---

## ✨ 核心特性

- 🎯 **意图识别分流 (Intent Routing)**：精准将用户提问分发至 FAQ 问答、业务办理或人工转接。
- 🔄 **主动槽位填充 (Slot-Filling State Machine)**：若缺少订单号或关键信息，Agent 主动温和追问，直到参数补齐后再调用工具。
- 🛡️ **情绪监测与人工转接 (Human Escalation)**：动态计算用户愤怒值（1-5分）。遇到强烈投诉时自动安抚、生成结构化支持工单（Support Ticket）并切换转人工模式。
- 📚 **零依赖轻量 RAG**：内置词法与关键词加权检索器，开箱即可基于 `data/faq.json` 准确解答售后保障与政策。
- 📦 **完整业务工具链**：内置模拟订单中心（`ORD1001`、`ORD1002`、`ORD1003`），支持订单查询、物流轨迹追踪、退货申请与地址变更。
- 🖥️ **高颜值 Web 工作台**：左右分栏设计，左侧实时呈现 Agent 的内部思考轨迹（意图、愤怒表盘、槽位、工单），右侧提供仿真实时聊天。
- 🎁 **永久免费体验**：默认支持 **智谱 GLM-4-Flash（官方永久免费）**、**本地离线 Ollama**，甚至内置 **Mock 仿真引擎**，不填 Key 也能一秒跑通！

---

## 🏗️ 核心架构流转图

```mermaid
flowchart TD
    User([用户发送消息]) --> Guard[意图与情绪安全风控]
    
    subgraph Analysis [分析与路由]
        Guard --> Sentiment{情绪是否激动 (>=4分)?}
        Sentiment -- 是 / 明确要求人工 --> Escalate[生成加急工单 & 转接人工客服]
        Sentiment -- 否 (情绪正常) --> IntentRouter[意图分类器]
    end

    subgraph Business [业务处理与检索]
        IntentRouter -- 政策/常见问题 (FAQ) --> RAG[本地知识库检索]
        IntentRouter -- 查单/查快递/退货 --> SlotCheck{必要槽位 (order_id) 是否齐全?}
        SlotCheck -- 缺失 --> SlotAsk[向用户主动追问订单号]
        SlotCheck -- 齐全 --> ToolExec[执行业务工具: 查物流/办退款]
        IntentRouter -- 问候/闲聊 --> Chitchat[友好问候与引导]
    end

    RAG --> Response[整合输出专业客服回复]
    SlotAsk --> Response
    ToolExec --> Response
    Chitchat --> Response
    Escalate --> Response
    Response --> User
```

---

## 🚀 30 秒极速上手

### 1. 安装依赖

```bash
git clone https://github.com/guan110110/OpenSupport.git
cd OpenSupport

pip install -r requirements.txt
```

### 2. 启动本地 Web 工作台（最推荐）

```bash
python webui/server.py
```
> 程序将自动在浏览器中打开 **`http://127.0.0.1:8501`**，呈现完整的智能客服工作台！

### 3. 或者启动终端命令行交互

```bash
python examples/cli_chat.py
```

---

## 🧪 经典测试用例体验

您可以在 Web 工作台左侧点击快捷用例，或手动输入测试 Agent 的反应：

| 测试场景 | 用户输入示例 | Agent 智能反馈行为 |
| :--- | :--- | :--- |
| **1. 政策咨询 (FAQ)** | *"你们支持7天无理由退货吗？"* | 检索本地知识库，清晰准确回复 7 天无理由政策与运费责任规则。 |
| **2. 槽位主动追问** | *"帮我查下我的快递到哪了"* | 识别出缺少 `order_id`，主动追问：*“请问您的订单编号是多少呢？（如 ORD1001）”* |
| **3. 槽位补全与执行** | *"单号是 ORD1001"* | 自动填槽，调用工具查出商品为“无线头戴耳机”，返回顺丰物流轨迹。 |
| **4. 退款业务办理** | *"我要申请退款，订单号是 ORD1002"* | 调用退款工具，根据已签收状态生成退货寄件单与验货退款说明。 |
| **5. 情绪激化转人工** | *"你们这什么垃圾服务！再不退钱我直接打12315投诉你们！"* | 愤怒指数评分打出 5 分，触发共情安抚，自动生成加急工单转接人工主管。 |

---

## 🎁 大模型支持与免费方案

本框架采用**三级智能自适应机制**，配置零门槛：
1. **免费云端推荐**：在 `.env` 中配置 `ZHIPU_API_KEY`，直接使用官方**永久免费的 `glm-4-flash`** 模型；
2. **极高性价比云端**：在 `.env` 中配置 `DEEPSEEK_API_KEY`，使用强大的 `deepseek-chat`；
3. **本地离线免费**：电脑安装了 [Ollama](https://ollama.ai) 并运行模型（如 `ollama run qwen2.5:7b`），框架自动识别并直连；
4. **内置 Mock 仿真**：什么都不配置，直接启动即可完整演示全套业务流程！

---

<div id="english-overview"></div>

## 🌐 English Overview

**OpenSupport** is an enterprise-ready, open-source AI Customer Service Agent framework. It features intent routing, slot filling, local zero-dependency RAG, tool calling, and emotion-based human escalation. Works out of the box with zero external database dependencies.

---

## 📄 开源许可证

本项目采用 [MIT License](LICENSE) 协议，欢迎自由商用、集成与二次开发。
