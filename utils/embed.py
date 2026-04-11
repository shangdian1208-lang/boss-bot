import discord

def success(title, desc):
    return discord.Embed(
        title=f"✅ {title}",
        description=desc,
        color=0x57F287
    )

def error(title, desc):
    return discord.Embed(
        title=f"❌ {title}",
        description=desc,
        color=0xED4245
    )

def info(title, desc):
    return discord.Embed(
        title=f"ℹ️ {title}",
        description=desc,
        color=0x5865F2
    )
