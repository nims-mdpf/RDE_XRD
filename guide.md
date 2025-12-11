# XRD用テンプレート

## 概要
XRDをご利用の方に適したテンプレートです。以下の装置メーカーに対応しています。
- DT0005: Rigaku
- DT0009: Bruker

XRDの専門家によって監修されたメタ情報を上記ファイルから自動的にRDEが抽出します。 プロットはリニアスケールとログスケールを出力します。
- Rigakuの.ras/.rasx/.TXTフォーマット、Brukerの.uxdフォーマットに対応したメタ情報の抽出、可視化を行う。(.rasフォーマットのみマルチリージョン対応。)
- MultiDataTile対応（１つの送り状で複数のデータ登録を行う）
- ファイル命名規則に従っている場合は所定のマッピングを行う
- 出力画像はlinear, logを作成する
- 代表画像はlinear（初期設定によりlogに変更可能）
- マジックネーム対応（データ名を${filename}とすると、ファイル名をデータ名にマッピングする）

## メタ情報
- [メタ情報](docs/requirement_analysis/要件定義.xlsx)

## 基本情報

### コンテナ情報
- 【コンテナ名】nims_xrd:v1.3

### テンプレート情報
- DT0005:
    - 【データセットテンプレートID】NIMS_DT0005_XRD_RIGAKU_v1.3
    - 【データセットテンプレート名日本語】XRD Rigaku データセットテンプレート
    - 【データセットテンプレート名英語】XRD Rigaku dataset-template
    - 【データセットテンプレートの説明】RigakuのXRDをご利用の方に適したモードです。ras/rasx/TXTフォーマットでデータを取得されている方がご利用いただけます。 XRDの専門家によって監修されたメタ情報をras/rasx/TXTファイルから自動的にRDEが抽出します。 プロットはリニアスケールとログスケールを出力します。
    - 【バージョン】1.3
    - 【データセット種別】加工・計測レシピ型
    - 【データ構造化】あり (システム上「あり」を選択)
    - 【取り扱い事業】NIMS研究および共同研究プロジェクト (PROGRAM)
    - 【装置名】(なし。装置情報を紐づける場合はこのテンプレートを複製し、装置情報を設定すること。)
- DT0009:
    - 【データセットテンプレートID】NIMS_DT0009_XRD_BRUKER_v1.3
    - 【データセットテンプレート名日本語】XRD Bruker データセットテンプレート
    - 【データセットテンプレート名英語】XRD Bruker dataset-template
    - 【データセットテンプレートの説明】BrukerのXRDをご利用の方に適したモードです。uxdフォーマットでデータを取得されている方がご利用いただけます。 XRDの専門家によって監修されたメタ情報をuxdファイルから自動的にRDEが抽出します。 プロットはリニアスケールとログスケールを出力します。
    - 【バージョン】1.3
    - 【データセット種別】加工・計測レシピ型
    - 【データ構造化】あり (システム上「あり」を選択)
    - 【取り扱い事業】NIMS研究および共同研究プロジェクト (PROGRAM)
    - 【装置名】(なし。装置情報を紐づける場合はこのテンプレートを複製し、装置情報を設定すること。)

### データ登録方法
- 送り状画面をひらいて入力ファイルに関する情報を入力する
- 「登録ファイル」欄に登録したいファイルをドラッグアンドドロップする。
  - 登録したいファイルのフォーマットは、\*.ras、\*.rasx、\*.TXT、\*.uxd のどれか一つとなります。
  - 複数のファイルを入力し一度に複数のデータを登録することが可能。
  - 複数のファイルを入力する場合は、「データ名」に「${filename}」と入力し「データ名」に入力ファイル名をマッピングさせることができる
- 「登録開始」ボタンを押して（確認画面経由で）登録を開始する

## 構成

### レポジトリ構成

