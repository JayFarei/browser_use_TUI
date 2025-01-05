from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from langchain.callbacks.base import BaseCallbackHandler

console = Console()

class TokenCostCallbackHandler(BaseCallbackHandler):
    def __init__(self, cost_tracker):
        self.cost_tracker = cost_tracker
        
    def on_llm_end(self, response, **kwargs):
        if hasattr(response, 'llm_output') and response.llm_output:
            if 'token_usage' in response.llm_output:
                self.cost_tracker.update(response.llm_output['token_usage'])

class CostTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.total_cost = 0
        self.start_time = datetime.now()
        # GPT-4o pricing per 1M tokens
        self.INPUT_PRICE_PER_M = 5.00  # $5 per 1M input tokens
        self.OUTPUT_PRICE_PER_M = 15.00  # $15 per 1M output tokens
        
    def update(self, tokens_info):
        if isinstance(tokens_info, dict):
            # Handle detailed token information
            prompt_tokens = tokens_info.get('prompt_tokens', 0)
            completion_tokens = tokens_info.get('completion_tokens', 0)
            self.input_tokens += prompt_tokens
            self.output_tokens += completion_tokens
            self.total_tokens += prompt_tokens + completion_tokens
            
            # Calculate costs
            input_cost = (prompt_tokens / 1_000_000) * self.INPUT_PRICE_PER_M
            output_cost = (completion_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_M
            self.total_cost += input_cost + output_cost
        else:
            # Fallback for when we only have total tokens
            self.total_tokens += tokens_info
            # Assume worst case (output pricing) when we don't have the breakdown
            self.total_cost += (tokens_info / 1_000_000) * self.OUTPUT_PRICE_PER_M
        
    def get_summary(self):
        duration = datetime.now() - self.start_time
        return {
            "duration": str(duration).split('.')[0],
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": f"${self.total_cost:.4f}"
        }

async def get_user_task() -> str:
    console.print(Panel.fit(
        Text("🌐 Browser Agent", style="bold blue"),
        subtitle="Your AI-powered browser assistant"
    ))
    return Prompt.ask("\n[bold cyan]What would you like the browser to do?[/bold cyan]")

def format_results(history, cost_tracker):
    if not history:
        return "No results available"
    
    # Get final result using the proper method
    final_result = history.final_result()
    if final_result and final_result.startswith("Result:"):
        final_result = final_result[7:].strip()  # Remove "Result:" prefix
    
    # Show the final result prominently first
    console.print("\n")
    console.print(Panel(
        Text(final_result, style="bold green", justify="center"),
        title="🎯 Result",
        border_style="green",
        padding=(1, 2)
    ))
    
    # Add a divider
    console.print("\n" + "─" * console.width + "\n")
    
    # Create steps table for the process
    steps_table = Table(title="🔍 Process Details", show_header=True, header_style="bold magenta")
    steps_table.add_column("Step", style="dim", width=6)
    steps_table.add_column("Action", style="cyan")
    
    # Use proper history methods to get actions and results
    for i, (action, result) in enumerate(zip(history.action_names(), history.action_results()), 1):
        if result.error:
            icon = "❌"
            content = f"{action}: {result.error}"
        else:
            icon = "✅"
            content = f"{action}: {result.extracted_content if result.extracted_content else ''}"
        steps_table.add_row(f"{i}", f"{icon} {content}")
    
    # Add visited URLs if any
    urls = history.urls()
    if urls:
        console.print("\n[bold blue]📍 Visited URLs:[/bold blue]")
        for url in urls:
            console.print(f"  • {url}")
    
    # Create cost summary
    stats = cost_tracker.get_summary()
    stats_table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        collapse_padding=True
    )
    stats_table.add_column(justify="right", style="bold")
    stats_table.add_column(justify="left")
    stats_table.add_row("⏱️ Duration:", stats["duration"])
    stats_table.add_row("🔤 Input Tokens:", str(stats["input_tokens"]))
    stats_table.add_row("🔤 Output Tokens:", str(stats["output_tokens"]))
    stats_table.add_row("🔤 Total Tokens:", str(stats["total_tokens"]))
    stats_table.add_row("💰 Total Cost:", stats["total_cost"])
    
    console.print("\n")
    console.print(steps_table)
    console.print("\n")
    console.print(Panel(
        stats_table,
        title="📊 Usage Statistics",
        border_style="yellow",
        expand=True,
        padding=(1, 1)
    ))

async def main():
    try:
        cost_tracker = CostTracker()
        
        llm = ChatOpenAI(
            model="gpt-4o",
            callbacks=[TokenCostCallbackHandler(cost_tracker)]
        )
        
        task = await get_user_task()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False
        ) as progress:
            progress_task = progress.add_task("Browser agent is working on your task...", total=None)
            agent = Agent(task=task, llm=llm)
            result = await agent.run()
            progress.update(progress_task, completed=True)
            
        format_results(result, cost_tracker)
        
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
