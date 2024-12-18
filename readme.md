# 專案說明

## 簡介

此專案用於自動化 API 通訊、日誌管理與告警處理，包含 Python 腳本 (`MOA.py`) 進行主要任務執行，以及 Bash 腳本 (`run.sh`) 管理服務的生命週期。

---

## 功能

- **API 通訊**：向外部 API 發送請求並處理回應。
- **日誌管理**：維護日誌文件，並自動清理超過一週的記錄。
- **告警系統**：當條件符合時，發送郵件告警並觸發跑馬燈。
- **排程管理**：根據設定的間隔時間自動執行定期任務。
- **服務控制**：透過 Bash 腳本啟動、停止並監控 Python 服務。

---

## 系統需求

- Python 3
- `requests` 和 `configparser` 套件
- 一個有效的配置文件 `CSConfig.ini`

---

## 檔案結構

- **`MOA.py`**：主要的 Python 腳本，負責 API 通訊與任務排程。
- **`run.sh`**：Bash 腳本，用於管理服務的啟動與停止。
- **`CSConfig.ini`**：配置文件，包含 URL、API 密鑰與相關設定。
- **`log.txt`**：日誌文件，用於記錄腳本活動。

---

## 使用方法

### 啟動服務

```bash
bash run.sh start
```

### 停止服務

```bash
bash run.sh stop
```

### 查看日誌

```bash
bash run.sh log
```

---

## 配置文件 (`CSConfig.ini`)

- **URL**：設定 API 端點，包括 `tccalllog`、`share_service` 和 `marquee`。
- **Authorization**：API 密鑰或 Token。
- **排程間隔**：`hour` 用於定義任務執行的間隔時間。
- **告警設定**：`sendmail` 指定告警郵件的收件人。

---

## 注意事項

- 日誌文件超過一週的記錄會自動清理，以控制檔案大小。
- 當任務超過允許時間或發生錯誤時，系統會發送告警通知。
- 確保對 `run.sh` 腳本有執行權限：

```bash
chmod +x run.sh
```

---

## 範例指令

直接執行 Python 腳本：

```bash
python3 MOA.py
```

