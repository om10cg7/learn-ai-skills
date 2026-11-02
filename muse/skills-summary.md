# このチャットで要約した Skill 一覧

対象：このサイドチャットで Instagram リンクを送って要約した投稿（2026-10-26〜2026-10-31）。
learn-ui の既存ノートと照合済み。重複が多いものは末尾に「常連」として整理。

## デザイン系

1. **Claude デザイン Skill 3選**（@haru.ai.news）
   - frontend-design（Anthropic公式、AIっぽい見た目を避ける）
   - Impeccable（タイポ・余白・色をプロ水準に整える）
   - Taste Skill（優れたサイトから学習）
   - 番外：Playwright MCP（ブラウザで画面確認して自己修正）
   - ※ learn-ui にノートあり：`notes/2026-10-27-claude-design-skills.md`

2. **プロダクトデザイナー向け Claude Skill 5選**（@vamshi.work）
   - UI/UX Pro Max（Claudeにデザイン判断力を与える）
   - Frontend Design（上記と重複）
   - Emil Kowalski（アニメーション／イージング論ベースのモーション Skill）
   - App Store Design（iOSストア用スクショ生成）
   - gstack（デザインを0〜10点で採点、AIっぽさを指摘）
   - おすすめ導入順：Pro Max → Emil → gstack

## 動画・アニメーション系

3. **無料 Claude アニメーション Skill 3選**（@aevyvideoschool）
   - Three.js（映画風3D商品CM、分解ビュー）
   - Remotion（ドキュメンタリー風モーショングラフィクス、地図・グラフ）
   - GSAP（高度な2Dアニメーション）
   - ※ learn-ui にノートあり（4本まとめの一部）：`notes/2026-10-28-claude-video-skills.md`

4. **Claude 動画差別化 Skill 5選**（@mao_hiiro、いずれも GitHub 公開）
   - HyperFrames（HeyGen、HTML→モーショングラフィクス）
   - onetake（ナレーション付き動画、広告／YouTube向け）
   - Collage B-roll（半調コラージュが組み上がる、Gemini使用）
   - Claude Animation Base（手描き風、Claude Codeマスコット主演）
   - Lemo-Opuscar（コード生成のみで43種の動画スタイル）
   - ※ 同上ノートに収録

5. **Claude Motion 発表カルーセル**（@zeeuiux）
   - プロンプト／PDFから約30秒の解説動画。動画生成モデルではなく Claude がコードでアニメーションを書くため文字・数字が編集可能。MP4書き出し可
   - 注意：検証済み情報では Team／Enterprise 向けベータ、個人の Free／Pro／Max では使えない。ナレーションは非対応

6. **Claude を動画編集者にする 5パス方式**（@zeeuiux）
   - 01 Transcribe（単語単位タイムスタンプ）→ 02 Cut-out（背景除去）→ 03 Captions（音声同期字幕）→ 04 Motion（発言に合わせたグラフィクス）→ 05 Sound（効果音、-14 LUFS）

7. **Claude Opus 5.5 × Remotion 8ステップ**（@ai.byarsh）
   - Claude Desktop → Codeタブ（Pro以上）→ Remotion Skill導入 → フォルダ構成（Assets／Raw footage／Reference）→ プロンプト → 絵コンテ確認 → 言葉で修正 → Prompt＞Preview＞Feedback の反復。ElevenLabs／Whisperとも連携可

8. **ブランドデザインのクローン＋モーション 6ステップ**（@charliehills）
   - ブランドの実コードを Claude Code に読ませてスタイルファイル化し、その下にモーション指示を貼る。Stripe風アニメーション16種を作成

## 運用・自動化・知識系

9. **official-mcp-servers カタログ**（VoltAgent、テキストで依頼）
   - 公式 MCP サーバー280以上の一覧（Stripe、Supabase、Figma、Notion、Cloudflare、Google 等）。AIエージェントを DB・決済・ドキュメントへ接続する用途

10. **Google Artemis**（@igao.ia）
    - AIエージェントが実機 Android を操作する無料 OSS（MCP連携）。Flash／Pro の2モード、アプリテスト向け
    - 確認済み：google 公式 GitHub あり。ただし ADB／USBデバッグ前提でタップ・入力・インストールまで可能なため、検証機＋テストアカウント推奨

11. **Claude Code 連携 5選**（@kakeru_kakerujj）
    - Browser Use、Skill Creator、Canva、HyperFrames、Zapier

12. **Instagram Agent Skill 13個セット**（@almantiqi3、GitHub: Jakeschincariol/instagram-agent-skill）
    - /ig-reel（フック26公式で台本）、/ig-profile（プロフィール採点・書き直し）、/ig-plan（週間投稿計画）、/ig-viral（バズリール分析）ほか
    - 訂正済み：実際は下書き作成のみ。Instagram へ接続せず、投稿・コメント・DMは本人が行う

