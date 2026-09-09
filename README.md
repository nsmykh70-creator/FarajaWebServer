# Faraja WebServer

[![Release](https://img.shields.io/github/v/release/nsmykh70-creator/FarajaWebServer)](https://github.com/nsmykh70-creator/FarajaWebServer/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows-blue)](https://github.com/nsmykh70-creator/FarajaWebServer)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](MiniServer.py)

**Faraja WebServer** — портативная локальная среда веб-разработки для Windows.
Всё в одном EXE: веб-сервер, базы данных, PHP, Node.js, SSL, Docker-контроль.

![Faraja WebServer](docs/logo.png)

**[⬇ Скачать FarajaWebServer.exe](https://github.com/nsmykh70-creator/FarajaWebServer/releases/latest/download/FarajaWebServer.exe)** ·
**[🌐 Сайт проекта](https://nsmykh70-creator.github.io/FarajaWebServer/)**

---

## Что внутри

| Сервис     | Назначение                          | Порт |
|------------|-------------------------------------|------|
| Apache     | Веб-сервер (HTTP)                   | 8080 |
| MariaDB    | База данных, совместимая с MySQL    | 3306 |
| PHP        | Серверный язык (FastCGI)            | 9074 |
| PostgreSQL | Продвинутая СУБД                    | 5432 |
| Redis      | Хранилище «ключ-значение» в памяти  | 6379 |
| Nginx      | Обратный прокси, балансировщик      | 80   |
| Node.js    | JavaScript / TypeScript скрипты     | —    |
| Docker     | Проверка наличия и статуса          | —    |
| phpMyAdmin | Веб-панель управления базами        | —    |

Плюс: локальный SSL (mkcert + HTTPS), мультисайты, планировщик задач,
файловый менеджер с редактором кода, SQL-редактор, интерфейс на 6 языках
(RU / EN / ES / DE / FR / ZH), сворачивание в трей.

## Быстрый старт

1. Скачайте `FarajaWebServer.exe` из [релизов](https://github.com/nsmykh70-creator/FarajaWebServer/releases/latest) и запустите.
2. При первом запуске отметьте нужные компоненты и нажмите «Установить».
3. Нажмите **«ЗАПУСТИТЬ ВСЕ»** — все бейджи станут зелёными.
4. Откройте в браузере `http://127.0.0.1:8080/` — стартовая страница.
5. Положите проект в папку `www/` (например `www/mysite/index.php`) —
   он доступен по адресу `http://127.0.0.1:8080/mysite/`.

Ничего в систему не устанавливается: все компоненты живут в папке `runtime/`
рядом с программой.

## Сборка из исходников

```bat
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --icon "assets/logo.ico" ^
  --name "FarajaWebServer" ^
  --add-data "config;config" --add-data "www;www" --add-data "assets;assets" ^
  --add-data "components.json;." --add-data "requirements.txt;." ^
  --clean MiniServer.py
```

Требуется Python 3.12, Windows 10/11.

## Структура

```
MiniServer.py      — весь исходный код приложения
components.json    — ссылки и версии скачиваемых компонентов
assets/            — логотип и иконки
www/               — корневая папка сайтов
config/            — порты, сайты, задачи, язык (создаётся при запуске)
docs/              — лендинг проекта (GitHub Pages)
```

## Лицензия

MIT — см. [LICENSE](LICENSE).

---

## English (short)

**Faraja WebServer** is a portable local web-development environment for Windows:
Apache, MariaDB, PHP, PostgreSQL, Redis, Nginx, Node.js, Docker status check,
local SSL, multi-site hosting, task scheduler, file manager with code editor,
SQL editor and a 6-language UI — all in a single EXE, nothing installed into the system.

Download: [FarajaWebServer.exe (latest release)](https://github.com/nsmykh70-creator/FarajaWebServer/releases/latest/download/FarajaWebServer.exe)
