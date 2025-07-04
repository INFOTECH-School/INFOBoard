## 12. CI/CD i zarządzanie wersjami

W tym rozdziale opisujemy proces ciągłej integracji i wdrażania (CI/CD) oraz zarządzanie wersjami projektu INFOBoard.

### 12.1 GitHub Actions

Pliki konfiguracyjne znajdują się w katalogu `.github/workflows/`:

* `ci.yml` – budowanie, testy i lintowanie przy każdym pull request:

  ```yaml
  name: CI
  on:
    push:
      branches: [ main ]
    pull_request:
      branches: [ main ]
  jobs:
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - name: Setup Python
          uses: actions/setup-python@v2
          with: python-version: '3.8'
        - name: Install dependencies
          run: pip install -r requirements.txt
        - name: Run linters
          run: |
            flake8 .
            npm --prefix client run lint
    test:
      runs-on: ubuntu-latest
      services:
        postgres:
          image: postgres:12
          env:
            POSTGRES_USER: postgres
            POSTGRES_DB: info_board_test
          options: >-
            --health-cmd "pg_isready -U postgres" --health-interval 10s
      steps:
        - uses: actions/checkout@v2
        - name: Setup Python
          uses: actions/setup-python@v2
          with: python-version: '3.8'
        - name: Install dependencies
          run: pip install -r requirements.txt
        - name: Migrate and test backend
          run: |
            python manage.py migrate
            pytest --maxfail=1 --disable-warnings -q
        - name: Test frontend
          run: |
            npm --prefix client install
            npm --prefix client test -- --watchAll=false
  ```

* `docker-build.yml` – budowanie i publikacja obrazów Docker (multi-arch):

  ```yaml
  name: Docker Build and Publish
  on:
    push:
      tags:
        - 'v*.*.*'
  jobs:
    build:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - name: Set up QEMU
          uses: docker/setup-qemu-action@v1
        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v1
        - name: Login to Registry
          uses: docker/login-action@v2
          with:
            registry: ghcr.io
            username: ${{ github.actor }}
            password: ${{ secrets.GITHUB_TOKEN }}
        - name: Build and push
          uses: docker/build-push-action@v2
          with:
            context: .
            push: true
            tags: ghcr.io/${{ github.repository }}/info-board:${{ github.ref_name }}
            platforms: linux/amd64,linux/arm64
  ```

### 12.2 Zarządzanie wydaniami (Releases)

* **Tagowanie**: używamy semantycznego wersjonowania (vMAJOR.MINOR.PATCH).
* **Draft Release**: po utworzeniu tagu `vX.Y.Z` GitHub automatycznie tworzy draft release.
* **Changelog**: generowany z commitów za pomocą narzędzia `github-changelog-generator`.

### 12.3 Makefile

W głównym katalogu projektu znajduje się `Makefile` z przydatnymi celami:

```makefile
.PHONY: install test lint docker-build migrate

install:
	pip install -r requirements.txt && npm --prefix client install

test:
	pytest && npm --prefix client test -- --watchAll=false

lint:
	flake8 . && npm --prefix client run lint

docker-build:
	docker buildx build --platform linux/amd64,linux/arm64 -t info-board:latest .

migrate:
	python manage.py makemigrations && python manage.py migrate
```

### 12.4 Environments i Secrets

* **Production**, **Staging**, **Development** w GitHub:

  * Każde środowisko posiada własne zmienne środowiskowe i klucze.
  * Sekrety (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`) przechowywane w GitHub Secrets.

---
