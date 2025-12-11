# Python Version: 3.12
FROM python:3.12-slim-trixie

RUN apt-get update && apt-get install -y \
    build-essential

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
