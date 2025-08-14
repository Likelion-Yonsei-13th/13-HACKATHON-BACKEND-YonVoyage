# 13-HACKATHON-BACKEND-YonVoyage

## 🚀 Clone 후 할 일(초기 세팅)

dev 브랜치로 checkout

```bash
    checkout dev
```

### 1. 가상환경 생성 및 실행

```bash
# 가상환경 생성
python -m venv myvenv

# (Mac/Linux)
source myvenv/bin/activate

# (Windows)
myvenv\Scripts\activate
```

### 2. requirements 설치

```bash
pip install -r requirements.txt
```

### 3. 로컬 MySQL DB 생성

```sql
CREATE DATABASE pixpl_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 4. 환경변수 설정

manage.py와 같은 위치에 .env 파일 생성:

```env
DEBUG=True
DB_PASSWORD=본인비번
```

운영 환경에서는 DEBUG=False로 변경

### 5. 마이그레이션 적용 및 superuser 만들기(로컬용)

```bash
cd pixpl
python manage.py migrate
python manage.py createsuperuser
```

### 6. 서버 실행

```bash
python manage.py runserver
```

## 📄 Swagger API 문서

개발 서버 실행 후 아래 주소에서 Swagger UI 접속 가능:

Swagger UI: http://127.0.0.1:8000/swagger/
주의: Swagger는 DEBUG=True일 때만 접근 가능하게 설정되어 있음

## 🛠 개발 규칙

### 💡 개발 순서

1. dev 브랜치 최신 코드 가져오기

```bash
git checkout dev
git pull origin dev
```

2. 새 기능 브랜치 생성

```bash
git checkout -b feat/기능이름-본인이름
```

3. 개발 및 테스트

4. 변경 사항 커밋 & 푸시

5. PR 생성 (dev 브랜치로)

### 브랜치 네이밍

| 타입       | 설명             | 예시                        |
| ---------- | ---------------- | --------------------------- |
| `feat`     | 새로운 기능 추가 | `feat/user-auth-sebin`      |
| `fix`      | 버그 수정        | `fix/login-error-sebin`     |
| `refactor` | 코드 리팩토링    | `refactor/user-model-sebin` |
| `docs`     | 문서 수정        | `docs/update-readme`        |

형식: 타입/기능이름-본인이름

### 새로운 패키지를 설치한 경우:

```bash
pip freeze > requirements.txt
```

후, requirements.txt를 커밋

.env 파일은 절대 Git에 올리지 않기 (.gitignore에 포함되어있음)
