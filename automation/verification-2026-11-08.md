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


## 使用者批准後的一次實際全流程測試

- 執行成功：https://github.com/600725abc/tiny-museum/actions/runs/42453727958
- 新展品：https://600725abc.github.io/tiny-museum/garage-torpedo-level.html
- 由雲端自動選品、呼叫一次圖片 API、生成頁面、提交、部署、驗證成功；使用者無需中途介入。
- 新增黃銅水準尺後共 18 件館藏；30 個公開檔案線上逐檔核對通過。
- API 回報文字輸入 77 tokens、圖片輸出 824 tokens。依當前官方費率估算 US$0.025105；不是帳單結算驗證。原始 usage 保存在圖片 checkpoint 的 Git 歷史。
- 已目視生成圖片：暖光木質工作檯、黃銅器物與氣泡管符合題材方向；沒有宣稱真實歷史器物的精確復原，也未進行瀏覽器頁面視覺驗收。
- 本次一次性授權已用完；repository variable 與 budget approved 都恢復關閉。常態付費自動生成仍待批准。
- 本次成功證明單次完整鏈路可自動跑完，不代表未來永不需要維護。
