# Python Version: 3.11
# python:3.11-slim-bookworm for linux/amd64
FROM python@sha256:fc39d2e68b554c3f0a5cb8a776280c0b3d73b4c04b83dbade835e2a171ca27ef

COPY pip.conf /etc/pip.conf

# appディレクトリを作成
WORKDIR /app

# 必要なPythonライブラリのインストール
COPY requirements.txt /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# プログラムや設定ファイルなどをコピーする
COPY main.py /app
COPY modules/ /app/modules/
COPY modules_xrd/ /app/modules_xrd/
