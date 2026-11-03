FROM python:3.12-slim

# uv で高速インストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system --no-cache .

# 設定は /config にマウントする（accounts.yaml、必要なら ca.pem）
ENV MAIL_MCP_CONFIG=/config/accounts.yaml \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Tokyo

# stdio で待ち受ける（Claude Desktop / Gemini CLI が docker run -i で起動する）
ENTRYPOINT ["mail-mcp"]
