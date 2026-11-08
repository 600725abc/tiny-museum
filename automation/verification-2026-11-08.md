# 2026-11-08 修復驗證紀錄

- 已部署程式提交：`0a9e29e`。網站：https://600725abc.github.io/tiny-museum/
- 最新部署成功：https://github.com/600725abc/tiny-museum/actions/runs/42453250138
- 手動執行成功且付費閘門阻擋：https://github.com/600725abc/tiny-museum/actions/runs/42453173784
- 本地與雲端：20 項 unittest 通過。測試 API 回應和模擬上線資料使用 mock，不是付費服務成功證據。
- 真實線上驗證：28 個公開檔案（HTML、CSS、圖片）SHA-256 與部署 artifact 一致。未宣稱目視驗收新圖片。
- 免費 The Met API 實際取得 Spoon，object ID 13502；原始來源：https://www.metmuseum.org/art/collection/search/13502 。未新增為正式館藏。
- Pages publishing source 已由 legacy 改為 workflow。`MUSEUM_PAID_ENABLED=false`，`budget.json approved=false`。
- 沒有呼叫付費 API；既有 secret 有效性、帳戶模型權限、實際圖像品質與單張實際帳單均未驗證。
- 失敗處理會建立或更新 GitHub issue 並指派 owner；本次沒有故意製造正式失敗，也未驗證 Email 或推播投遞。
- 保留原有 17 件展品和三展廳，未重寫既有展品頁。修改 dashboard 排程文字及 HISTORY 對舊定時成功紀錄的描述；舊程式備份在 legacy_curator.txt。
- 下一步：先批准一次圖片 API 測試、預留 US$0.25，確認用量和成品後再決定每月 US$3 / 最多 12 次的常態額度。這是請求預留控管，不是供應商美元硬上限。
