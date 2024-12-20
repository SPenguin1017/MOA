import requests
import json
import configparser
import subprocess
import os
import time
from datetime import datetime , timedelta


# 定義常量
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
INI_FILE_PATH = os.path.join(BASE_DIR, "CSConfig.ini")
RUN_SCRIPT_PATH = os.path.join(BASE_DIR, "run.sh")

# 初始化配置文件
configs = configparser.ConfigParser()
configs.read(INI_FILE_PATH, encoding="utf-8")
TCCALLLOG_URL = configs.get("URL", "tccalllog")
SHARE_SERVICE_URL = configs.get("URL", "share_service")
MARQUEE_URL = configs.get("URL","marquee")
AUTHORIZATION = configs.get("AUTHORIZATION", "authorization")
SEND_MAIL = configs.get("ITEM", "sendmail")
HOUR = int(configs.get("ITEM", "hour"))

# global now()
# now() = datetime.strptime("2024-12-16 14:30:00", "%Y-%m-%d %H:%M:%S")

# 清除Log   
def cleanLog():
    if os.path.getsize(LOG_FILE) > 10 * 1024 * 1024:
        try:
            # 如果日誌文件不存在，則不需要處理
            if not os.path.exists(LOG_FILE):
                return
            
            # 讀取所有日誌
            with open(LOG_FILE, "r", encoding="utf-8") as log_file:
                lines = log_file.readlines()

            # 計算一週前的日期
            one_week_ago = datetime.now() - timedelta(days=7)

            # 篩選最近一週的日誌
            recent_logs = []
            for line in lines:
                try:
                    log_date = datetime.strptime(line.split(" - ")[0], "%Y-%m-%d %H:%M:%S")
                    if log_date >= one_week_ago:
                        recent_logs.append(line)
                except ValueError:
                    # 如果日誌行不符合日期格式，保留該行
                    recent_logs.append(line)

            # 將篩選後的日誌寫回文件
            with open(LOG_FILE, "w", encoding="utf-8") as log_file:
                log_file.writelines(recent_logs)
            
            log(f"日誌清理完成，只保留最近一週的記錄，共 {len(recent_logs)} 條。")

        except Exception as e:
            send_alert(e)
            log(f"清理日誌時發生錯誤: {e}")

# 發送 TcCallLog 農業部 Api
def api(retry=3, retry_delay=5):
    for attempt in range(1, retry + 1):
        try:
            response = requests.post(
                TCCALLLOG_URL, 
                json={
                    "listId": "761c6e12-2247-4cdd-a0f9-93a4a4cb21bc",
                    "schemaId": "c5e2b62f-2c6d-4b49-b6d9-b1eef5090167",
                    "keyword": ""
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": AUTHORIZATION
                },
                timeout=10
            )

            if response.status_code != 200:
                raise Exception(f"API 請求失敗，狀態碼: {response.status_code}，回傳內容: {response.text}")

            # 提取數據
            records = response.json().get('data', {}).get('records', [])
            if not records:
                log("回傳的記錄為空，無需處理")
                return None  

            # 提取第一筆數據的時間
            f_start_time = records[0].get("FStartTime")
            if not f_start_time:
                log("未找到有效的 FStartTime，無需處理")
                return None 
            
            return f_start_time

        except requests.RequestException as e:
            log(f"API 請求失敗，重試 {attempt}/{retry} 次，錯誤: {e}")
            time.sleep(retry_delay)

    # 如果多次重試後仍失敗，拋出異常
    raise Exception("API 請求失敗，已重試多次。")
 