13. **無料 Claude Skill 99個／6リポジトリ**（@gut1n）
    - Marketing 52、Social Media 17、Design 9、Finance 8（Anthropic公式）、Legal 9（同）、Documents 4（同、DOCX／PDF／PPTX／XLSX）

14. **Claude に入れるもの 42個**（@charliehills、60日分の利用ログから）
    - BUILD & TEST 8（Superpowers、gstack、graphify、Playwright 等）
    - DESIGN & ANIMATE 9（Figma、ui-ux-pro-max、impeccable、taste-skill、HyperFrames、Remotion 等）
    - GROW 8、MAKE 8、RUN 9（Notion が接続最多 242回）
    - 助言：全部入れず、必要な部門から1個ずつ

15. **Anatomy Skill**（@dannystuart、無料）
    - アイデアを一言で伝えると機械を部品ごとに描く対話型図解を生成（レコードプレーヤーは84部品）。`/anatomy` で実行。生成は低速（簡易でも最大1時間ほど）が前提

16. **Graphify + Obsidian + Claude Code**（@divyannshisharma）
    - 文書群を知見・つながり・話題グループへ地図化（実験：171ページ→591知見／685接続／67グループ）し、`graphify --obsidian` で Obsidian ノート化して「第二の脳」にする
    - 追記（@gut1n版、2026-11-02受信・同テーマの別投稿）：コマンドは `/graphify . --obsidian`。出力は HTMLマップ／JSON／Vaultフォルダ（知見ごとに1ノート、各ノートに出典と接続を明記）。Vaultは分離・マージ・手動コピーの3択。地図への直接質問は `/graphify query ...` でキーワード検索ではなく関係をたどる

17. **Claude Code 神機能 7選**（@tatsu.insta_ai）
    - カレンダー連携、リモートコントロール、Claude in Chrome、Meta API連携、UTAGE連携、Codexプラグイン連携、Claude Skills
    - ※「Skillの作り方で精度38%→98%」という数字は動画内の主張で根拠未確認

18. **Claude Code × Muse 連携で AI 動画**（@kou_ai.in_sta）
    - 招待コードで期限なし10億トークンという特典自体は実在を確認済み。ただし動画は1本約10秒・同時生成に上限があり「無限に作れる」は誇張。本人は既存ユーザーなので新規招待は対象外

19. **自分専用 JARVIS 構築 4パーツ**（@ibraviz.ai）
    - Brain＝Claude Code＋仕事ごとの小さい Skill ファイル、Memory＝Obsidian Vault、Voice＝ローカル音声入出力、Face＝プロンプト1つで作る HUD。ループは「話す→振り分け→実行→記憶」

20. **間取り図→実写風ウォークスルー動画**（@ohneis652、Skillではなくワークフロー）
    - Claude で Blender に実寸モデル化 → カメラ経路を引く → 部屋ごとに静止画で素材を固定 → Seedance 2.5 が動きをそのままに見た目だけ差し替え（間取りは動画モデルが作らない）

21. **JARVIS OS 2.0**（@juanbertorello.ia、2026-11-02追加）
    - 19番の JARVIS 構築とほぼ同型の5ピース構成：Engine＝Claude Code、Memory＝Obsidian、Voice＝ローカル音声（Whisper／Kokoro、音声は端末外に出ない）、Brain＝Skills（最大10個をボタン化）、Face＝2つのパネル
    - 新要素は Step 5：**Mailerfind** を MCP コネクタで接続し、見込み客探し。「コルドバの不動産会社を探して」で企業の公開メール・Web・電話を Vault に保存。送信は承認なしに行わない、個人の調査用ではない、無料トライアルあり

22. **UIワークフロー向け Claude MCP ツール 7選**（@sanskaar.ai、2026-11-02追加）
    - Figma MCP（デザイン→コード、推測でなく実デザインを読む）、shadcn MCP（UIコンポーネント検索・導入）、Playwright MCP（実ページを開いて操作・撮影・修正）、Chrome DevTools MCP（コンソール／ネットワーク／CSS／Lighthouseでデバッグ）、21st.dev Magic MCP（プロンプトから React コンポーネント生成）、Penpot MCP（オープンソース版デザイン→コード）、Context7 MCP（現行バージョンのドキュメントを引く）
    - MCP自体は「AI版 USB-C」という例えで紹介。なしだと Claude が推測し、ありだと Figma・実ページ・最新ドキュメントを読める、という対比

## 常連（複数投稿に繰り返し登場）

frontend-design、Taste Skill、Impeccable、UI/UX Pro Max、gstack、HyperFrames、Remotion、Playwright、graphify

## 番外（Skillが主題ではない要約）

- デザインリソース12選（@codewithnishant）：godly のみ learn-ui 既存ノートと重複、他11件は新規
- Lightroom マスキング講座（@mikita.yo）
- Arcads で作った LinkedIn Premium 広告デモ（@riki.bosso）