```
xrd
├── LICENSE
├── README.md
├── container
│   ├── Dockerfile
│   ├── Dockerfile_nims (NIMSイントラ用)
│   ├── data (入出力(下記参照))
│   ├── main.py
│   ├── modules (ソースコード)
│   │   └── datasets_process.py (構造化処理の大元)
│   ├── modules_xrd (ソースコード)
│   │   ├── factory.py (設定ファイル、使用クラス取得)
│   │   ├── graph_handler.py (グラフ描画)
│   │   ├── inputfile_handler.py (入力ファイル読み込み(共通部))
│   │   ├── interfaces.py
│   │   ├── invoice_handler.py (送り状上書き)
│   │   ├── meta_handler.py (メタデータ解析(共通部))
│   │   ├── models.py
│   │   ├── rigaku (Rigaku向け)
│   │   │   ├── ras (rasフォーマット用)
│   │   │   │   ├── inputfile_handler.py (入力ファイル読み込み)
│   │   │   │   └── meta_handler.py (メタデータ解析)
│   │   │   ├── rasx (rasxフォーマット用)
│   │   │   │   ├── inputfile_handler.py (入力ファイル読み込み)
│   │   │   │   └── meta_handler.py (メタデータ解析)
│   │   │   └── txt (TXTフォーマット用)
│   │   │       ├── inputfile_handler.py (入力ファイル読み込み)
│   │   │       └── meta_handler.py (メタデータ解析)
│   │   ├── bruker (Bruker向け)
│   │   │   ├── uxd (uxdフォーマット用)
│   │   │   │   ├── inputfile_handler.py (入力ファイル読み込み)
│   │   │   │   └── meta_handler.py (メタデータ解析)
│   │   └── structured_handler.py (構造化データ解析)
│   ├── pip.conf
│   ├── pyproject.toml
│   ├── requirements-test.txt
│   ├── requirements.txt
│   ├── tests (テストコード)
│   └── tox.ini
├── docs (ドキュメント)
│   ├── manual (マニュアル)
│   └── requirement_analysis (要件定義)
├── inputdata (サンプルデータ)
│   ├── rigaku (Rigaku向け)
│   │   ├── ras_basic (rasフォーマット, invoiceモード)
│   │   ├── ras_excel_invoice (rasフォーマット, excelinvoiceモード)
│   │   ├── ras_multi_region (rasフォーマット, マルチリージョンデータ)
│   │   ├── rasx_basic (rasxフォーマット, invoiceモード)
│   │   ├── rasx_excel_invoice (rasxフォーマット, excelinvoiceモード)
│   │   ├── txt_space (TXTフォーマット, スペース区切りファイル)
│   │   └── txt_tab (TXTフォーマット, タブ区切りファイル)
│   └── bruker (Bruker向け)
│       └── uxd_basic (uxdフォーマット, invoiceモード)
└── template (テンプレート群)
     ├── rigaku (Rigaku向け)
     │   ├── batch.yaml
     │   ├── catalog.schema.json (カタログ項目定義)
     │   ├── invoice.schema.json (送り状項目定義)
     │   ├── jobs.template.yaml
     │   ├── metadata-def.json (メタデータ定義(RDE画面表示用))
     │   ├── metadata-def_rigaku_ras.json (メタデータ定義(rasフォーマット用))
     │   ├── metadata-def_rigaku_rasx.json (メタデータ定義(rasxフォーマット用))
     │   ├── metadata-def_rigaku_txt_space.json (メタデータ定義(TXTフォーマット(スペース区切り)用))
     │   ├── metadata-def_rigaku_txt_tab.json (メタデータ定義(TXTフォーマット(タブ区切り)用))
     │   └── tasksupport
     │       ├── invoice.schema.json (送り状項目定義)
     │       ├── metadata-def.json (メタデータ定義)
     │       ├── metadata-def_rigaku_ras.json (メタデータ定義(rasフォーマット用))
     │       ├── metadata-def_rigaku_rasx.json (メタデータ定義(rasxフォーマット用))
     │       ├── metadata-def_rigaku_txt_space.json (メタデータ定義(TXTフォーマット(スペース区切り)用))
     │       ├── metadata-def_rigaku_txt_tab.json (メタデータ定義(TXTフォーマット(タブ区切り)用))
     │       └── rdeconfig.yaml (設定ファイル)
     └── bruker (Bruker向け)
         ├── batch.yaml
         ├── catalog.schema.json (カタログ項目定義)
         ├── invoice.schema.json (送り状項目定義)
         ├── jobs.template.yaml
         ├── metadata-def.json (メタデータ定義(RDE画面表示用))
         ├── metadata-def_bruker_uxd.json (メタデータ定義(uxdフォーマット用))
         └── tasksupport
             ├── invoice.schema.json (送り状項目定義)
             ├── metadata-def.json (メタデータ定義)
             ├── metadata-def_bruker_uxd.json (メタデータ定義(uxdフォーマット用))
             └── rdeconfig.yaml (設定ファイル)
```

