from datetime import datetime, timedelta

import aiohttp

from api import Singleton


class PatreonTier:
    id: int
    title: str

    def __init__(self, id, title):
        self.id = id
        self.title = title


class CampaignTierCache:
    timestamp: datetime
    tiers: list[PatreonTier]

    def __init__(self, timestamp, tiers):
        self.timestamp = timestamp
        self.tiers = tiers


class MemberInfo:
    tiers: list[str]
    discord_id: int | None

    def __init__(self, tiers, discord_id):
        self.tiers = tiers
        self.discord_id = discord_id


class PatreonApi(metaclass=Singleton):
    session: aiohttp.ClientSession
    campaign_tier_cache: dict[str, CampaignTierCache] = {}

    def __init__(self, campaign_id: str, access_token: str):
        self.campaign_id = campaign_id
        self.access_token = access_token

    async def async_init__(self):
        self.session = aiohttp.ClientSession(base_url="https://www.patreon.com")

    async def update_token(self, client_id: str, client_secret, refresh_token: str):
        url = "/api/oauth2/token"
        params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        async with self.session.post(url, params=params) as response:
            auth_data = await response.json()
            print(auth_data)

    async def fetch_tiers(self) -> list[PatreonTier]:
        cache_entry = self.campaign_tier_cache.get(self.campaign_id, None)
        current_time = datetime.now()
        if cache_entry is not None:
            if (current_time - cache_entry.timestamp) < timedelta(minutes=30):
                return cache_entry.tiers

        url = f"/api/oauth2/v2/campaigns/{self.campaign_id}"
        params = {
            "include": "tiers",
            "fields[tier]": "title",
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        tiers = []
        async with self.session.get(url, params=params, headers=headers) as response:
            campaign_data = await response.json()
            for included in campaign_data.get("included", []):
                if included.get("type") != "tier":
                    continue
                tiers.append(
                    PatreonTier(
                        int(included.get("id")),
                        included.get("attributes", {}).get("title", ""),
                    )
                )

        self.campaign_tier_cache[self.campaign_id] = CampaignTierCache(
            datetime.now(), tiers
        )
        return tiers

    async def fetch_members(self) -> dict[str, MemberInfo]:
        url = f"/api/oauth2/v2/campaigns/{self.campaign_id}/members"
        params = {
            "include": "user,currently_entitled_tiers",
            "fields[user]": "social_connections",
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}
        patreons: dict[str, MemberInfo] = {}

        end_cursor = False
        while not end_cursor:
            async with self.session.get(
                url, params=params, headers=headers
            ) as response:
                patreon_data = await response.json()
                for data in patreon_data.get("data", []):
                    discord_user_id = None
                    for patreon_user in patreon_data.get("included", []):
                        if patreon_user.get("type") != "user":
                            continue

                        if data["relationships"]["user"]["data"][
                            "id"
                        ] != patreon_user.get("id"):
                            continue

                        patreon_user_data = patreon_user.get("attributes", {})
                        if not "social_connections" in patreon_user_data:
                            continue

                        discord_data = patreon_user["attributes"]["social_connections"][
                            "discord"
                        ]

                        if not discord_data or not "user_id" in discord_data:
                            continue

                        discord_user_id = int(discord_data.get("user_id", ""))

                    patreons[data["relationships"]["user"]["data"]["id"]] = MemberInfo(
                        [
                            d["id"]
                            for d in data["relationships"]["currently_entitled_tiers"][
                                "data"
                            ]
                        ],
                        discord_user_id,
                    )

                pagination_data = patreon_data["meta"]["pagination"]
                if (
                    not pagination_data.get("cursors")
                    or pagination_data["cursors"].get("next", None) is None
                ):
                    end_cursor = True
                else:
                    next_cursor_id = pagination_data["cursors"]["next"]
                    params["page[cursor]"] = next_cursor_id

        return patreons
