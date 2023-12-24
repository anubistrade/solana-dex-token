from telethon.sync import TelegramClient
from telethon.tl import types
from datetime import datetime, timezone
from telegram import Bot
import mysql.connector
import asyncio
import time
import re
from telethon.tl.custom import Message
from telegram.error import BadRequest
import datetime

# Замените 'API_ID' и 'API_HASH' на ваши данные
api_id = ''
api_hash = ''

bot_token = ''
channel_id = '@dexscreeneronline'

# Создайте клиент Telethon
client = TelegramClient('your_session22', api_id, api_hash)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="solana_token"
)


def to_utc(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S+00:00").replace(tzinfo=timezone.utc)


async def send_message_to_channel(message, channel_id):
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=channel_id, text=message, parse_mode='Markdown')
    except BadRequest as e:
        print(f"Failed to send message: {e}")


async def save_to_database(item):
    cursor = db.cursor()
    sql = "INSERT INTO tokens (id, message_id, supply, tax, telegram, twitter, web, name, ticket, address, owner, lptoken, active, send_tg, burn, mint, fdv, liq, price, idmarket, message_id_secon, timestamp, scam, lp_supply)" \
          " VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 0, 0, 0, 0, 0, 0, 0, NULL, 0, 0, 0, 0)"
    val =(item['message_id'], item['supply'], item['tax'], item['telegram'], item['twitter'], item['web'], item['name'], item['ticket'], item['address'], item['owner'])

    try:
        cursor.execute(sql, val)
        db.commit()
    except mysql.connector.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()


async def update_database(item):
    cursor = db.cursor()
    sql = "UPDATE `tokens` SET mint=%s, fdv=%s, liq=%s, price=%s, idmarket=%s, message_id_secon=%s, timestamp=%s WHERE 1 AND address=%s"
    val =(item['mint'], item['fdv'], item['liq'], item['price'], item['idmarket'], item['message_id'], item['timestamp'], item['tokenAddress'])

    try:
        cursor.execute(sql, val)
        db.commit()
    except mysql.connector.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()

async def get_last_message_id():
    cursor = db.cursor()
    sql = "SELECT message_id FROM tokens ORDER BY message_id DESC LIMIT 1"

    try:
        cursor.execute(sql)
        result = cursor.fetchone()

        if result:
            return result
        else:
            return None

    except mysql.connector.IntegrityError as e:
        print(f"An errors occurred: {e}")
    finally:
        cursor.close()


async def get_last_message_id_second():
    cursor = db.cursor()
    sql = "SELECT message_id_secon FROM tokens ORDER BY message_id_secon DESC LIMIT 1"

    try:
        cursor.execute(sql)
        result = cursor.fetchone()

        if result:
            return result
        else:
            return None

    except mysql.connector.IntegrityError as e:
        print(f"An errors occurred: {e}")
    finally:
        cursor.close()


def print_green(text):
    print(f"\033[92m{text}\033[0m")

