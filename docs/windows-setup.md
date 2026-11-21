# Windows + VS Code setup for IEEE Poker Bot Hackathon

This is the **organizers' recommended WSL/Ubuntu route**, adapted for Windows and VS Code. If you have **Visual Studio** (full IDE) rather than **Visual Studio Code**, install VS Code for this workflow: https://code.visualstudio.com/

## 1. Install Ubuntu under WSL (Windows PowerShell as administrator)

First check `wsl --status`. If Ubuntu is not installed, run:

```powershell
wsl --install -d Ubuntu
```

Restart Windows if asked; open Ubuntu from Start and create a Linux username/password. If already installed, open your existing Ubuntu instead of reinstalling.

Reference: https://learn.microsoft.com/en-us/windows/wsl/install

## 2. Ubuntu prerequisites (Ubuntu terminal, not PowerShell)

```bash
sudo apt update
sudo apt install -y build-essential git make curl ca-certificates
```

## 3. Install uv, then Python 3.10

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
uv python install 3.10
```

Python 3.10 matters: the official kit pins `eval7==0.1.7` and tells participants not to use 3.11+.

Reference: https://docs.astral.sh/uv/getting-started/installation/

## 4. Clone inside Ubuntu, not under C:\\

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/Wriskyzeus/poker-bot-hackathon.git
cd poker-bot-hackathon
```

Use the Ubuntu home filesystem for better WSL/Linux performance.

## 5. Create and activate the exact Python environment

```bash
uv venv --seed -p 3.10 .venv
source .venv/bin/activate
python --version
make install
```

`python --version` should report 3.10.x. Reactivate `source .venv/bin/activate` when starting a new terminal in the project.

## 6. First match and validator

```bash
python3 play.py my_bots/uo_monte bots/caller --seed 7
make validate BOT=my_bots/uo_monte
```

Optional detailed hand log:

```bash
python3 play.py my_bots/uo_monte bots/caller --seed 7 --show
```

**Important:** UO-Monte's submission identifier is `uo_monte`; use that exact value in the submission form and keep the matching folder.

## 7. Open in VS Code

Install the **WSL** extension from Microsoft in Windows VS Code, then run `code .` from your Ubuntu project directory. Install the Microsoft Python extension in the WSL context, and select `.venv/bin/python` as the interpreter. Run all Python commands from the integrated **Ubuntu** terminal.

Reference: https://code.visualstudio.com/docs/remote/wsl

## 8. Optional: Docker sandbox (after basic commands succeed)

If you have time, install Docker Desktop for Windows, enable its WSL 2 backend and Ubuntu integration, then:

```bash
docker --version
make sandbox
python3 play.py my_bots/uo_monte bots/caller --docker
```

Docker provides the closest test to the competition's **0.5 CPU core, 768 MB, no-network** runtime. The normal validator is usable without Docker.

Reference: https://docs.docker.com/desktop/features/wsl/

## Troubleshooting

- `uv: command not found`: run `export PATH="$HOME/.local/bin:$PATH"` or reopen Ubuntu.
- `code: command not found`: install Windows VS Code and its WSL extension; open the folder via the WSL connection from within VS Code.
- `python3` is not 3.10: activate `.venv` before running `make install`.
- `make: command not found`: run the Ubuntu prerequisites install again.
- `eval7` compiler errors: confirm Ubuntu build tools and Python 3.10, then share the actual error output rather than changing package versions.
- Docker problems: skip Docker temporarily; prioritize a successful local match and `make validate`.

No poker engine code should be modified to resolve local installation problems.
