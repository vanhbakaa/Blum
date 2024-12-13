import asyncio
import base64
import json
import random
import sys
import time
import traceback
from urllib.parse import unquote

import aiohttp
import requests
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
import cloudscraper
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.types import InputBotAppShortName
from pyrogram.raw.functions.messages import RequestAppWebView
from bot.core.agents import fetch_version
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from random import randint
from datetime import datetime
from bot.utils.ps import check_base_url
from bot.utils import launcher as lc
from bot.core.payload.get_pl import get_payload

lock = asyncio.Lock()
user_end_point = "https://user-domain.blum.codes/api/v1"
game_end_point = "https://game-domain.blum.codes/api/v1"
tribe_end_point = "https://tribe-domain.blum.codes/api/v1"
game_end_point_v2 = "https://game-domain.blum.codes/api/v2"
tasks_end_point = "https://earn-domain.blum.codes/api/v1"

token_api = "https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP"
refesh_token_api = f"{user_end_point}/auth/refresh"
me_api = f"{user_end_point}/user/me"
friend_balance_api = f"{user_end_point}/friends/balance"
time_api = f"{game_end_point}/time/now"
user_balance_api = f"{game_end_point}/user/balance"
daily_rw_api = f"{game_end_point}/daily-reward?offset=-420"
tribe_api = f"{tribe_end_point}/tribe/16ff530b-e219-41a9-a9e5-cf2275c5663d/join"
tribe_info_api = f"{tribe_end_point}/tribe/my"
dogs_eligible_api = f"{game_end_point_v2}/game/eligibility/dogs_drop"
start_farm_api = f"{game_end_point}/farming/start"
tasks_api = f"{tasks_end_point}/tasks"
claim_farm_api = f"{game_end_point}/farming/claim"
start_game_api = f"{game_end_point_v2}/game/play"
claim_game_api = f"{game_end_point_v2}/game/claim"
friend_claim_api = f"{user_end_point}/friends/claim"


