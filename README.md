## Accuse Bot

Discord bot for managing accusations with means to vote for an outcome. Users are moved up or down in the role hierarchy when punished or pardoned respectively. Accusations and any sentences given are serialized and are managed with coroutines to perform actions across their lifetime.

### Supported Commands
```
/accuse
/roles
```

### Deployment

```sh
sudo apt update
sudo apt install git tmux python3 python3-dev python3-venv
mkdir bot && cd bot
git clone https://github.com/jiejasonliu/accuse-bot.git
cd accuse-bot
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# note: update .env before running the bot

# run the command detached from the ephermal shell if ssh-ing into the host
# to detach: CTRL + B then D 
tmux
python3 main.py 
```