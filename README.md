# Viggy
Self-hosted moderation bot
<img src="https://i.imgur.com/mCpZPcv.png" alt="viggy mascot, made by @catneptune on github" width=200, height=200>
### Features
- Moderation tracking
- Tempban support
- Event logs
- Quickmod (react with 💥 to a message)
- Moderation marking (the ability to mark moderations as active or inactive)

### Setup
Begin by cloning the repository
```
git clone https://github.com/0vf/viggy
cd viggy
```
Install required dependencies
```
pip install -r requirements.txt
```
Configure the bot token (configuration guide below), and start the bot
```
python ./main.py
```

### Configuration guide
The configuration is just a simple toml file, all you have to do is copy `config.toml.sample` into `config.toml`, and then add the bot token to the `token` key under the `[discord]` table.

Example:
```toml
[discord]
token = "MjEzMjkwMTY3NDA5MTgwNjcy.8JFhmK.nMMfj8laiN6kknmbPIEtrfr4nk99_4rEDxles"
```
(token for demonstration purposes, it isn't real)