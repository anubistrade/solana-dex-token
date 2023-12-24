from telegram import Bot
from telegram.constants import ParseMode
import mysql.connector
import asyncio
import time
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from telegram.error import BadRequest

from jsonrpcclient import request, parse, Ok
import logging
import requests

# Замените 'API_ID' и 'API_HASH' на ваши данные
api_id = ''
api_hash = ''

bot_token = ''
channel_id = '@dexscreeneronline'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="solana_token"
)

async def send_message_to_channel(message, channel_id):
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=channel_id, text=message, parse_mode='Markdown')
    except BadRequest as e:
        print(f"Failed to send message: {e}")


async def get_tokens_search():
    cursor = db.cursor(dictionary=True)
    sql = "SELECT * FROM tokens WHERE 1 AND mint=1 AND burn!=1 AND scam!=1 AND (telegram IS NOT NULL OR twitter IS NOT NULL) AND timestamp>%s" #AND (telegram IS NOT NULL OR twitter IS NOT NULL)
    val = ((int(time.time()) - 3600), )
    try:
        cursor.execute(sql, val)
        result = cursor.fetchall()  # Fetch the first result

        if result:
            return result
        else:
            return (0, )

    except mysql.connector.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()


async def get_lpaddress(token_address):
    cursor = db.cursor()
    sql = "SELECT lpMint FROM raydium WHERE baseMint = %s AND quoteMint = 'So11111111111111111111111111111111111111112' " \
          "OR baseMint = 'So11111111111111111111111111111111111111112' AND quoteMint = %s LIMIT 1"
    val = (token_address, token_address )

    try:
        cursor.execute(sql, val)
        result = cursor.fetchone()  # Fetch the first result

        if result:
            return result
        else:
            return (0, )

    except mysql.connector.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()

async def update_token_scam_database(item):
    cursor = db.cursor()
    sql = "UPDATE `tokens` SET scam=1 WHERE 1 AND address=%s"
    val =(item['tokenAddress'], )

    try:
        cursor.execute(sql, val)
        db.commit()
    except mysql.connector.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()


async def update_token_burn_database(item):
    cursor = db.cursor()
    sql = "UPDATE `tokens` SET burn=1 WHERE 1 AND address=%s"
    val =(item['tokenAddress'], )

    try:
        cursor.execute(sql, val)
        db.commit()
    except mysql.connector.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()

async def update_lp_token_supply(item):
    cursor = db.cursor()
    sql = "UPDATE `tokens` SET lp_supply=%s WHERE 1 AND address=%s"
    val =(item['lp_supply'], item['tokenAddress'], )

    try:
        cursor.execute(sql, val)
        db.commit()
    except mysql.connector.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()

async def print_red(text):
    RED = '\033[91m'
    RESET = '\033[0m'
    print(f"{RED}{text}{RESET}")

async def print_green(text):
    print(f"\033[92m{text}\033[0m")


