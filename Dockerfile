# 2026-11-25 - smart-voca - 학교 서버용 이미지: 화면을 빌드하고, 백엔드 하나가 화면과 API 를 8080 으로 함께 내보낸다 (이슈 #23)
# 파일 위치: Dockerfile

# 1단계: 화면(React)을 빌드한다. 결과물(dist)만 2단계로 가져가므로 최종 이미지에는 Node 가 들어가지 않는다.
FROM node:22-slim AS frontend-build
WORKDIR /build
# 의존성 파일을 먼저 복사해 설치하면, 소스만 바뀐 다음 빌드에서 설치 단계를 다시 하지 않아도 된다
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci
COPY src/frontend/ ./
RUN npm run build

# 2단계: 실행 이미지
FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/data/voca.db \
    LOG_DIR=/tmp/logs \
    AI_PROVIDER=fake \
    PAYMENT_PROVIDER=fake
# 위 환경변수: DB 는 /data, 로그는 /tmp 에만 쓴다(서버는 그 두 곳만 쓰기 허용).
# AI 선생님·결제는 실행 중 인터넷이 막혀 있어 가짜 담당자로 고정한다.
# 비밀값 SECRET_KEY 는 서버가 환경변수로 주며, 없으면 앱이 켜질 때 무작위로 만든다.

# 폴더 구조를 개발 때와 똑같이 맞춘다(앱이 프로젝트 루트를 /app 으로 계산한다)
WORKDIR /app/src/backend
COPY src/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/app ./app
COPY data/words/toeic_2000.csv /app/data/words/toeic_2000.csv
COPY --from=frontend-build /build/dist /app/src/frontend/dist

# 일반 사용자(UID 10001)로 실행한다. DB 파일을 둘 /data 의 주인을 이 사용자로 만들어 둔다.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown 10001:10001 /data
USER 10001

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