async def main():

    # Регулярное выражение для поиска адреса контракта
    address_regex = r'`([^`]+)`'
    twitter_regex = r'X: \*\*\*\*(https://twitter\.com/[^\*]+)\*\*'
    telegram_regex = r'Telegram: \*\*\*\*(https://t\.me/[^\*]+)\*\*'
    web_regex = r'Web: (https://[^\s]+)'
    name_regex = r'🌱 \*\*(.*?)\*\*'
    ticket_regex = r'• (.*?) 🌱'
    total_supply_regex = r'Total Supply:  \*\*\[\*\*(.*?)]'
    tax_regex = r'Tax:  \*\*\[\*\*(.*?)]'

    # Регулярные выражения для поиска на канале newsolanapools
    price_regex = r'💰 \*\*Price:\*\* `\$([^`]+)`'
    fdv_regex = r'💎 \*\*FDV:\*\* `\$([^`]+)`'
    liq_regex = r'💦 \*\*Liq:\*\* `\$([^`]+)`'

    print('Start')

    await client.start()

    while True:
        # print('Start read @solanascanner')
        last_id_update = await get_last_message_id()
        last_id_update_second = await get_last_message_id_second()

        async for message in client.iter_messages('@solanascanner'):
            if isinstance(message, Message) and message.text and last_id_update[0] < message.id:
                # print(f'\n {message.date}')
                # print(f'\n {message.id}')

                item = {}
                item['message_id'] = message.id

                match = re.search(total_supply_regex, message.text)
                if match:
                    total_supply_data = match.group(1)
                    # print("Total Supply Data:", total_supply_data)
                else:
                    # print("Total Supply data not found.")
                    total_supply_data = 0

                item['supply'] = re.sub(r',', '', str(total_supply_data))

                match = re.search(tax_regex, message.text)
                if match:
                    tax = match.group(1)
                    # print("Tax:", tax)
                else:
                    # print("Tax data not found.")
                    tax = 0

                item['tax'] = re.sub(r'%', '', str(tax))

                match = re.search(telegram_regex, message.text)

                if match:
                    telegram_link = match.group(1)
                    # print("Telegram Link:", telegram_link)
                else:
                    # print("Telegram link not found.")
                    telegram_link = None

                item['telegram'] = telegram_link

                match = re.search(twitter_regex, message.text)

                if match:
                    twitter_link = match.group(1)
                    # print("Twitter Link:", twitter_link)
                else:
                    # print("Twitter link not found.")
                    twitter_link = None

                item['twitter'] = twitter_link

                match = re.search(web_regex, message.text)

                if match:
                    website_link = match.group(1)
                    # print("Website Link:", website_link)
                else:
                    # print("Website link not found.")
                    website_link = None

                item['web'] = website_link

                match = re.search(name_regex, message.text)

                if match:
                    name = match.group(1)
                    # print("Name:", name)
                else:
                    # print("Name not found.")
                    name = None

                item['name'] = name

                match = re.search(ticket_regex, message.text)

                if match:
                    ticket = match.group(1)
                    # print("Ticket:", ticket)
                else:
                    # print("Ticket not found.")
                    ticket = None

                item['ticket'] = ticket

                addresses = re.findall(address_regex, message.text)

                filtered_addresses = [addr for addr in addresses if addr.lower() != 'none']

                if len(filtered_addresses) >= 2:
                    first_address = filtered_addresses[0]
                    second_address = filtered_addresses[1]
                    # print("Token Address:", first_address)
                    item['address'] = first_address
                    # print("Owner Address:", second_address)
                    item['owner'] = second_address
                    print(f'solanascanner: {item}')
                    await save_to_database(item)
                else:
                    print("Not enough addresses found.")
            else:
                break

        # print('Start read @newsolanapools')
        async for message in client.iter_messages('@newsolanapools'):
            if isinstance(message, Message) and message.text and last_id_update_second[0] < message.id:
                if "Mint Authority: No ✅" in message.text and "Freeze Authority: No ✅" in message.text and "Single holder ownership" not in message.text \
                        and "Top 10 holders high ownership" not in message.text \
                        and "High ownership" not in message.text \
                        and "High holder concentration" not in message.text:
                    # print(message.text)

                    item = {}

                    item['message_id'] = message.id
                    item['mint'] = 1

                    match = re.search(price_regex, message.text)
                    if match:
                        price_token = match.group(1)
                        # print("Price:", price_token)
                    else:
                        # print("Price data not found.")
                        price_token = 0

                    item['price'] = price_token

                    multiple = 1

                    match = re.search(fdv_regex, message.text)
                    if match:
                        if 'B' in match.group(1):
                            multiple = 1000000000
                        if 'M' in match.group(1):
                            multiple = 10000000
                        if 'K' in match.group(1):
                            multiple = 1000

                        fdv_token = re.sub(r'K', '', re.sub(r'M', '', re.sub(r'B', '', match.group(1))))

                        if '.' in fdv_token:
                            fdv_token = int(re.sub(r'\.', '', fdv_token)) * multiple
                        # print("FDV:", fdv_token)
                    else:
                        # print("FDV data not found.")
                        fdv_token = 0

                    item['fdv'] = fdv_token

                    multiple = 1

                    match = re.search(liq_regex, message.text)
                    if match:
                        if 'B' in match.group(1):
                            multiple = 1000000000
                        if 'M' in match.group(1):
                            multiple = 10000000
                        if 'K' in match.group(1):
                            multiple = 1000

                        liq_token = re.sub(r'K', '', re.sub(r'M', '', re.sub(r'B', '', match.group(1))))

                        if '.' in liq_token:
                            liq_token = int(re.sub(r'\.', '', liq_token)) * multiple
                        # print("Liq:", liq_token)
                    else:
                        # print("Liq data not found.")
                        liq_token = 0

                    item['liq'] = liq_token
                    item['timestamp'] = int(message.date.timestamp())
                    item['now_timestamp'] = int(time.time())
                    if isinstance(message, Message) and message.reply_markup:
                        for row in message.reply_markup.rows:
                            for button in row.buttons:
                                if button.url:
                                    # print(f"Found link: {button.url}")
                                    item['idmarket'] = None
                                    if "https://birdeye.so/token/" in button.url and "?chain=solana" in button.url:
                                        tokenAddressSecondChanel =  re.sub(r'\?chain=solana', '', re.sub(r'https://birdeye.so/token/', '', button.url))
                                        # print(tokenAddressSecondChanel)
                                        item['tokenAddress'] = tokenAddressSecondChanel

                    print_green(f'newsolanapools {item}')
                    await update_database(item)

            else:
                break

        await asyncio.sleep(3)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())