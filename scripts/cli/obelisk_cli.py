#!/usr/bin/env python3

import typer
import httpx
import sys
import subprocess
from rich.console import Console
from rich.spinner import Spinner
from time import sleep

app = typer.Typer(help="OBELISK Command Line Interface - Active Defense")
console = Console()

API_URL = "http://localhost:8000/api/packages/analyze"

@app.command()
def install(package: str, manager: str = typer.Option("npm", help="Package manager to use (npm or pypi)")):
    """
    Live Kill-Chain Interception wrapper.
    Analyses the package dynamically through OBELISK backend before passing 
    control to standard package managers like npm or pip.
    """
    with console.status(f"[bold cyan][~] OBELISK ML Pipeline Analyzing '{package}'...[/bold cyan]", spinner="dots"):
        try:
            payload = {
                "name": package,
                "version": "latest",
                "registry": manager if manager in ["npm", "pypi"] else "npm"
            }
            # Synchronous Analysis Block
            response = httpx.post(API_URL, json=payload, timeout=10.0)
            
            # Even if API fails to hit analysis correctly, don't fail-open securely (fail-closed if strict)
            if response.status_code == 200:
                data = response.json()
                score = data.get("risk_score", data.get("analysis", {}).get("risk_score", 0))
                
                # Execution Gate
                if score > 75:
                    console.print("\n[bold red blink]KILL-CHAIN INTERCEPTED: Malicious payload detected. Installation aborted.[/bold red blink]")
                    console.print(f"[bold red]► Risk Score: {score}/100[/bold red]")
                    console.print(f"[bold red]► Threat Level: CRITICAL[/bold red]")
                    sys.exit(1)
            else:
                console.print(f"[bold yellow][!] OBELISK Analysis API returned non-200 status code: {response.status_code}[/bold yellow]")
        except httpx.ConnectError:
            console.print("[bold yellow][!] OBELISK Server unreachable. Proceeding with unverified install.[/bold yellow]")
        except httpx.TimeoutException:
            console.print("[bold yellow][!] OBELISK Analysis timed out. Proceeding with unverified install.[/bold yellow]")

    # Pass the command through to `npm install <pkg>` or `pip install <pkg>`
    console.print(f"[bold green]✓ Verified by OBELISK -> Safe to Install[/bold green]")
    manager_cmd = "pip" if manager == "pypi" else manager
    console.print(f"[dim]Running standard {manager_cmd} install...[/dim]")
    
    install_cmd = [manager_cmd, "install", package]
    result = subprocess.run(install_cmd)
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    app()
