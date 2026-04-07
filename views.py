import discord
from database import get_setting

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="領取身分組", style=discord.ButtonStyle.green, custom_id="role_btn")
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ 已領取身分組", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="開啟工單", style=discord.ButtonStyle.blurple, custom_id="ticket_btn")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        category_id = await get_setting(interaction.guild.id, "ticket_category")
        category = interaction.guild.get_channel(category_id)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category
        )

        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        await channel.send(
            f"{interaction.user.mention} 工單已建立",
            view=CloseTicketView()
        )

        await interaction.response.send_message(f"✅ {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="關閉工單", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()