# 檢核時間
def checkTime(f_start_time):
    # 將抓回來的時間轉換為 datetime
    f_start_time_dt = datetime.strptime(f_start_time, "%Y-%m-%d %H:%M:%S")

    # 保存原始通話記錄的時間
    f_start_time_first = f_start_time_dt

    # 計算下一次排程時間：基於通話記錄時間加上 HOUR
    while f_start_time_dt <= datetime.now():
        f_start_time_dt += timedelta(hours=HOUR)
        
    # 如果計算出的時間與當前時間太接近，向後調整
    if (f_start_time_dt - datetime.now()).total_seconds() < 60:
        f_start_time_dt += timedelta(minutes=1)

    # 格式化下一次排程時間為字串
    new_f_start_time = f_start_time_dt.strftime("%Y-%m-%d %H:%M:%S")

    return f_start_time_first, new_f_start_time

# 告警跑馬燈
def alert(f_start_time_first):
    if (datetime.now() - f_start_time_first) >= timedelta(hours = HOUR):
        if checkDay():
            log("超過允許時間，發送告警")
            marquee("true")
            marquee("false")
        else:
            log("超過允許時間，但不在可發送日期內")
    else:
        log("未超過允許時間，無需發送告警")

# # 更新 crontab 排程
# def update_cron(new_time):
#     try:
#         subprocess.run(f"{RUN_SCRIPT_PATH} stop", shell=True, check=True)
#         new_time_dt = datetime.strptime(new_time, "%Y-%m-%d %H:%M:%S")
#         cron_time = new_time_dt.strftime("%M %H %d %m *")
#         cron_command = f"(crontab -l 2>/dev/null | grep -v 'run.sh'; echo '{cron_time} {RUN_SCRIPT_PATH} start >> {LOG_FILE} 2>&1') | crontab -"
#         subprocess.run(cron_command, shell=True, check=True)
#         log(f"設置排程：{cron_time}")
#     except subprocess.CalledProcessError as e:
#         log(f"更新 crontab 時發生錯誤: {e}")
    
# 發送告警跑馬燈  
def marquee(launch):
    
    jsondata = {
        "entityId": "193ae890-19e0-055d-10b1-4201c0a83431",
        "cancel": launch
    }
    
    headers = {
    "Authorization": AUTHORIZATION
    }
    
    response = requests.post(MARQUEE_URL, data=json.dumps(jsondata), headers=headers)
    if response.status_code != 200:
        log(f"error code: {response.status_code}")

def checkDay():
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()    # 0=週一, 6=週日

    # 設置時間範圍
    if weekday in range(0, 5):  # 平日（週一到週五）
        start_time = datetime.strptime("11:00:00", "%H:%M:%S").time()
        end_time = datetime.strptime("20:00:00", "%H:%M:%S").time()
    else:  # 週末或假日（週六、週日）
        start_time = datetime.strptime("11:00:00", "%H:%M:%S").time()
        end_time = datetime.strptime("17:00:00", "%H:%M:%S").time()

    # 檢查是否在允許時間段內
    if start_time <= current_time <= end_time:
        return True
    return False

# 發送Error郵件
def send_alert(e):
    jsondata = {
        "service": "NOTICE",
        "action": "sendMail",
        "param": {
            "mail_to": SEND_MAIL,
            "mail_cc": "",
            "subject": "農委會-掛掉了",
            "content": "程式掛掉了ㄚㄚㄚㄚㄚ : " + str(e),
        },
    }
    response = requests.post(SHARE_SERVICE_URL, files={"jsondata": json.dumps(jsondata)})
    if response.status_code != 200:
        log(f"郵件發送失敗，狀態碼: {response.status_code}")
    else:
        log("告警郵件已發送")

# 記錄錯誤日誌
def log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {message}\n")

def main():
    while True:
        try:
            # 清除Log
            cleanLog()
            
            # 發送 TcCallLog 農業部 Api
            f_start_time = api()
            # f_start_time = "2024-12-16 14:00:00"

            f_start_time_first , new_f_start_time = checkTime(f_start_time)

            # 發送告警
            alert(f_start_time_first)    

            # 更新排程
            # update_cron(new_f_start_time)

        except Exception as e:
            # 發送Error郵件
            send_alert(e)
            log(str(e))
            
        # 每 5 分鐘執行一次
        time.sleep(300)

if __name__ == "__main__":
    main()

