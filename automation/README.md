# 自動策展操作紀錄（2026-11-08）

現有三展廳與館藏保留。正式網站：https://600725abc.github.io/tiny-museum/

## 排程與發布

- GitHub 每日台北時間 09:17 檢查；以**上次逐檔驗證成功的台北日期 + 3 天**判斷是否新增，跨月照常。不是每月的 1、4、7 日，也不是精確計時器。排程可能延遲。
- `push` 只部署，不生成。手動執行與排程共用同一個日期判斷，不提供跳過間隔的付費捷徑。
- `prepare → 提交預留紀錄 → generate → 提交圖片 → render → 提交頁面 → deploy-pages → 線上逐檔 SHA-256 核對 → finalize → 提交成功日期`。
- 使用單一 concurrency 群組且不取消執行中的工作。只有 workflow 處理 Git；Python 不再自行推送。
- `_site` 只收錄 HTML、CSS、images 與公開部署清單。金鑰和內部狀態不進入部署 artifact。
- 原始腳本留存於 `legacy_curator.txt` 供比對，不會執行。

## 付費閘門與預算提案（尚未批准）

必須同時將 GitHub repository variable `MUSEUM_PAID_ENABLED` 設為 `true`，且 `budget.json` 的 `approved` 改成 `true`。現在兩者均關閉。沿用已存在的 `OPENAI_API_KEY` secret；沒有測試有效性，也沒有建立新 key。

- 模型固定 `gpt-image-2.6-flare`，1024×1024、low quality、每次一張、沒有 SDK 自動重試。
- 首次測試提案：最多一次請求，預留 US$0.25。取得結果後先檢查實際用量與畫面，再決定常態啟用。
- 常態提案：每月 US$3 預留額度、最多 12 次請求；正常三天一件約每月 10–11 件。每次先扣 US$0.25 預留額，即使失敗也不自動退回。
- 這是應用端的請求次數與保守預留控制，**不是供應商的美元硬上限**。單次實際帳單依 token 用量計費；首次實測前不可宣稱每張固定費用。其他程式使用同一 API 專案的花費也不在這個帳本內。
- 官方查證：圖片輸出 US$30 / 百萬 tokens，文字輸入 US$5 / 百萬 tokens；本流程沒有圖片輸入。來源：https://developers.openai.com/api/docs/pricing 。模型與格式：https://developers.openai.com/api/docs/models/gpt-image-2.6-flare 、https://developers.openai.com/api/docs/guides/image-generation 。

## 供應與內容

先使用修訂後的候選清單（展籤含趣聞不超過 40 英文單字），再透過 The Met 免費開放 API 自動尋找三展廳相關器物。來源 ID 去重，來源標題、材質、年代留存在該次 state checkpoint 與 Git 歷史。新展品明示 AI 示意圖與數位館藏。

來源文件：https://metmuseum.github.io/ 。使用新 `/v1.1/search` 分頁端點，每個主題最多掃描 2000 筆；實際免費查詢已取得 Spoon、object ID 13502。這提供可持續補充的來源，並不保證無限供應。來源停機、沒有合格資料或查詢範圍耗盡會報錯通知，不會假裝成功。可在 `QUERIES` 增加經審核的日常物件詞。

## 重試與復原

## 成果交付規範（如何交付與交付內容）

每次展品發布完成後，自動化腳本與代理必須嚴格依據以下規範向使用者交付成果：

### 如何交付（交付管道）
1. **GitHub Actions 執行摘要**：自動寫入 `$GITHUB_STEP_SUMMARY`，在每次 CI/CD 執行完成頁面直接呈現可點擊的 Markdown 交付卡片。
2. **終端與日誌標準輸出**：`pipeline.py finalize` 與 `pipeline.py summary` 會在 stdout 輸出結構化交付摘要。
3. **典藏歷史紀錄更新**：自動追加至 `HISTORY.md`，永久記錄發布時間、展品名稱、展廳、展籤字數與檔案連結。
4. **對話互動即時交付**：代理回報時，必須一併附上可點擊的公開網站連結（首頁、展品、展廳、儀表板），不得僅回報成功代碼或檔案路徑。

### 交付內容（必備項目）
1. **4 大公開線上網址**：
   - 館藏首頁（Home URL）
   - 本次新增展品頁面（Exhibit URL）
   - 所屬展廳頁面（Room Gallery URL）
   - 展館儀表板（Dashboard URL）
2. **展品元數據**：
   - 展件中英文名稱
   - 所屬展廳
   - 獲取年份（Acquired Year）
   - 展籤字數（嚴格限制 40 英文單字內）
   - 展籤內文（無驚嘆號）與館長趣聞
3. **驗收證明**：
   - 線上所有公開檔案（HTML、CSS、圖片）與本地 bytes 之 SHA-256 逐檔一致性證明。

- `reserved`：可能已扣款，禁止自動重試。先查該 run 的 recovery artifact 與供應商用量；如果圖片已回傳，取回圖片與 `image_ready` 狀態，提交後重新執行。不確定是否扣款時，不能清掉紀錄重畫。
- `image_ready`：重試只重新產生網頁，不再次付費。
- `rendered`：重試只部署、驗證、完成紀錄，不再次付費。
- `pending=null`：目前沒有未完成展品；成功日期決定下次到期日。
- Git push 衝突會失敗並通知，不 force push。不確定的失敗保留既有頁面與預留額，優先人工核對。
- Recovery artifacts 保留 30 天；Git 中成功存下的圖片與 checkpoint 持續保留。

## 失敗通知與帳戶限制

失敗會保留 Actions 紅色狀態，並建立或更新 `Museum automation needs attention` issue，指派給 repository owner，附執行連結。沒有寄送外部郵件服務。

是否實際收到 Email / GitHub App 推播取決於使用者的通知設定；本次未修改或驗證個人信箱投遞。請在 https://github.com/settings/notifications 啟用 Actions 失敗通知，以及被指派 issue 的通知。排程通知接收者通常是最後修改 cron 或重新啟用排程的人。官方：https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs 。

公開 repository 長期無活動時 GitHub 可能停用排程；付費暫停期間尤其需要留意。正常每三天產生提交時會持續有活動。GitHub 排程服務本身停用或完全未觸發時，該 workflow 無法自行寄出失敗通知；需要外部監控才能涵蓋，這次未新增付費服務。

## 免費驗證

`python -m unittest discover -s tests -v`：不連付費 API，在暫存副本測試跨月/閏日、雙重閘門、圖片 Base64/URL、損壞資料、缺少 marker、原子渲染、重試去重、補充來源去重、部署檔案範圍與成功日期閘門。

線上驗證使用所有公開 HTML、CSS 和圖片的 SHA-256，比 HTTP 200 更嚴格；不代表已目視驗收新生成圖片。第一次付費圖尚未產生，圖像品質與真實 API 權限須待批准後測試。