### 動作環境ファイル入出力

```
│   ├── container/data
│   │   ├── attachment
│   │   ├── inputdata
│   │   │   └── 登録ファイル欄にドラッグアンドドロップした任意のファイル
│   │   ├── invoice
│   │   │   └── invoice.json (送り状ファイル)
│   │   ├── main_image
│   │   │   └── (メイン)プロット画像
│   │   ├── meta
│   │   │   └── metadata.json (主要パラメータメタ情報ファイル)
│   │   ├── nonshared_raw
│   │   │   └── inputdataからコピーした入力ファイル
│   │   ├── other_image
│   │   │   └── (メイン以外の)プロット画像
│   │   ├── structured
│   │   │   ├── *.csv (プロット画像元データ)
│   │   │   ├── *.html (html形式のプロット画像)
│   │   │   ├── *.xml (入力ファイルから抽出したメタ情報(入力ファイルが *.rasxの場合のみ))
│   │   │   └── Profile0.txt (入力ファイルから抽出した測定データ(入力ファイルが *.rasxの場合のみ))
│   │   ├── tasksupport (テンプレート群、_rigaku_と_bruker_は背反)
│   │   │   ├── invoice.schema.json
│   │   │   ├── metadata-def.json
│   │   │   ├── metadata-def_rigaku_ras.json
│   │   │   ├── metadata-def_rigaku_rasx.json
│   │   │   ├── metadata-def_rigaku_txt_space.json
│   │   │   ├── metadata-def_rigaku_txt_tab.json
│   │   │   ├── metadata-def_bruker_uxd.json
│   │   │   └── rdeconfig.yaml
│   │   └── thumbnail
│   │       └── (サムネイル用)プロット画像
```

## データ閲覧
- データ一覧画面を開く。
- ギャラリー表示タブでは１データがタイル状に並べられている。データ名をクリックして詳細を閲覧する。
- ツリー表示タブではタクソノミーにしたがってデータを階層表示する。データ名をクリックして詳細を閲覧する。

### 動作環境
- Python: 3.12
- RDEToolKit: 1.4.2

## 入力ファイルから抽出するメタデータを追加(変更)する場合
- 入力ファイルから抽出するメタデータを追加(変更)する場合、以下のファイルを修正する必要があります。
    - metadata-def.json (必須。RDE画面表示用)
    - metadata-def_rigaku_ras.json (Rigaku社のrasフォーマットの項目を追加する場合)
    - metadata-def_rigaku_rasx.json (Rigaku社のrasxフォーマットの項目を追加する場合)
    - metadata-def_rigaku_txt_tab.json (Rigaku社のTXTフォーマット(タブ区切り)の項目を追加する場合)
    - metadata-def_rigaku_txt_space.json (Rigaku社のTXTフォーマット(スペース区切り)の項目を追加する場合)
    - metadata-def_bruker_uxd.json (Bruker社のuxdフォーマットの項目を追加する場合)
<br>

- 上記ファイルに、以下のようにオブジェクトを追加(変更)する必要があります。
```
    },
    "ras.voltage_unit": {    ← 'ras. or rasx. or txt.' + metadata.json(出力ファイル)に記述したい名称 (重複不可)
        "name": {
            "ja": "電圧単位",    ← RDEのデータ詳細画面の'日本語名'に表示したい名称
            "en": "Voltage unit"    ← RDEのデータ詳細画面の'英語名'に表示したい名称
        },
        "schema": {
            "type": "string"　← 計測ファイルに書かれているメタデータ項目の値のデータ型 (文字列: "string", 数字: "number")
        },
        "order": 31,　← metadata.json(出力ファイル)上での記述順番 (重複不可)
        "unit": "kV" ← 単位(不要の場合、この行自体不要)
        "mode": "ras形式",　← "ras形式" or "rasx形式" or "txt形式" のどれかを設定
        "originalName": "HW_XG_VOLTAGE_UNIT",　← 計測ファイルに書かれているメタデータ項目 (重複不可、metadata-def.jsonでは不要)
        "variable": 1　← 1 固定
    },
    "ras.***": {
```