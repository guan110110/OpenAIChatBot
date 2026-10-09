"""
CLI Interactive Chat for OpenSupport.
终端交互式客户服务 Agent 体验脚本。
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opensupport.agent import CustomerServiceAgent
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    agent = CustomerServiceAgent()
    console.print(Panel(
        f"[bold cyan]OpenSupport 智能客服 Agent 交互终端[/bold cyan]\n"
        f"当前运行引擎: [bold green]{agent.llm_cfg['provider']}[/bold green]\n"
        f"输入 [yellow]'exit'[/yellow] 或 [yellow]'quit'[/yellow] 退出交互。",
        border_style="cyan"
    ))

    session_id = "cli_session"
    while True:
        try:
            user_input = console.input("[bold blue]用户 > [/bold blue]").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[dim]已结束会话。再见！[/dim]")
                break

            reply, session = agent.process_message(user_input, session_id=session_id)
            
            # 打印智能体决策元信息
            console.print(f"[dim]⚡ [意图: {session.current_intent} | 情绪评分: {session.sentiment_score}/5 | 槽位: {session.slots}][/dim]")
            console.print(Panel(reply, title="🤖 [bold green]客服小智[/bold green]", border_style="green"))

        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    main()