async def main():

    tokens = await get_tokens_search()

    print(f"Number of tokens: {len(tokens)}\n")

    if tokens[0] != 0:
        for token in tokens:
            lp_address = await get_lpaddress(token['address'])
            supply_spl_token = None
            supply_lp_token = None

            if lp_address[0] != 0:
                print(token)
                print(f'LP address: {lp_address[0]}')

                try:
                    response = requests.post("https://tame-aged-star.solana-mainnet.quiknode.pro/70b1d6a8ee1c4cb59b211636ab7a8dde52eba884/", json=request("getTokenSupply", params=([token['address']])))
                    parsed = parse(response.json())

                    if isinstance(parsed, Ok):
                        result = parsed.result
                        supply_spl_token = result['value']['uiAmount']
                        print(f"Supply SPL token: {result['value']['uiAmount']} type {type(result['value']['uiAmount'])}")
                    else:
                        logging.error(parsed.message)
                except Exception as e:
                    print(f"An error occurred: {e}")

                try:
                    response = requests.post("https://tame-aged-star.solana-mainnet.quiknode.pro/70b1d6a8ee1c4cb59b211636ab7a8dde52eba884/", json=request("getTokenSupply", params=([lp_address[0]])))
                    parsed = parse(response.json())

                    if isinstance(parsed, Ok):
                        result = parsed.result
                        supply_lp_token = result['value']['uiAmount']
                        if supply_lp_token!=0 and token['lp_supply'] == 0:
                            item = {}
                            item['lp_supply'] = supply_lp_token
                            item['tokenAddress'] = token['address']
                            await update_lp_token_supply(item)
                        print(f"Supply LP token: {supply_lp_token} type {type(supply_lp_token)}")
                    else:
                        logging.error(parsed.message)
                except Exception as e:
                    print(f"An error occurred: {e}")

                # Get SPL token ballance

                pubkey_token = None

                try:
                    solana_client = Client("https://tame-aged-star.solana-mainnet.quiknode.pro/70b1d6a8ee1c4cb59b211636ab7a8dde52eba884/")

                    pub_key = Pubkey.from_string(token['owner'])
                    mint_account = Pubkey.from_string(token['address'])

                    response_dict = solana_client.get_token_accounts_by_owner(pub_key, TokenAccountOpts(mint=mint_account))

                    if response_dict and response_dict.value:
                        for item in response_dict.value:
                            pubkey_token = item.pubkey
                            print(f'Account SPL token: {pubkey_token}')
                    else:
                        print("Error: Unable to retrieve token accounts.")
                except Exception as e:
                    print(f"An error occurred: {e}")

                # Get SPL-LP token ballance
                ballance_owner_spl = 0

                if pubkey_token is not None:
                    try:
                        solana_client = Client("https://tame-aged-star.solana-mainnet.quiknode.pro/70b1d6a8ee1c4cb59b211636ab7a8dde52eba884/")

                        response_dict = solana_client.get_token_account_balance(pubkey_token)

                        if response_dict and response_dict.value:
                            ballance_owner_spl = response_dict.value.ui_amount
                            print(f'Balance SPL token: {response_dict.value.ui_amount} type {type(response_dict.value.ui_amount)}')
                        else:
                            print("Error: Unable to retrieve token balance.")

                    except Exception as e:
                        print(f"An error occurred: {e}")

                if supply_spl_token is not None and supply_lp_token is not None:
                    if int(ballance_owner_spl) > int(supply_spl_token) * 0.2:
                        await print_red(f'😂Scam token {token["address"]} time {int(time.time())}😂')
                        item = {}
                        item['tokenAddress'] = token['address']
                        await update_token_scam_database(item)
                        # message_to_send = f"😂Scam token😂\n{token['address']}"
                        # await send_message_to_channel(message_to_send, channel_id)
                    else:
                        if token['lp_supply'] > 0 and supply_lp_token < token['lp_supply'] * 0.9:
                            await print_green(f'🔥🔥🔥LP Burn LFG {token["address"]} time {int(time.time())} 🔥🔥🔥')
                            item = {}
                            item['tokenAddress'] = token['address']
                            await update_token_burn_database(item)
                            message_to_send = f"🔥🔥🔥 {token['name']} 🔥🔥🔥\n" \
                                              f"Ca: {token['address']}\n\n" \
                                              f"Tg: {token['telegram']}\n" \
                                              f"Tw: {token['twitter']}\n\n" \
                                              f"📈 [Birdeye chart](https://birdeye.so/token/{token['address']}?chain=solana)\n\n" \
                                              f"💰 [Raydium swap](https://raydium.io/swap/?inputCurrency=sol&outputCurrency={token['address']})\n\n" \
                                              f"👨‍💻 [Owner wallet check](https://solscan.io/account/{token['owner']}#splTransfers)\n"

                            await send_message_to_channel(message_to_send, channel_id)

                print(f'End token analys {token["address"]}')
                print('\n')

            time.sleep(0.5)
    time.sleep(10)

if __name__ == '__main__':
    while True:
        try:
            # Запускаем асинхронный цикл
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        finally:
            loop.close()