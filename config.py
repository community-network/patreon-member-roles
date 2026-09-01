from dataclasses import dataclass

from environs import Env


@dataclass
class DiscordBot:
    discord_bot_token: str
    patreon_campaign_id: str
    patreon_client_id: str
    patreon_client_secret: str
    patreon_refresh_token: str
    patreon_access_token: str

    @staticmethod
    def from_env(env: Env):
        discord_bot_token = env.str("DISCORD_BOT_TOKEN")
        patreon_campaign_id = env.str("PATREON_CAMPAIGN_ID")
        patreon_client_id = env.str("PATREON_CLIENT_ID")
        patreon_client_secret = env.str("PATREON_CLIENT_SECRET")
        patreon_refresh_token = env.str("PATREON_REFRESH_TOKEN")
        patreon_access_token = env.str("PATREON_ACCESS_TOKEN")
        return DiscordBot(
            discord_bot_token=discord_bot_token,
            patreon_campaign_id=patreon_campaign_id,
            patreon_client_id=patreon_client_id,
            patreon_client_secret=patreon_client_secret,
            patreon_refresh_token=patreon_refresh_token,
            patreon_access_token=patreon_access_token,
        )


@dataclass
class Db:
    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_host: str
    db_port: int = 5432

    @staticmethod
    def from_env(env: Env):
        db_host = env.str("DB_HOST")
        postgres_password = env.str("POSTGRES_PASSWORD")
        postgres_user = env.str("POSTGRES_USER")
        postgres_db = env.str("POSTGRES_DB")
        db_port = env.int("DB_PORT", 5432)
        return Db(
            postgres_user=postgres_user,  # type: ignore
            postgres_password=postgres_password,  # type: ignore
            postgres_db=postgres_db,  # type: ignore
            db_host=db_host,  # type: ignore
            db_port=db_port,
        )


@dataclass
class Config:
    bot: DiscordBot
    db: Db


def load_config() -> Config:
    env = Env()
    env.read_env()

    return Config(
        bot=DiscordBot.from_env(env),
        db=Db.from_env(env),
    )