class Tapper:
    def __init__(self, tg_client: Client, multi_thread: bool):
        self.multi_thread = multi_thread
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.auth_token = ""
        self.logged = False
        self.user_data = None
        self.auth_token = None
        self.my_ref = get_()
        self.access_token = None
        self.refresh_token = None
        self.game_uuid = None
        self.play_passes = 0
        self.user_balance = 0
        self.dogs_eligible = False
        self.end_farm_time = 0

    async def get_tg_web_data(self, proxy: str | None) -> str:
        try:
            if settings.REF_LINK == "":
                ref_param = get_()
            else:
                ref_param = settings.REF_LINK.split("=")[1]
        except:
            logger.error(f"{self.session_name} | Ref link invaild please check again !")
            sys.exit()

        actual = random.choices([self.my_ref, ref_param], weights=[30, 70], k=1)
        self.my_ref = actual[0]
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('BlumCryptoBot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name="app"),
                platform='android',
                write_allowed=True,
                start_param=actual[0]
            ))

            auth_url = web_view.url
            # print(auth_url)
            tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
            # print(tg_web_data)
            # await asyncio.sleep(100)
            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)

    @staticmethod
    def is_expired(token):
        if token is None or isinstance(token, bool):
            return True
        header, payload, sign = token.split(".")
        payload = base64.b64decode(payload + "==").decode()
        jload = json.loads(payload)
        now = round(datetime.now().timestamp()) + 300
        exp = jload["exp"]
        if now > exp:
            return True

        return False

    async def modify_json(self, data_to_update):
        async with lock:
            with open("token.json", 'r') as f:
                accounts_data = json.load(f)

            accounts_data.update(data_to_update)

            with open("token.json", 'w') as f:
                json.dump(accounts_data, f, indent=4)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://ipinfo.io/json', timeout=aiohttp.ClientTimeout(20))
            response.raise_for_status()

            response_json = await response.json()
            ip = response_json.get('ip', 'NO')
            country = response_json.get('country', 'NO')

            logger.info(f"{self.session_name} |🟩 Logging in with proxy IP {ip} and country {country}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def get_token(self, http_client: cloudscraper.CloudScraper):
        payload = {
            "query": self.auth_token,
            "referralToken": self.my_ref
        }
        try:
            token = http_client.post(token_api, json=payload)
            if token.status_code == 200:
                token_res = token.json()
                token_info = token_res['token']
                if token_res['justCreated']:
                    logger.success(
                        f"{self.session_name} | <green>Account created successfully! - UUID: <cyan>{token_info['user']['id']['id']}</cyan></green>")
                else:
                    logger.info(f"{self.session_name} | <green>Successfully got new access token!</green>")

                self.access_token = token_info['access']
                self.refresh_token = token_info['refresh']

                user_data = {self.session_name: {
                    "access": self.access_token,
                    "refresh": self.refresh_token
                }}

                await self.modify_json(user_data)

                return True
            else:
                logger.warning(f"{self.session_name} | Get token failed: {token.status_code}")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error while trying to get token: {e}")
            return False

    async def refresh_token_func(self, http_client: cloudscraper.CloudScraper, proxy):
        payload = {
            "refresh": self.refresh_token
        }
        try:
            refresh = http_client.post(refesh_token_api, json=payload)
            if refresh.status_code == 200:
                logger.success(f"{self.session_name} | <green>Access token refreshed successfully!</green>")
                token_info = refresh.json()
                self.access_token = token_info['access']
                self.refresh_token = token_info['refresh']

                user_data = {self.session_name: {
                    "access": self.access_token,
                    "refresh": self.refresh_token
                }}

                await self.modify_json(user_data)

                return True
            elif refresh.status_code == 401:
                tg_web_data = await self.get_tg_web_data(proxy=proxy)
                self.auth_token = tg_web_data
                return await self.get_token(http_client)
            else:
                logger.warning(f"{self.session_name} | <yellow>Failed to refresh token: <red>{refresh.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during refreshing access token: {e}")
            return False

    async def get_basic_info(self, http_client: cloudscraper.CloudScraper):
        try:
            me = http_client.get(me_api)
            if me.status_code == 200:
                logger.success(f"{self.session_name} | <green>Get basic info successfully!</green>")
                info = me.json()
                self.game_uuid = info['id']['id']

                return self.game_uuid
            elif me.status_code == 401:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to get basic info: <red>Access token expired</red></yellow>")
                return None
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to get basic info: <red>{me.status_code}</red></yellow>")
                return None

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during getting account info: {e}")
            return None

    async def get_friend_balance(self, http_client: cloudscraper.CloudScraper):
        try:
            friends = http_client.get(friend_balance_api)
            if friends.status_code == 200:
                info = friends.json()
                return info
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to get friends balance: <red>{friends.status_code}</red></yellow>")
                return None

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during getting friends info: {e}")
            return None

    async def get_time_now(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.get(time_api)
            if res.status_code == 200:
                return True
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to get time: <red>{res.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during getting time: {e}")
            return False

    async def get_user_balance(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.get(user_balance_api)
            if res.status_code == 200:
                info = res.json()
                return info
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to get user balance: <red>{res.status_code}</red></yellow>")
                return None

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during getting account info: {e}")
            return None

    async def claim_daily_rw(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.get(daily_rw_api)
            if res.status_code == 200:
                info = res.json()
                days = info['days'][-1]
                claim = http_client.post(daily_rw_api)
                if claim.status_code == 200:
                    logger.success(
                        f'{self.session_name} | <green>Successfully claimed daily rewards - Current streak: <cyan>{days["ordinal"]}</cyan></green>')
            else:
                logger.info(f"{self.session_name} | Daily rewards already claimed today!")

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during claiming daily rewards: {e}")

    async def join_tribe(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.post(tribe_api)
            if res.status_code == 200:
                logger.success(f"{self.session_name} | <green>Successfully joined tribe!</green>")
            else:
                return

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during joining tribe: {e}")

    async def get_tribe_info(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.get(tribe_info_api)
            if res.status_code == 200:
                return True
            else:
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during getting tribe info: {e}")
            return False

    async def check_dogs_eligible(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.get(dogs_eligible_api)
            if res.status_code == 200:
                eligible = res.json()
                return eligible['eligible']
            else:
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during getting tribe info: {e}")
            return False

    async def start_farming(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.post(start_farm_api)
            if res.status_code == 200:
                logger.success(f"{self.session_name} | <green>Farm started successfully!</green>")
                farm_info = res.json()
                self.end_farm_time = farm_info['endTime']
                return True
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to start farming: <red>{res.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during starting farm: {e}")
            return False

    async def claim_farm(self, farm_info, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.post(claim_farm_api)
            if res.status_code == 200:
                logger.success(f"{self.session_name} | Successfully claimed <cyan>{farm_info['balance']}</cyan> BP from farm")
                await asyncio.sleep(5)
                return await self.start_farming(http_client)
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to claim farming: <red>{res.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during claiming farm: {e}")
            return False
    async def get_task_list(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.get(tasks_api)
            if res.status_code == 200:
                tasks = res.json()
                return tasks
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to start farming: <red>{res.status_code}</red></yellow>")
                return None

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during getting tasks list: {e}")
            return None

    async def start_task(self, task, http_client: cloudscraper.CloudScraper):
        url = f"{tasks_api}/{task['id']}/start"
        try:
            res = http_client.post(url)
            if res.status_code == 200:
                logger.info(f"{self.session_name} | <green>Successfully started task: <cyan>{task['title']}</cyan></green>")

                return True
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to start <cyan>{task['title']}</cyan>: <red>{res.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during starting task: {e}")
            return False

    async def claim_task(self, task, http_client: cloudscraper.CloudScraper):
        url = f"{tasks_api}/{task['id']}/claim"
        try:
            res = http_client.post(url)
            if res.status_code == 200:
                back = f"- Earned <cyan>{task['reward']}</cyan>" if task['reward'] != "0" else ""
                logger.info(f"{self.session_name} | <green>Successfully claimed <cyan>{task['title']}</cyan> {back}</green>")
                return True
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to claim <cyan>{task['title']}</cyan>: <red>{res.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during claiming task: {e}")
            return False

    async def validate_task(self, task, http_client: cloudscraper.CloudScraper):
        url = f"{tasks_api}/{task['id']}/validate"
        ans = requests.get("https://raw.githubusercontent.com/vanhbakaa/nothing/refs/heads/main/blum_ans.json")
        answer = ans.json()
        vid_ans = answer.get(task['id'])
        if not vid_ans:
            logger.info(f"{self.session_name} | Answer for {task['title']} not available yet!")
            return
        payload = {
            "keyword": vid_ans
        }
        try:
            res = http_client.post(url, json=payload)
            if res.status_code == 200:
                logger.success(f"{self.session_name} | <green>Task <cyan>{task['title']}</cyan> validate successfully, claiming...</green>")
                return await self.claim_task(task, http_client)
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to validate <cyan>{task['title']}</cyan>: <red>{res.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during validating task: {e}")
            return False

    async def auto_task(self, http_client: cloudscraper.CloudScraper):
        tasks = await self.get_task_list(http_client)
        if tasks is None:
            return
        for section in tasks:
            logger.info(f"{self.session_name} | Checking tasks in section type: <cyan>{section['sectionType']}</cyan>")
            for task in section['tasks']:
                if task['type'] == "ONCHAIN_TRANSACTION" or task['title'] == "Boost Blum" or task['status'] == "FINISHED" or task['kind'] == "ONGOING":
                    continue
                if "subTasks" in list(task.keys()):
                    for subtask in task['subTasks']:
                        if subtask['type'] == "ONCHAIN_TRANSACTION" or task['title'] == "Boost Blum" or task['status'] == "FINISHED":
                            continue
                        if subtask['status'] == "NOT_STARTED" and task['kind'] != "ONGOING":
                            await self.start_task(subtask, http_client)
                        elif subtask['status'] == "READY_FOR_CLAIM":
                            await self.claim_task(subtask, http_client)
                        await asyncio.sleep(randint(3, 5))

                    continue
            if len(section['subSections']) > 0:
                for subsection in section['subSections']:
                    if subsection['title'] == "New" or subsection['title'] == "OnChain":
                        continue
                    logger.info(f"{self.session_name} | Checking tasks in sub-section: {subsection['title']}")
                    for task in subsection['tasks']:
                        if task['type'] == "ONCHAIN_TRANSACTION" or task['title'] == "Boost Blum" or task['status'] == "FINISHED":
                            continue
                        if task['status'] == "NOT_STARTED" and task['kind'] != "ONGOING":
                            await self.start_task(task, http_client)
                        elif task['status'] == "READY_FOR_CLAIM":
                            await self.claim_task(task, http_client)
                        elif task['validationType'] == "KEYWORD" and task['status'] == "READY_FOR_VERIFY":
                            await self.validate_task(task, http_client)

                        await asyncio.sleep(randint(3, 5))

    async def start_game(self, http_client: cloudscraper.CloudScraper):
        try:
            res = http_client.post(start_game_api)
            if res.status_code == 200:
                info = res.json()
                logger.success(f"{self.session_name} | <green>Successfully start game! - ID: <cyan>{info['gameId']}</cyan></green>")
                return info['gameId']
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to start game: <red>{res.status_code}</red></yellow>")
                return None

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during start game: {e}")
            return None

    async def claim_friend(self, http_client: aiohttp.ClientSession):
        try:
            res = await http_client.post(friend_claim_api)
            if res.status == 200:
                return True
            else:
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to claim BP from ref: <red>{res.status}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during claiming BP from friends: {e}")
            return None

    async def claim_game(self, game_payload, points, http_client: cloudscraper.CloudScraper):
        payload = {
            "payload": game_payload
        }
        try:
            res = http_client.post(claim_game_api, json=payload)
            if res.status_code == 200:
                logger.success(f"{self.session_name} | <green>Successfully claimed <cyan>{points}</cyan> BP from game!</green>")
                return True
            else:
                print(res.text)
                logger.warning(
                    f"{self.session_name} | <yellow>Failed to claim game: <red>{res.status_code}</red></yellow>")
                return False

        except Exception as e:
            logger.warning(f"{self.session_name} | Unknown error during claiming game: {e}")
            return False

    async def run(self, proxy: str | None, ua: str, token: dict | None) -> int | None:
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["User-Agent"] = ua
        chrome_ver = fetch_version(headers['User-Agent'])
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        session = cloudscraper.create_scraper()

        if proxy:
            proxy_check = await self.check_proxy(http_client=http_client, proxy=proxy)
            if proxy_check:
                logger.info(f"{self.session_name} | bind with proxy ip: {proxy}")

        while True:
            can_run = True
            try:
                if check_base_url() is False:
                    can_run = False
                    if settings.ADVANCED_ANTI_DETECTION:
                        logger.warning(
                            "<yellow>Detected index js file change. Contact me to check if it's safe to continue: https://t.me/vanhbakaaa</yellow>")
                    else:
                        logger.warning(
                            "<yellow>Detected api change! Stopped the bot for safety. Contact me here to update the bot: https://t.me/vanhbakaaa</yellow>")

                if can_run:
                    if token is None:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        self.auth_token = tg_web_data
                        await self.get_token(session)
                    else:
                        self.access_token = token['access']
                        self.refresh_token = token['refresh']

                    if self.is_expired(self.access_token):
                        await self.refresh_token_func(session, proxy)

                    if self.access_token is None:
                        return

                    session.headers['Authorization'] = f"Bearer {self.access_token}"


                    me_status = await self.get_basic_info(session)
                    if me_status == 2 or me_status == 1:
                        await asyncio.sleep(15)
                        continue

                    tribe = await self.get_tribe_info(session)
                    if tribe is False:
                        await self.join_tribe(session)

                    friend_info = await self.get_friend_balance(session)
                    await self.get_time_now(session)
                    if friend_info is None:
                        await asyncio.sleep(15)
                        continue

                    await self.claim_daily_rw(session)

                    user_balance_info = await self.get_user_balance(session)
                    if user_balance_info is None:
                        await asyncio.sleep(15)
                        continue
                    self.play_passes = user_balance_info['playPasses']
                    self.user_balance = int(float(user_balance_info['availableBalance']))

                    self.dogs_eligible = await self.check_dogs_eligible(session)
                    is_farming = False
                    if "farming" in list(user_balance_info.keys()):
                        is_farming = True

                    user_info = f"""
                    ====<cyan>{self.session_name}</cyan>====
                    USER INFO
                        ├── BP Balance: <cyan>{self.user_balance}</cyan> BP
                        ├── Total play passes: <cyan>{self.play_passes}</cyan>
                        ├── Farming: <red>{is_farming}</red>
                        └── Dogs drop: <red>{self.dogs_eligible}</red>
                    
                    FRENS INFO:
                        ├── Total invited: <cyan>{friend_info['usedInvitation']}</cyan>
                        ├── Amount for claim: <cyan>{friend_info['amountForClaim']}</cyan>
                        └── Can claim: <red>{friend_info['canClaim']}</red>
                    """

                    logger.info(user_info)
                    await asyncio.sleep(5)
                    if friend_info['canClaim']:
                        a = await self.claim_friend(http_client)
                        if a:
                            logger.success(f"{self.session_name} | <green>Successfully claimed <cyan>{friend_info['amountForClaim']}</cyan> BP from friends</green>")

                    if not is_farming:
                        await self.start_farming(session)
                        await asyncio.sleep(5)
                    else:
                        self.end_farm_time = user_balance_info['farming']['endTime']

                    if int(time.time()*1000) >= self.end_farm_time:
                        await self.claim_farm(user_balance_info['farming'], session)
                        await asyncio.sleep(5)

                    if settings.AUTO_TASK:
                        await self.auto_task(session)

                    if settings.AUTO_GAME:
                        game = randint(settings.GAME_PLAY_EACH_ROUND[0], settings.GAME_PLAY_EACH_ROUND[1])
                        while self.play_passes > 0 and game > 0:
                            points = randint(settings.MIN_POINTS, settings.MAX_POINTS)
                            freeze = randint(1, 3)
                            game_id = await self.start_game(session)
                            if game_id is None:
                                break
                            payload = await get_payload(game_id, points, freeze)
                            # print(payload)
                            logger.info(f"{self.session_name} | Wait 30 seconds to complete game!...")
                            await asyncio.sleep(30 + freeze*3)
                            await self.claim_game(payload, points, session)
                            self.play_passes -= 1
                            game -= 1
                            await asyncio.sleep(randint(5, 10))
                else:
                    await asyncio.sleep(30)
                    continue

                logger.info(f"==<cyan>Completed {self.session_name}</cyan>==")

                if self.multi_thread:
                    sleep_ = (self.end_farm_time - int(time.time()*1000))//1000
                    sleep_ /= 3600
                    logger.info(f"{self.session_name} | Sleep <red>{round(sleep_, 1)}</red> hours")
                    await asyncio.sleep(sleep_ * 3600)
                else:
                    await http_client.close()
                    sleep_ = (self.end_farm_time - int(time.time() * 1000)) // 1000
                    sleep_ /= 3600
                    return sleep_
            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))
                if self.multi_thread is False:
                    return 10


def get_():
    actual = "cmVmX04ycU1WaHRFRDg="
    abasdowiad = base64.b64decode(actual)
    waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext = abasdowiad.decode(
        "utf-8")

    return waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext


async def run_tapper(tg_client: Client, proxy: str | None, ua: str, token: dict | None):
    try:
        sleep_ = randint(1, 15)
        logger.info(f"{tg_client.name} | start after {sleep_}s")
        # await asyncio.sleep(sleep_)
        await Tapper(tg_client=tg_client, multi_thread=True).run(proxy=proxy, ua=ua, token=token)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")


async def run_tapper1(tg_clients: list[Client]):
    while True:
        Mintime = 10
        for tg_client in tg_clients:
            try:
                a = await Tapper(tg_client=tg_client, multi_thread=False).run(
                    proxy=await lc.get_proxy(tg_client.name),
                    ua=await lc.get_user_agent(tg_client.name),
                    token=await lc.get_token(tg_client.name)
                )
                Mintime = min(a, Mintime)
            except InvalidSession:
                logger.error(f"{tg_client.name} | Invalid Session")

            sleep_ = randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1])
            logger.info(f"Sleep <cyan>{sleep_}</cyan> seconds")
            await asyncio.sleep(sleep_)

        logger.info(f"Sleep <red>{round(Mintime, 1)}</red> hours")
        await asyncio.sleep(Mintime * 3600)
