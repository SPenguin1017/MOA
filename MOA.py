import requests
import json
import configparser
from datetime import datetime, timedelta

# 定義錯誤日誌檔案路徑
error_log_file = "error.log"

# 初始化配置檔案
configs = configparser.ConfigParser()
configs.read("CSConfig.ini", encoding="utf-8")
tccalllog = configs.get("TCCALLLOG", "tccalllog")
authorization = configs.get("AUTHORIZATION", "authorization")

# API Body
body = {
    "listId": "761c6e12-2247-4cdd-a0f9-93a4a4cb21bc",
    "schemaId": "c5e2b62f-2c6d-4b49-b6d9-b1eef5090167",
    "keyword": ""
}

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": authorization
}

try:
    # 發送 API 請求
    response = requests.post(tccalllog, json=body, headers=headers)

    if response.status_code == 200:
        data = response.json()

        # 提取資料
        records = data.get('data', {}).get('records', [])
        if records:
            first_record = records[0]  # 假設資料為列表，取第一筆
            f_start_time = first_record.get("FStartTime")

            if f_start_time:
                # 將 FStartTime 字串轉為 datetime 對象
                f_start_time_dt = datetime.strptime(f_start_time, "%Y-%m-%d %H:%M:%S")
                new_f_start_time_dt = f_start_time_dt + timedelta(hours=3)
                new_f_start_time = new_f_start_time_dt.strftime("%Y-%m-%d %H:%M:%S")

                current_time = datetime.now()

                # 更新 .ini 文件
                configs.set("TIME", "time", new_f_start_time)  # 確保值為字符串
                with open("CSConfig.ini", "w", encoding="utf-8") as configfile:
                    configs.write(configfile)
                print(f"已將 FStartTime 更新到 [TIME] 區塊的 time：{new_f_start_time}")

                # 計算時間差
                time_difference = current_time - f_start_time_dt

                # 判斷是否超過 3 小時
                if time_difference > timedelta(hours=1):
                    print("超過 3 小時，發送告警郵件")
                    mail_url = configs.get("SHARE_SERVICE", "url")
                    jsondata = {
                        "service": "NOTICE",
                        "action": "sendMail",
                        "param": {
                            "mail_to": "Penguin.Hsieh@chainsea.com.tw",
                            "mail_cc": "",
                            "subject": "資訊局-通話記錄告警",
                            "content": "警告已三小時無通話記錄。",
                        },
                    }
                    data = {
                        "jsondata": json.dumps(jsondata),
                    }
                    send_mail = requests.post(mail_url, files=data)

                    if send_mail.status_code != 200:
                        raise Exception(f"郵件發送失敗，狀態碼: {send_mail.status_code}")
                else:
                    print("未超過 3 小時，無需發送郵件")
        else:
            print("回傳的記錄為空，無需處理")

    else:
        raise Exception(f"API 請求失敗，狀態碼: {response.status_code}")

except Exception as e:
    # 將錯誤訊息寫入 error.log
    with open(error_log_file, "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now()} - 錯誤: {str(e)}\n")
