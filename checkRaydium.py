import requests
import json
import time
import mysql.connector
import base58

url = "https://api.raydium.io/v2/sdk/liquidity/mainnet.json"
max_wait_time = 90  # Максимальное время ожидания в секундах
output_file_path = "mainnet.json"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="solana_token"
)

def download_file(url, max_wait_time=300):  # max_wait_time в секундах
    start_time = time.time()
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait_time:
                    print("Failed to load file within the specified time.")
                    return None

                print(f"Retrying in 30 seconds. Status code: {response.status_code}")
                time.sleep(30)
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")

            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                print("Failed to load file within the specified time.")
                return None

            print("Retrying in 30 seconds due to a request error.")
            time.sleep(30)

def save_to_disk(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
        # print(f"File saved to {file_path}")

def main():
    cursor = db.cursor()

    while True:
        # print(f"Next Loop {time.time()}")

        data = download_file(url)
        if data is not None:
            save_to_disk(data, output_file_path)
            # print("File loaded and saved successfully.")

        # Открытие JSON-файла и загрузка данных
        with open(output_file_path, 'r', encoding='utf-8') as file:
            data = file.read()
            data_parce = json.loads(data)

        # Перебор элементов JSON и вставка их в базу данных
        for item in data_parce['unOfficial']:
            sql = """
            INSERT INTO raydium (id, baseMint, quoteMint, lpMint, baseDecimals, quoteDecimals, lpDecimals, version, programId,
            authority, openOrders, targetOrders, baseVault, quoteVault, withdrawQueue, lpVault, marketVersion, marketProgramId,
            marketId, marketAuthority, marketBaseVault, marketQuoteVault, marketBids, marketAsks, marketEventQueue)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            val = (
                item['id'], item['baseMint'], item['quoteMint'], item['lpMint'], item['baseDecimals'], item['quoteDecimals'],
                item['lpDecimals'], item['version'], item['programId'], item['authority'], item['openOrders'],
                item['targetOrders'], item['baseVault'], item['quoteVault'], item['withdrawQueue'], item['lpVault'],
                item['marketVersion'], item['marketProgramId'], item['marketId'], item['marketAuthority'],
                item['marketBaseVault'], item['marketQuoteVault'], item['marketBids'], item['marketAsks'],
                item['marketEventQueue']
            )

            try:
                cursor.execute(sql, val)
                db.commit()
                print(item)
            except mysql.connector.Error as e:
                if e.errno != 1062:
                    print(f"An error occurred: {e}")

        time.sleep(30)

    # Закрытие соединения с базой данных
    cursor.close()
    db.close()

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Произошла ошибка: {e}")

        time.sleep(30)