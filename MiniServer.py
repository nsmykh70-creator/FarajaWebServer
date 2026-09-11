import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import json, os, shutil, socket, subprocess, sys, threading, time, webbrowser, zipfile, re, atexit, signal
from urllib.parse import urljoin
import requests, pystray
from PIL import Image, ImageDraw, ImageTk

if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).resolve().parent
    BUNDLE_ROOT = Path(sys._MEIPASS)
else:
    APP_ROOT = Path(__file__).resolve().parent
    BUNDLE_ROOT = APP_ROOT

def seed(rel):
    dst, src = APP_ROOT / rel, BUNDLE_ROOT / rel
    if dst.exists() or not src.exists(): return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)
    return dst

CONFIG_FILE=seed("config/server.json")
if getattr(sys, "frozen", False):
    bundled_manifest = BUNDLE_ROOT / "components.json"
    dst_manifest = APP_ROOT / "components.json"
    if bundled_manifest.exists():
        dst_manifest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(bundled_manifest), str(dst_manifest))
MANIFEST_FILE = APP_ROOT / "components.json"
WWW=seed("www"); ICON=seed("assets/MiniServer.ico")
LOGO_PNG=seed("assets/logo.png")
_LOGO_ICO=seed("assets/logo.ico")
if _LOGO_ICO.exists(): ICON=_LOGO_ICO
def tray_image():
    if LOGO_PNG.exists():
        return str(LOGO_PNG)
    return str(ICON)
DONATE = {
    "BTC": ("assets/donate_btc.png", "bc1q48l0mfvrs6kza5xs6qmzagatmpelrxzyqcwfhpz"),
    "ETH": ("assets/donate_eth.png", "0x6889fD4d5B688d6E3c4b7E5A2B1D6E8F2C3A4b5D"),
    "TRX": ("assets/donate_trx.png", "TN7V3t8EKjRTJFXNJwMjYpLqHGSQN7BTyv"),
}
for _c in DONATE:
    DONATE[_c] = (seed(DONATE[_c][0]), DONATE[_c][1])
del _c
RUNTIME=APP_ROOT/"runtime"; DOWNLOADS=APP_ROOT/"downloads"; LOGS=APP_ROOT/"logs"; PMA=WWW/"phpmyadmin"
for x in (RUNTIME,DOWNLOADS,LOGS,WWW,APP_ROOT/"tmp"): x.mkdir(parents=True,exist_ok=True)

DEFAULT={"apache_port":8080,"mariadb_port":3306,"php_cgi_port":9074,"postgresql_port":5432,"redis_port":6379,"nginx_port":80}
try: CONFIG={**DEFAULT,**json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
except Exception:
    CONFIG=DEFAULT.copy(); CONFIG_FILE.parent.mkdir(parents=True,exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(CONFIG,indent=2),encoding="utf-8")

THEME = {
    # Unified Faraja visual system — based on the Settings reference screen.
    "bg": "#071321",
    "bg_card": "#0b1c2d",
    "bg_elevated": "#0f2438",
    "bg_input": "#132a40",
    "border": "#1d4261",
    "border_light": "#2a587d",
    "accent": "#168cff",
    "accent_hover": "#3aa0ff",
    "accent_active": "#0b6ed6",
    "success": "#16d68a",
    "success_dim": "#0b9f66",
    "danger": "#ff5b68",
    "danger_dim": "#c83f4e",
    "warning": "#ff9f1a",
    "warning_dim": "#d97908",
    "info": "#28b7ff",
    "text": "#eef6ff",
    "text_dim": "#a8bfd5",
    "text_muted": "#6f8ba5",
    "white": "#ffffff",
    "entry_bg": "#eaf0f5",
    "entry_fg": "#17202a",
    "font_family": "Segoe UI",
}

LANGUAGES = {
    "ru": {"flag": "\U0001F1F7\U0001F1FA", "name": "Русский"},
    "en": {"flag": "En", "name": "English"},
    "es": {"flag": "\U0001F1EA\U0001F1F8", "name": "Español"},
    "de": {"flag": "\U0001F1E9\U0001F1EA", "name": "Deutsch"},
    "fr": {"flag": "\U0001F1EB\U0001F1F7", "name": "Français"},
    "zh": {"flag": "\U0001F1E8\U0001F1F3", "name": "中文"},
}

LOCALES = {
    "app_title": {"ru": "FarajaWebServer", "en": "FarajaWebServer", "es": "FarajaWebServer", "de": "FarajaWebServer", "fr": "FarajaWebServer", "zh": "FarajaWebServer"},
    "app_subtitle": {"ru": "Локальная среда разработки", "en": "Local development environment", "es": "Entorno de desarrollo local", "de": "Lokale Entwicklungsumgebung", "fr": "Environnement de développement local", "zh": "本地开发环境"},
    "start_all": {"ru": "ЗАПУСТИТЬ ВСЕ", "en": "START ALL", "es": "INICIAR TODO", "de": "ALLE STARTEN", "fr": "TOUT DÉMARRER", "zh": "全部启动"},
    "stop_all": {"ru": "ОСТАНОВИТЬ ВСЕ", "en": "STOP ALL", "es": "DETENER TODO", "de": "ALLE STOPPEN", "fr": "TOUT ARRÊTER", "zh": "全部停止"},
    "restart_all": {"ru": "ПЕРЕЗАПУСТИТЬ ВСЕ", "en": "RESTART ALL", "es": "REINICIAR TODO", "de": "ALLE NEUSTARTEN", "fr": "TOUT REDÉMARRER", "zh": "全部重启"},
    "start": {"ru": "СТАРТ", "en": "START", "es": "INICIAR", "de": "STARTEN", "fr": "DÉMARRER", "zh": "启动"},
    "stop": {"ru": "СТОП", "en": "STOP", "es": "DETENER", "de": "STOPPEN", "fr": "ARRÊTER", "zh": "停止"},
    "restart": {"ru": "ПЕРЕЗАПУСК", "en": "RESTART", "es": "REINICIAR", "de": "NEUSTART", "fr": "REDÉMARRER", "zh": "重启"},
    "running": {"ru": "РАБОТАЕТ", "en": "RUNNING", "es": "EJECUTANDO", "de": "LÄUFT", "fr": "EN EXÉCUTION", "zh": "运行中"},
    "stopped": {"ru": "ОСТАНОВЛЕН", "en": "STOPPED", "es": "DETENIDO", "de": "GESTOPPT", "fr": "ARRÊTÉ", "zh": "已停止"},
    "apache": {"ru": "Apache HTTP Server", "en": "Apache HTTP Server", "es": "Apache HTTP Server", "de": "Apache HTTP Server", "fr": "Apache HTTP Server", "zh": "Apache HTTP 服务器"},
    "mariadb": {"ru": "База данных MariaDB", "en": "MariaDB Database", "es": "Base de datos MariaDB", "de": "MariaDB Datenbank", "fr": "Base de données MariaDB", "zh": "MariaDB 数据库"},
    "php": {"ru": "PHP FastCGI", "en": "PHP FastCGI", "es": "PHP FastCGI", "de": "PHP FastCGI", "fr": "PHP FastCGI", "zh": "PHP FastCGI"},
    "postgresql": {"ru": "PostgreSQL", "en": "PostgreSQL", "es": "PostgreSQL", "de": "PostgreSQL", "fr": "PostgreSQL", "zh": "PostgreSQL"},
    "redis": {"ru": "Redis", "en": "Redis", "es": "Redis", "de": "Redis", "fr": "Redis", "zh": "Redis"},
    "nginx": {"ru": "Nginx", "en": "Nginx", "es": "Nginx", "de": "Nginx", "fr": "Nginx", "zh": "Nginx"},
    "docker": {"ru": "Docker", "en": "Docker", "es": "Docker", "de": "Docker", "fr": "Docker", "zh": "Docker"},
    "open_localhost": {"ru": "Открыть Localhost", "en": "Open Localhost", "es": "Abrir Localhost", "de": "Localhost öffnen", "fr": "Ouvrir Localhost", "zh": "打开 Localhost"},
    "phpmyadmin": {"ru": "phpMyAdmin", "en": "phpMyAdmin", "es": "phpMyAdmin", "de": "phpMyAdmin", "fr": "phpMyAdmin", "zh": "phpMyAdmin"},
    "open_www": {"ru": "Открыть www", "en": "Open www", "es": "Abrir www", "de": "www öffnen", "fr": "Ouvrir www", "zh": "打开 www"},
    "setup_ssl": {"ru": "Настроить SSL", "en": "Setup SSL", "es": "Configurar SSL", "de": "SSL einrichten", "fr": "Configurer SSL", "zh": "设置 SSL"},
    "run_script": {"ru": "Запустить скрипт", "en": "Run Script", "es": "Ejecutar script", "de": "Skript ausführen", "fr": "Exécuter le script", "zh": "运行脚本"},
    "clear_logs": {"ru": "Очистить логи", "en": "Clear Logs", "es": "Limpiar registros", "de": "Logs löschen", "fr": "Effacer les logs", "zh": "清除日志"},
    "tab_main": {"ru": "Основное", "en": "Main", "es": "Principal", "de": "Haupt", "fr": "Principal", "zh": "主要"},
    "tab_extra": {"ru": "Дополнительно", "en": "Advanced", "es": "Adicional", "de": "Erweitert", "fr": "Avancé", "zh": "高级"},
    "tab_system": {"ru": "Система", "en": "System", "es": "Sistema", "de": "System", "fr": "Système", "zh": "系统"},
    "tab_apache_err": {"ru": "Apache", "en": "Apache ", "es": " Apache", "de": "Apache ", "fr": " Apache", "zh": "Apache 错误"},
    "tab_php_err": {"ru": " PHP", "en": "PHP ", "es": " PHP", "de": "PHP ", "fr": " PHP", "zh": "PHP 错误"},
    "tab_mariadb_err": {"ru": " MariaDB", "en": "MariaDB ", "es": " MariaDB", "de": "MariaDB ", "fr": " MariaDB", "zh": "MariaDB 错误"},
    "tab_process": {"ru": "Процессы", "en": "Process", "es": "Proceso ", "de": "Prozess", "fr": "Processus", "zh": "进程 / 初始化"},
    "tab_files": {"ru": "Файлы", "en": "Files", "es": "Archivos", "de": "Dateien", "fr": "Fichiers", "zh": "文件"},
    "tab_sql": {"ru": "SQL", "en": "SQL", "es": "SQL", "de": "SQL", "fr": "SQL", "zh": "SQL"},
    "tab_sites": {"ru": "Сайты", "en": "Sites", "es": "Sitios", "de": "Sites", "fr": "Sites", "zh": "站点"},
    "tab_tasks": {"ru": "Задачи", "en": "Tasks", "es": "Tareas", "de": "Aufgaben", "fr": "Tâches", "zh": "任务"},
    "btn_refresh": {"ru": "Обновить", "en": "Refresh", "es": "Actualizar", "de": "Aktualisieren", "fr": "Actualiser", "zh": "刷新"},
    "btn_new_folder": {"ru": "Новая папка", "en": "New Folder", "es": "Nueva carpeta", "de": "Neuer Ordner", "fr": "Nouveau dossier", "zh": "新建文件夹"},
    "btn_new_file": {"ru": "Новый файл", "en": "New File", "es": "Nuevo archivo", "de": "Neue Datei", "fr": "Nouveau fichier", "zh": "新建文件"},
    "btn_edit": {"ru": "Редактировать", "en": "Edit", "es": "Editar", "de": "Bearbeiten", "fr": "Modifier", "zh": "编辑"},
    "btn_delete": {"ru": "Удалить", "en": "Delete", "es": "Eliminar", "de": "Löschen", "fr": "Supprimer", "zh": "删除"},
    "btn_execute": {"ru": "Выполнить", "en": "Execute", "es": "Ejecutar", "de": "Ausführen", "fr": "Exécuter", "zh": "执行"},
    "btn_clear": {"ru": "Очистить", "en": "Clear", "es": "Limpiar", "de": "Leeren", "fr": "Effacer", "zh": "清除"},
    "btn_add_site": {"ru": "Добавить сайт", "en": "Add Site", "es": "Agregar sitio", "de": "Site hinzufügen", "fr": "Ajouter un site", "zh": "添加站点"},
    "btn_remove": {"ru": "Удалить", "en": "Remove", "es": "Eliminar", "de": "Entfernen", "fr": "Supprimer", "zh": "删除"},
    "btn_open_folder": {"ru": "Открыть папку", "en": "Open Folder", "es": "Abrir carpeta", "de": "Ordner öffnen", "fr": "Ouvrir le dossier", "zh": "打开文件夹"},
    "btn_add_task": {"ru": "Добавить задачу", "en": "Add Task", "es": "Agregar tarea", "de": "Aufgabe hinzufügen", "fr": "Ajouter une tâche", "zh": "添加任务"},
    "btn_run_now": {"ru": "Запустить", "en": "Run Now", "es": "Ejecutar ahora", "de": "Jetzt ausführen", "fr": "Exécuter maintenant", "zh": "立即运行"},
    "col_site": {"ru": "Сайт", "en": "Site", "es": "Sitio", "de": "Site", "fr": "Site", "zh": "站点"},
    "col_domain": {"ru": "Домен", "en": "Domain", "es": "Dominio", "de": "Domain", "fr": "Domaine", "zh": "域名"},
    "col_root": {"ru": "Корень", "en": "Root", "es": "Raíz", "de": "Root", "fr": "Racine", "zh": "根目录"},
    "col_port": {"ru": "Порт", "en": "Port", "es": "Puerto", "de": "Port", "fr": "Port", "zh": "端口"},
    "col_task": {"ru": "Задача", "en": "Task", "es": "Tarea", "de": "Aufgabe", "fr": "Tâche", "zh": "任务"},
    "col_schedule": {"ru": "Расписание", "en": "Schedule", "es": "Horario", "de": "Zeitplan", "fr": "Horaire", "zh": "计划"},
    "col_command": {"ru": "Команда", "en": "Command", "es": "Comando", "de": "Befehl", "fr": "Commande", "zh": "命令"},
    "col_status": {"ru": "Статус", "en": "Status", "es": "Estado", "de": "Status", "fr": "Statut", "zh": "状态"},
    "sql_engine": {"ru": "Движок:", "en": "Engine:", "es": "Motor:", "de": "Engine:", "fr": "Moteur :", "zh": "引擎："},
    "sql_user": {"ru": "Пользователь:", "en": "User:", "es": "Usuario:", "de": "Benutzer:", "fr": "Utilisateur :", "zh": "用户："},
    "sql_pass": {"ru": "Пароль:", "en": "Pass:", "es": "Contraseña:", "de": "Passwort:", "fr": "Mot de passe :", "zh": "密码："},
    "sql_editor": {"ru": "SQL Редактор", "en": "SQL Editor", "es": "Editor SQL", "de": "SQL Editor", "fr": "Éditeur SQL", "zh": "SQL 编辑器"},
    "sql_results": {"ru": "Результаты", "en": "Results", "es": "Resultados", "de": "Ergebnisse", "fr": "Résultats", "zh": "结果"},
    "docker_not_found": {"ru": "Docker не установлен", "en": "Docker not found", "es": "Docker no encontrado", "de": "Docker nicht gefunden", "fr": "Docker non trouvé", "zh": "未找到 Docker"},
    "docker_install_offer": {"ru": "Хотите установить Docker?", "en": "Would you like to install Docker?", "es": "¿Desea instalar Docker?", "de": "Möchten Sie Docker installieren?", "fr": "Voulez-vous installer Docker ?", "zh": "是否安装 Docker？"},
    "docker_install_btn": {"ru": "Установить Docker", "en": "Install Docker", "es": "Instalar Docker", "de": "Docker installieren", "fr": "Installer Docker", "zh": "安装 Docker"},
    "docker_running": {"ru": "Docker работает", "en": "Docker is running", "es": "Docker está ejecutándose", "de": "Docker läuft", "fr": "Docker est en cours d'exécution", "zh": "Docker 正在运行"},
    "docker_stopped": {"ru": "Docker остановлен", "en": "Docker is stopped", "es": "Docker está detenido", "de": "Docker ist gestoppt", "fr": "Docker est arrêté", "zh": "Docker 已停止"},
    "help_btn": {"ru": "Помощь", "en": "Help", "es": "Ayuda", "de": "Hilfe", "fr": "Aide", "zh": "帮助"},
    "doc_title": {"ru": "Документация MiniServer", "en": "MiniServer Documentation", "es": "Documentación de MiniServer", "de": "MiniServer Dokumentation", "fr": "Documentation MiniServer", "zh": "MiniServer 文档"},
    "first_run_title": {"ru": "Первый запуск MiniServer", "en": "First Run Setup", "es": "Configuración inicial", "de": "Ersteinrichtung", "fr": "Configuration initiale", "zh": "首次运行设置"},
    "first_run_welcome": {"ru": "Добро пожаловать! Выберите компоненты для установки:", "en": "Welcome! Select components to install:", "es": "¡Bienvenido! Seleccione los componentes a instalar:", "de": "Willkommen! Wählen Sie die zu installierenden Komponenten:", "fr": "Bienvenue ! Sélectionnez les composants à installer :", "zh": "欢迎！选择要安装的组件："},
    "first_run_components": {"ru": "Компоненты", "en": "Components", "es": "Componentes", "de": "Komponenten", "fr": "Composants", "zh": "组件"},
    "first_run_download_dir": {"ru": "Папка с загруженными модулями:", "en": "Downloaded modules folder:", "es": "Carpeta de módulos descargados:", "de": "Ordner für heruntergeladene Module:", "fr": "Dossier des modules téléchargés :", "zh": "已下载模块文件夹："},
    "first_run_browse": {"ru": "Обзор...", "en": "Browse...", "es": "Examinar...", "de": "Durchsuchen...", "fr": "Parcourir...", "zh": "浏览..."},
    "first_run_install": {"ru": "Установить", "en": "Install", "es": "Instalar", "de": "Installieren", "fr": "Installer", "zh": "安装"},
    "first_run_skip": {"ru": "Пропустить", "en": "Skip", "es": "Omitir", "de": "Überspringen", "fr": "Ignorer", "zh": "跳过"},
    "confirm_delete": {"ru": "Удалить", "en": "Delete", "es": "Eliminar", "de": "Löschen", "fr": "Supprimer", "zh": "删除"},
    "confirm_delete_site": {"ru": "Удалить сайт '{name}'?", "en": "Remove site '{name}'?", "es": "¿Eliminar sitio '{name}'?", "de": "Site '{name}' entfernen?", "fr": "Supprimer le site '{name}' ?", "zh": "删除站点 '{name}'？"},
    "confirm_delete_task": {"ru": "Удалить задачу '{name}'?", "en": "Remove task '{name}'?", "es": "¿Eliminar tarea '{name}'?", "de": "Aufgabe '{name}' entfernen?", "fr": "Supprimer la tâche '{name}' ?", "zh": "删除任务 '{name}'？"},
    "status_ready": {"ru": "Готов", "en": "Ready", "es": "Listo", "de": "Bereit", "fr": "Prêt", "zh": "就绪"},
    "status_starting": {"ru": "Запуск {svc}...", "en": "Starting {svc}...", "es": "Iniciando {svc}...", "de": "Starte {svc}...", "fr": "Démarrage de {svc}...", "zh": "启动 {svc}..."},
    "status_stopping": {"ru": "Остановка {svc}...", "en": "Stopping {svc}...", "es": "Deteniendo {svc}...", "de": "Stoppe {svc}...", "fr": "Arrêt de {svc}...", "zh": "停止 {svc}..."},
    "error": {"ru": "Ошибка", "en": "Error", "es": "Error", "de": "Fehler", "fr": "Erreur", "zh": "错误"},
    "error_port_busy": {"ru": "Порт {port} все еще занят", "en": "Port {port} is still busy", "es": "Puerto {port} sigue ocupado", "de": "Port {port} ist noch belegt", "fr": "Le port {port} est toujours occupé", "zh": "端口 {port} 仍被占用"},
    "all_installed": {"ru": "Все компоненты установлены", "en": "All components installed", "es": "Todos los componentes instalados", "de": "Alle Komponenten installiert", "fr": "Tous les composants installés", "zh": "所有组件已安装"},
    "missing_components": {"ru": "Отсутствующие компоненты:", "en": "Missing components:", "es": "Componentes faltantes:", "de": "Fehlende Komponenten:", "fr": "Composants manquants :", "zh": "缺少的组件："},
    "install_now": {"ru": "Установить сейчас?", "en": "Install now?", "es": "¿Instalar ahora?", "de": "Jetzt installieren?", "fr": "Installer maintenant ?", "zh": "立即安装？"},
    "local_archive_found": {"ru": "Локальные архивы найдены:", "en": "Local archives found:", "es": "Archivos locales encontrados:", "de": "Lokale Archive gefunden:", "fr": "Archives locales trouvées :", "zh": "找到本地归档："},
    "install_complete": {"ru": "Установка завершена", "en": "Installation completed", "es": "Instalación completada", "de": "Installation abgeschlossen", "fr": "Installation terminée", "zh": "安装完成"},
    "saved": {"ru": "Сохранено", "en": "Saved", "es": "Guardado", "de": "Gespeichert", "fr": "Enregistré", "zh": "已保存"},
    "folder_name": {"ru": "Имя папки:", "en": "Folder name:", "es": "Nombre de carpeta:", "de": "Ordnername:", "fr": "Nom du dossier :", "zh": "文件夹名称："},
    "file_name": {"ru": "Имя файла (напр. index.html):", "en": "File name (e.g. index.html):", "es": "Nombre de archivo (ej. index.html):", "de": "Dateiname (z.B. index.html):", "fr": "Nom du fichier (ex. index.html) :", "zh": "文件名（例如 index.html）："},
    "site_name": {"ru": "Имя сайта:", "en": "Site name:", "es": "Nombre del sitio:", "de": "Site-Name:", "fr": "Nom du site :", "zh": "站点名称："},
    "site_domain": {"ru": "Домен (напр. myapp.localhost):", "en": "Domain (e.g. myapp.localhost):", "es": "Dominio (ej. myapp.localhost):", "de": "Domain (z.B. myapp.localhost):", "fr": "Domaine (ex. myapp.localhost) :", "zh": "域名（例如 myapp.localhost）："},
    "site_port": {"ru": "Порт (пусто для стандартного):", "en": "Port (empty for default):", "es": "Puerto (vacío para predeterminado):", "de": "Port (leer für Standard):", "fr": "Port (vide pour défaut) :", "zh": "端口（留空使用默认）："},
    "task_name": {"ru": "Имя задачи:", "en": "Task name:", "es": "Nombre de tarea:", "de": "Aufgabenname:", "fr": "Nom de la tâche :", "zh": "任务名称："},
    "task_command": {"ru": "Команда (напр. node server.js):", "en": "Command (e.g. node server.js):", "es": "Comando (ej. node server.js):", "de": "Befehl (z.B. node server.js):", "fr": "Commande (ex. node server.js) :", "zh": "命令（例如 node server.js）："},
    "task_schedule": {"ru": "Расписание (напр. 0 2 * * * - ежедневно в 2ч):", "en": "Schedule (e.g. 0 2 * * * for daily 2am):", "es": "Horario (ej. 0 2 * * * para diario a las 2am):", "de": "Zeitplan (z.B. 0 2 * * * für täglich 2 Uhr):", "fr": "Horaire (ex. 0 2 * * * pour quotidien à 2h) :", "zh": "计划（例如 0 2 * * * 每天凌晨2点）："},
    "minimized_tray": {"ru": "MiniServer свернут в трей", "en": "MiniServer minimized to tray", "es": "MiniServer minimizado a la bandeja", "de": "MiniServer in den Taskleiste minimiert", "fr": "MiniServer minimisé dans la zone de notification", "zh": "MiniServer 已最小化到托盘"},
    "tab_settings": {"ru": "Настройки", "en": "Settings", "es": "Ajustes", "de": "Einstellungen", "fr": "Paramètres", "zh": "设置"},
    "set_modules": {"ru": "Модули и дополнения", "en": "Modules & add-ons", "es": "Módulos y complementos", "de": "Module & Add-ons", "fr": "Modules et extensions", "zh": "模块和附加组件"},
    "set_dl_folder": {"ru": "Папка загрузок / локальных архивов:", "en": "Downloads / local archives folder:", "es": "Carpeta de descargas / archivos locales:", "de": "Downloads / lokaler Archivordner:", "fr": "Dossier de téléchargements / archives locales :", "zh": "下载 / 本地归档文件夹："},
    "set_open_folder": {"ru": "Открыть папку", "en": "Open folder", "es": "Abrir carpeta", "de": "Ordner öffnen", "fr": "Ouvrir le dossier", "zh": "打开文件夹"},
    "set_rescan": {"ru": "Пересканировать", "en": "Rescan", "es": "Reescanear", "de": "Neu scannen", "fr": "Réanalyser", "zh": "重新扫描"},
    "set_install_sel": {"ru": "Установить выбранное", "en": "Install selected", "es": "Instalar seleccionado", "de": "Ausgewählte installieren", "fr": "Installer la sélection", "zh": "安装所选"},
    "set_install_missing": {"ru": "Установить отсутствующие", "en": "Install missing", "es": "Instalar faltantes", "de": "Fehlende installieren", "fr": "Installer les manquants", "zh": "安装缺失项"},
    "col_component": {"ru": "Компонент", "en": "Component", "es": "Componente", "de": "Komponente", "fr": "Composant", "zh": "组件"},
    "col_state": {"ru": "Состояние", "en": "State", "es": "Estado", "de": "Status", "fr": "État", "zh": "状态"},
    "col_archive": {"ru": "Локальный архив", "en": "Local archive", "es": "Archivo local", "de": "Lokales Archiv", "fr": "Archive locale", "zh": "本地归档"},
    "col_expected": {"ru": "Ожидаемый файл", "en": "Expected file", "es": "Archivo esperado", "de": "Erwartete Datei", "fr": "Fichier attendu", "zh": "期望文件"},
    "state_installed": {"ru": "Установлен", "en": "Installed", "es": "Instalado", "de": "Installiert", "fr": "Installé", "zh": "已安装"},
    "state_missing": {"ru": "Отсутствует", "en": "Missing", "es": "Faltante", "de": "Fehlt", "fr": "Manquant", "zh": "缺失"},
    "set_no_selection": {"ru": "Ничего не выбрано", "en": "Nothing selected", "es": "Nada seleccionado", "de": "Nichts ausgewählt", "fr": "Rien de sélectionné", "zh": "未选择任何项"},
    "set_inst_done": {"ru": "Установка завершена", "en": "Installation finished", "es": "Instalación finalizada", "de": "Installation abgeschlossen", "fr": "Installation terminée", "zh": "安装完成"},
    "btn_open_site": {"ru": "Открыть сайт", "en": "Open Site", "es": "Abrir sitio", "de": "Seite öffnen", "fr": "Ouvrir le site", "zh": "打开站点"},
    "set_logs": {"ru": "Шрифт логов", "en": "Log font", "es": "Fuente de registros", "de": "Log-Schriftart", "fr": "Police des logs", "zh": "日志字体"},
    "set_font": {"ru": "Шрифт:", "en": "Font:", "es": "Fuente:", "de": "Schriftart:", "fr": "Police :", "zh": "字体："},
    "set_font_size": {"ru": "Размер:", "en": "Size:", "es": "Tamaño:", "de": "Größe:", "fr": "Taille :", "zh": "大小："},
    "nodejs": {"ru": "Node.js", "en": "Node.js", "es": "Node.js", "de": "Node.js", "fr": "Node.js", "zh": "Node.js"},
    "btn_ok": {"ru": "ОК", "en": "OK", "es": "Aceptar", "de": "OK", "fr": "OK", "zh": "确定"},
    "btn_cancel": {"ru": "Отмена", "en": "Cancel", "es": "Cancelar", "de": "Abbrechen", "fr": "Annuler", "zh": "取消"},
    "btn_yes": {"ru": "Да", "en": "Yes", "es": "Sí", "de": "Ja", "fr": "Oui", "zh": "是"},
    "btn_no": {"ru": "Нет", "en": "No", "es": "No", "de": "Nein", "fr": "Non", "zh": "否"},
    "tip_help": {"ru": "Открыть справку и документацию", "en": "Open help and documentation", "es": "Abrir ayuda y documentación", "de": "Hilfe und Dokumentation öffnen", "fr": "Ouvrir l'aide et la documentation", "zh": "打开帮助和文档"},
    "tip_toggle_all": {"ru": "Запустить или остановить все сервисы", "en": "Start or stop all services", "es": "Iniciar o detener todos los servicios", "de": "Alle Dienste starten oder stoppen", "fr": "Démarrer ou arrêter tous les services", "zh": "启动或停止所有服务"},
    "tip_start_all": {"ru": "Запустить все сервисы", "en": "Start all services", "es": "Iniciar todos los servicios", "de": "Alle Dienste starten", "fr": "Démarrer tous les services", "zh": "启动所有服务"},
    "tip_stop_all": {"ru": "Остановить все сервисы", "en": "Stop all services", "es": "Detener todos los servicios", "de": "Alle Dienste stoppen", "fr": "Arrêter tous les services", "zh": "停止所有服务"},
    "tip_restart_all": {"ru": "Перезапустить все сервисы", "en": "Restart all services", "es": "Reiniciar todos los servicios", "de": "Alle Dienste neu starten", "fr": "Redémarrer tous les services", "zh": "重启所有服务"},
    "tip_start": {"ru": "Запустить / остановить сервис", "en": "Start / stop the service", "es": "Iniciar / detener el servicio", "de": "Dienst starten / stoppen", "fr": "Démarrer / arrêter le service", "zh": "启动 / 停止服务"},
    "tip_restart": {"ru": "Перезапустить сервис", "en": "Restart the service", "es": "Reiniciar el servicio", "de": "Dienst neu starten", "fr": "Redémarrer le service", "zh": "重启服务"},
    "tip_add": {"ru": "Добавить", "en": "Add", "es": "Agregar", "de": "Hinzufügen", "fr": "Ajouter", "zh": "添加"},
    "tip_remove": {"ru": "Удалить", "en": "Remove", "es": "Eliminar", "de": "Entfernen", "fr": "Supprimer", "zh": "删除"},
    "tip_open": {"ru": "Открыть", "en": "Open", "es": "Abrir", "de": "Öffnen", "fr": "Ouvrir", "zh": "打开"},
    "tip_refresh": {"ru": "Обновить", "en": "Refresh", "es": "Actualizar", "de": "Aktualisieren", "fr": "Actualiser", "zh": "刷新"},
    "tip_save": {"ru": "Сохранить", "en": "Save", "es": "Guardar", "de": "Speichern", "fr": "Enregistrer", "zh": "保存"},
    "tip_run": {"ru": "Запустить", "en": "Run", "es": "Ejecutar", "de": "Ausführen", "fr": "Exécuter", "zh": "运行"},
    "tip_browse": {"ru": "Выбрать папку или файл", "en": "Browse for folder or file", "es": "Examinar carpeta o archivo", "de": "Ordner oder Datei wählen", "fr": "Parcourir dossier ou fichier", "zh": "浏览文件夹或文件"},
    "tip_localhost": {"ru": "Открыть сайт в браузере", "en": "Open the site in a browser", "es": "Abrir el sitio en el navegador", "de": "Seite im Browser öffnen", "fr": "Ouvrir le site dans le navigateur", "zh": "在浏览器中打开站点"},
    "tip_pma": {"ru": "Открыть phpMyAdmin", "en": "Open phpMyAdmin", "es": "Abrir phpMyAdmin", "de": "phpMyAdmin öffnen", "fr": "Ouvrir phpMyAdmin", "zh": "打开 phpMyAdmin"},
    "tip_www": {"ru": "Открыть папку www", "en": "Open the www folder", "es": "Abrir la carpeta www", "de": "www-Ordner öffnen", "fr": "Ouvrir le dossier www", "zh": "打开 www 文件夹"},
    "tip_ssl": {"ru": "Выпустить локальный SSL-сертификат", "en": "Issue a local SSL certificate", "es": "Emitir un certificado SSL local", "de": "Lokales SSL-Zertifikat ausstellen", "fr": "Émettre un certificat SSL local", "zh": "颁发本地 SSL 证书"},
    "tip_script": {"ru": "Запустить JS/TS скрипт через Node", "en": "Run a JS/TS script with Node", "es": "Ejecutar un script JS/TS con Node", "de": "JS/TS-Skript mit Node ausführen", "fr": "Exécuter un script JS/TS avec Node", "zh": "使用 Node 运行 JS/TS 脚本"},
    "tip_clear": {"ru": "Очистить все логи", "en": "Clear all logs", "es": "Borrar todos los registros", "de": "Alle Logs löschen", "fr": "Effacer tous les logs", "zh": "清除所有日志"},
    "set_select": {"ru": "Выберите для установки", "en": "Select to install", "es": "Seleccionar para instalar", "de": "Zur Installation auswählen", "fr": "Sélectionner à installer", "zh": "选择要安装的"},
    "install_extract": {"ru": "Распаковка…", "en": "Extracting…", "es": "Extrayendo…", "de": "Entpacken…", "fr": "Extraction…", "zh": "解压中…"},
    "tab_docker": {"ru": "Docker", "en": "Docker", "es": "Docker", "de": "Docker", "fr": "Docker", "zh": "Docker"},
    "col_cont": {"ru": "Контейнер", "en": "Container", "es": "Contenedor", "de": "Container", "fr": "Conteneur", "zh": "容器"},
    "col_image": {"ru": "Образ", "en": "Image", "es": "Imagen", "de": "Image", "fr": "Image", "zh": "镜像"},
    "col_dockstatus": {"ru": "Состояние", "en": "Status", "es": "Estado", "de": "Status", "fr": "État", "zh": "状态"},
    "col_ports": {"ru": "Порты", "en": "Ports", "es": "Puertos", "de": "Ports", "fr": "Ports", "zh": "端口"},
    "dock_notfound": {"ru": "Docker не найден. Установите Docker Desktop, затем нажмите Обновить.", "en": "Docker not found. Install Docker Desktop, then press Refresh.", "es": "Docker no encontrado. Instale Docker Desktop y pulse Actualizar.", "de": "Docker nicht gefunden. Docker Desktop installieren, dann Aktualisieren.", "fr": "Docker introuvable. Installez Docker Desktop, puis Actualiser.", "zh": "未找到 Docker。请安装 Docker Desktop，然后点击刷新。"},
    "faraja_meaning": {"ru": "Название Faraja на языке суахили означает «Комфорт» — среда создана для комфортной разработки.", "en": "The name Faraja means “Comfort” in Swahili — an environment built for comfortable development.", "es": "El nombre Faraja significa «Comodidad» en suajili: un entorno creado para desarrollar con comodidad.", "de": "Der Name Faraja bedeutet auf Swahili „Komfort“ – eine Umgebung für komfortables Entwickeln.", "fr": "Le nom Faraja signifie « Confort » en swahili : un environnement pensé pour développer confortablement.", "zh": "Faraja 在斯瓦希里语中意为“舒适”——为舒适开发而打造的环境。"},
    "btn_donate": {"ru": "❤ Поддержать", "en": "❤ Donate", "es": "❤ Donar", "de": "❤ Spenden", "fr": "❤ Soutenir", "zh": "❤ 捐赠"},
    "donate_title": {"ru": "Поддержать Faraja WebServer", "en": "Support Faraja WebServer", "es": "Apoyar a Faraja WebServer", "de": "Faraja WebServer unterstützen", "fr": "Soutenir Faraja WebServer", "zh": "支持 Faraja WebServer"},
    "donate_text": {"ru": "Если программа полезна — поддержите разработку. Спасибо!", "en": "If you find the app useful, please support its development. Thank you!", "es": "Si la aplicación le resulta útil, apoye su desarrollo. ¡Gracias!", "de": "Wenn Ihnen die App nützt, unterstützen Sie bitte die Entwicklung. Danke!", "fr": "Si l'application vous est utile, soutenez son développement. Merci !", "zh": "如果这个应用对您有用，请支持它的开发。谢谢！"},
    "donate_copy": {"ru": "Копировать", "en": "Copy", "es": "Copiar", "de": "Kopieren", "fr": "Copier", "zh": "复制"},
    "donate_copied": {"ru": "Адрес скопирован", "en": "Address copied", "es": "Dirección copiada", "de": "Adresse kopiert", "fr": "Adresse copiée", "zh": "地址已复制"},
    "kill_title": {"ru": "Порт занят", "en": "Port busy", "es": "Puerto ocupado", "de": "Port belegt", "fr": "Port occupé", "zh": "端口被占用"},
    "kill_text": {"ru": "Порт {port} занят: {detail}. Завершить мешающий процесс и продолжить запуск?", "en": "Port {port} is busy: {detail}. Kill the blocking process and continue?", "es": "El puerto {port} está ocupado: {detail}. ¿Terminar el proceso y continuar?", "de": "Port {port} ist belegt: {detail}. Blockierenden Prozess beenden und fortfahren?", "fr": "Le port {port} est occupé : {detail}. Terminer le processus et continuer ?", "zh": "端口 {port} 被占用：{detail}。结束该进程并继续吗？"},
    "set_phpmode": {"ru": "Режим PHP:", "en": "PHP mode:", "es": "Modo PHP:", "de": "PHP-Modus:", "fr": "Mode PHP :", "zh": "PHP 模式："},
    "php_dev": {"ru": "Разработка", "en": "Development", "es": "Desarrollo", "de": "Entwicklung", "fr": "Développement", "zh": "开发"},
    "php_safe": {"ru": "Безопасный", "en": "Safe", "es": "Seguro", "de": "Sicher", "fr": "Sûr", "zh": "安全"},
    "set_dirlist": {"ru": "Листинг каталогов", "en": "Directory listing", "es": "Listado de directorios", "de": "Verzeichnisauflistung", "fr": "Liste des répertoires", "zh": "目录列表"},
    "tab_node": {"ru": "Node.js / Python", "en": "Node.js / Python", "es": "Node.js / Python", "de": "Node.js / Python", "fr": "Node.js / Python", "zh": "Node.js / Python"},
    "site_pyver": {"ru": "Версия Python:", "en": "Python version:", "es": "Versión de Python:", "de": "Python-Version:", "fr": "Version de Python :", "zh": "Python 版本："},
    "node_project": {"ru": "Проект:", "en": "Project:", "es": "Proyecto:", "de": "Projekt:", "fr": "Projet :", "zh": "项目："},
    "node_entry": {"ru": "Файл:", "en": "Entry:", "es": "Archivo:", "de": "Datei:", "fr": "Fichier :", "zh": "入口："},
    "node_port": {"ru": "Порт:", "en": "Port:", "es": "Puerto:", "de": "Port:", "fr": "Port :", "zh": "端口："},
    "col_server": {"ru": "Сервер", "en": "Server", "es": "Servidor", "de": "Server", "fr": "Serveur", "zh": "服务器"},
    "col_pid": {"ru": "PID", "en": "PID", "es": "PID", "de": "PID", "fr": "PID", "zh": "PID"},
    "col_started": {"ru": "Запущен", "en": "Started", "es": "Iniciado", "de": "Gestartet", "fr": "Démarré", "zh": "启动时间"},
    "tab_db": {"ru": "Базы данных", "en": "Databases", "es": "Bases de datos", "de": "Datenbanken", "fr": "Bases de données", "zh": "数据库"},
    "db_host": {"ru": "Хост:", "en": "Host:", "es": "Host:", "de": "Host:", "fr": "Hôte :", "zh": "主机："},
    "db_user": {"ru": "Пользователь:", "en": "User:", "es": "Usuario:", "de": "Benutzer:", "fr": "Utilisateur :", "zh": "用户："},
    "db_pass": {"ru": "Пароль:", "en": "Password:", "es": "Contraseña:", "de": "Passwort:", "fr": "Mot de passe :", "zh": "密码："},
    "db_name": {"ru": "База:", "en": "Database:", "es": "Base de datos:", "de": "Datenbank:", "fr": "Base :", "zh": "数据库："},
    "db_apply": {"ru": "Применить", "en": "Apply", "es": "Aplicar", "de": "Anwenden", "fr": "Appliquer", "zh": "应用"},
    "db_createdb": {"ru": "Создать БД", "en": "Create DB", "es": "Crear BD", "de": "DB erstellen", "fr": "Créer BD", "zh": "创建数据库"},
    "db_setpass": {"ru": "Сменить пароль", "en": "Set password", "es": "Cambiar clave", "de": "Passwort setzen", "fr": "Définir mot de passe", "zh": "设置密码"},
    "db_bind": {"ru": "Адрес:", "en": "Bind:", "es": "Bind:", "de": "Bind:", "fr": "Bind :", "zh": "绑定："},
    "dock_file": {"ru": "Compose-файл:", "en": "Compose file:", "es": "Archivo Compose:", "de": "Compose-Datei:", "fr": "Fichier Compose :", "zh": "Compose 文件："},
    "dock_up": {"ru": "Up", "en": "Up", "es": "Up", "de": "Up", "fr": "Up", "zh": "Up"},
    "dock_down": {"ru": "Down", "en": "Down", "es": "Down", "de": "Down", "fr": "Down", "zh": "Down"},
    "dock_pull": {"ru": "Pull", "en": "Pull", "es": "Pull", "de": "Pull", "fr": "Pull", "zh": "Pull"},
    "dock_logs": {"ru": "Логи", "en": "Logs", "es": "Registros", "de": "Logs", "fr": "Logs", "zh": "日志"},
    "dock_images": {"ru": "Образы", "en": "Images", "es": "Imágenes", "de": "Images", "fr": "Images", "zh": "镜像"},
    "col_size": {"ru": "Размер", "en": "Size", "es": "Tamaño", "de": "Größe", "fr": "Taille", "zh": "大小"},
    "col_tag": {"ru": "Тег", "en": "Tag", "es": "Etiqueta", "de": "Tag", "fr": "Tag", "zh": "标签"},
    "col_type": {"ru": "Тип", "en": "Type", "es": "Tipo", "de": "Typ", "fr": "Type", "zh": "类型"},
    "col_https": {"ru": "HTTPS", "en": "HTTPS", "es": "HTTPS", "de": "HTTPS", "fr": "HTTPS", "zh": "HTTPS"},
    "site_type": {"ru": "Тип (php/node/python/static):", "en": "Type (php/node/python/static):", "es": "Tipo (php/node/python/static):", "de": "Typ (php/node/python/static):", "fr": "Type (php/node/python/static) :", "zh": "类型 (php/node/python/static)："},
    "site_https_q": {"ru": "Включить HTTPS (нужен mkcert)?", "en": "Enable HTTPS (needs mkcert)?", "es": "¿Activar HTTPS (requiere mkcert)?", "de": "HTTPS aktivieren (braucht mkcert)?", "fr": "Activer HTTPS (nécessite mkcert) ?", "zh": "启用 HTTPS（需要 mkcert）？"},
    "site_hosts_admin": {"ru": "Нет прав на запись hosts — запустите от имени администратора", "en": "No permission to write hosts — run as administrator", "es": "Sin permiso para escribir hosts — ejecute como administrador", "de": "Keine hosts-Schreibrechte — als Administrator starten", "fr": "Permission hosts refusée — lancer en administrateur", "zh": "无权写入 hosts——请以管理员身份运行"},
    "tab_procs": {"ru": "Процессы", "en": "Processes", "es": "Procesos", "de": "Prozesse", "fr": "Processus", "zh": "进程"},
    "col_proc": {"ru": "Процесс", "en": "Process", "es": "Proceso", "de": "Prozess", "fr": "Processus", "zh": "进程"},
    "col_mem": {"ru": "Память", "en": "Memory", "es": "Memoria", "de": "Speicher", "fr": "Mémoire", "zh": "内存"},
    "col_parent": {"ru": "Родитель", "en": "Parent", "es": "Padre", "de": "Parent", "fr": "Parent", "zh": "父进程"},
    "log_level": {"ru": "Уровень:", "en": "Level:", "es": "Nivel:", "de": "Stufe:", "fr": "Niveau :", "zh": "级别："},
    "log_find": {"ru": "Поиск:", "en": "Search:", "es": "Buscar:", "de": "Suchen:", "fr": "Rechercher :", "zh": "搜索："},
    "level_all": {"ru": "Все", "en": "All", "es": "Todos", "de": "Alle", "fr": "Tous", "zh": "全部"},
    "tab_dbmanager": {"ru": "Менеджер БД", "en": "DB Manager", "es": "Gestor BD", "de": "DB-Manager", "fr": "Gestion BD", "zh": "数据库管理"},
    "db_list": {"ru": "Список БД", "en": "List DBs", "es": "Ver BD", "de": "DBs listen", "fr": "Lister BD", "zh": "列出数据库"},
    "db_create": {"ru": "Создать", "en": "Create", "es": "Crear", "de": "Erstellen", "fr": "Créer", "zh": "创建"},
    "db_drop": {"ru": "Удалить БД", "en": "Drop DB", "es": "Borrar BD", "de": "DB löschen", "fr": "Supprimer BD", "zh": "删除数据库"},
    "db_users": {"ru": "Пользователи", "en": "Users", "es": "Usuarios", "de": "Benutzer", "fr": "Utilisateurs", "zh": "用户"},
    "db_mkuser": {"ru": "+ Пользователь", "en": "+ User", "es": "+ Usuario", "de": "+ Benutzer", "fr": "+ Utilisateur", "zh": "+ 用户"},
    "db_backup": {"ru": "Бэкап", "en": "Backup", "es": "Respaldo", "de": "Backup", "fr": "Sauvegarde", "zh": "备份"},
    "db_restore": {"ru": "Восстановить", "en": "Restore", "es": "Restaurar", "de": "Wiederherst.", "fr": "Restaurer", "zh": "恢复"},
    "db_flush": {"ru": "Очистить Redis", "en": "Flush Redis", "es": "Vaciar Redis", "de": "Redis leeren", "fr": "Vider Redis", "zh": "清空 Redis"},
    "tab_perf": {"ru": "Нагрузка", "en": "Load Test", "es": "Carga", "de": "Lasttest", "fr": "Charge", "zh": "压力测试"},
    "perf_target": {"ru": "Цель:", "en": "Target:", "es": "Objetivo:", "de": "Ziel:", "fr": "Cible :", "zh": "目标："},
    "perf_profile": {"ru": "Профиль:", "en": "Profile:", "es": "Perfil:", "de": "Profil:", "fr": "Profil :", "zh": "配置文件："},
    "perf_users": {"ru": "Пользователи:", "en": "Users:", "es": "Usuarios:", "de": "Benutzer:", "fr": "Utilisateurs :", "zh": "用户数："},
    "perf_duration": {"ru": "Длительность (с):", "en": "Duration (s):", "es": "Duración (s):", "de": "Dauer (s):", "fr": "Durée (s) :", "zh": "时长（秒）："},
    "perf_paths": {"ru": "Запросы (МЕТОД путь [вес]):", "en": "Requests (METHOD path [weight]):", "es": "Peticiones (MÉTODO ruta [peso]):", "de": "Anfragen (METHODE Pfad [Gew.]) :", "fr": "Requêtes (MÉTHODE chemin [poids]) :", "zh": "请求（方法 路径 [权重]）:"},
    "perf_save": {"ru": "Сохранить отчёт", "en": "Save report", "es": "Guardar informe", "de": "Bericht speichern", "fr": "Enregistrer rapport", "zh": "保存报告"},
    "db_rootpass": {"ru": "Новый пароль root:", "en": "New root password:", "es": "Nueva clave root:", "de": "Neues Root-Passwort:", "fr": "Nouveau mot de passe root :", "zh": "新 root 密码："},
    "db_curpass": {"ru": "Текущий пароль:", "en": "Current password:", "es": "Clave actual:", "de": "Aktuelles Passwort:", "fr": "Mot de passe actuel :", "zh": "当前密码："},
    "tab_logs": {"ru": "Логи", "en": "Logs", "es": "Registros", "de": "Logs", "fr": "Logs", "zh": "日志"},
    "tab_projects": {"ru": "Проекты", "en": "Projects", "es": "Proyectos", "de": "Projekte", "fr": "Projets", "zh": "项目"},
    "tab_monitor": {"ru": "Мониторинг", "en": "Monitor", "es": "Monitor", "de": "Monitor", "fr": "Moniteur", "zh": "监控"},
    "dock_networks": {"ru": "Сети", "en": "Networks", "es": "Redes", "de": "Netzwerke", "fr": "Réseaux", "zh": "网络"},
    "dock_volumes": {"ru": "Тома", "en": "Volumes", "es": "Volúmenes", "de": "Volumes", "fr": "Volumes", "zh": "卷"},
    "perf_baseline": {"ru": "В эталон", "en": "Set baseline", "es": "Referencia", "de": "Basiswert", "fr": "Référence", "zh": "设为基线"},
    "net_btc": {"ru": "Сеть Bitcoin", "en": "Bitcoin network", "es": "Red Bitcoin", "de": "Bitcoin-Netzwerk", "fr": "Réseau Bitcoin", "zh": "比特币网络"},
    "net_eth": {"ru": "Сеть Ethereum (ERC-20)", "en": "Ethereum network (ERC-20)", "es": "Red Ethereum (ERC-20)", "de": "Ethereum-Netzwerk (ERC-20)", "fr": "Réseau Ethereum (ERC-20)", "zh": "以太坊网络（ERC-20）"},
    "net_trx": {"ru": "Сеть Tron (TRC-20)", "en": "Tron network (TRC-20)", "es": "Red Tron (TRC-20)", "de": "Tron-Netzwerk (TRC-20)", "fr": "Réseau Tron (TRC-20)", "zh": "波场网络（TRC-20）"},
    "set_env": {"ru": "Окружение", "en": "Environment", "es": "Entorno", "de": "Umgebung", "fr": "Environnement", "zh": "环境"},
    "env_php": {"ru": "PHP:", "en": "PHP:", "es": "PHP:", "de": "PHP:", "fr": "PHP :", "zh": "PHP："},
    "env_node": {"ru": "Node.js:", "en": "Node.js:", "es": "Node.js:", "de": "Node.js:", "fr": "Node.js :", "zh": "Node.js："},
    "env_tools": {"ru": "Инструменты:", "en": "Tools:", "es": "Herramientas:", "de": "Werkzeuge:", "fr": "Outils :", "zh": "工具："},
    "dock_build": {"ru": "Build", "en": "Build", "es": "Build", "de": "Build", "fr": "Build", "zh": "构建"},
    "dbm_conn": {"ru": "Подключение", "en": "Connection", "es": "Conexión", "de": "Verbindung", "fr": "Connexion", "zh": "连接"},
    "tab_phpini": {"ru": "PHP.ini", "en": "PHP.ini", "es": "PHP.ini", "de": "PHP.ini", "fr": "PHP.ini", "zh": "PHP.ini"},
    "phpini_search": {"ru": "Поиск:", "en": "Search:", "es": "Buscar:", "de": "Suchen:", "fr": "Rechercher :", "zh": "搜索："},
    "phpini_directives": {"ru": "Директивы", "en": "Directives", "es": "Directivas", "de": "Direktiven", "fr": "Directives", "zh": "指令"},
    "phpini_ext": {"ru": "Расширения", "en": "Extensions", "es": "Extensiones", "de": "Erweiterungen", "fr": "Extensions", "zh": "扩展"},
    "phpini_save": {"ru": "Сохранить", "en": "Save", "es": "Guardar", "de": "Speichern", "fr": "Enregistrer", "zh": "保存"},
    "phpini_restart": {"ru": "Рестарт PHP", "en": "Restart PHP", "es": "Reiniciar PHP", "de": "PHP neu starten", "fr": "Redémarrer PHP", "zh": "重启 PHP"},
    "set_ports": {"ru": "Порты", "en": "Ports", "es": "Puertos", "de": "Ports", "fr": "Ports", "zh": "端口"},
    "set_autostart": {"ru": "Автозапуск с Windows", "en": "Start with Windows", "es": "Iniciar con Windows", "de": "Mit Windows starten", "fr": "Démarrer avec Windows", "zh": "随 Windows 启动"},
    "perf_chart_tab": {"ru": "Нагрузка: график", "en": "Load: chart", "es": "Carga: gráfico", "de": "Last: Chart", "fr": "Charge : graphique", "zh": "负载：图表"},
    "set_snapshot": {"ru": "Снапшот", "en": "Snapshot", "es": "Instantánea", "de": "Snapshot", "fr": "Instantané", "zh": "快照"},
    "set_restore": {"ru": "Восстановить", "en": "Restore", "es": "Restaurar", "de": "Wiederherst.", "fr": "Restaurer", "zh": "恢复"},
    "site_phpver": {"ru": "Версия PHP (пусто — по умолчанию):", "en": "PHP version (empty — default):", "es": "Versión de PHP (vacío — predeterminada):", "de": "PHP-Version (leer — Standard):", "fr": "Version de PHP (vide — défaut) :", "zh": "PHP 版本（留空为默认）:"},
    "update_avail": {"ru": "Доступно обновление {ver} (у вас {cur}) — скачайте с GitHub", "en": "Update available {ver} (you have {cur}) — download from GitHub", "es": "Actualización disponible {ver} (tienes {cur}) — descarga de GitHub", "de": "Update verfügbar {ver} (installiert {cur}) — von GitHub laden", "fr": "Mise à jour {ver} disponible (vous avez {cur}) — voir GitHub", "zh": "有可用更新 {ver}（当前 {cur}）——请从 GitHub 下载"},
    "btn_open": {"ru": "Открыть", "en": "Open", "es": "Abrir", "de": "Öffnen", "fr": "Ouvrir", "zh": "打开"},
    "quick_actions": {"ru": "Быстрые действия", "en": "Quick actions", "es": "Acciones rápidas", "de": "Schnellzugriff", "fr": "Actions rapides", "zh": "快捷操作"},
    "btn_cut": {"ru": "Вырезать", "en": "Cut", "es": "Cortar", "de": "Ausschneiden", "fr": "Couper", "zh": "剪切"},
    "btn_paste": {"ru": "Вставить", "en": "Paste", "es": "Pegar", "de": "Einfügen", "fr": "Coller", "zh": "粘贴"},
    "btn_rename": {"ru": "Переименовать", "en": "Rename", "es": "Renombrar", "de": "Umbenennen", "fr": "Renommer", "zh": "重命名"},
    "dbm_actions": {"ru": "Действия", "en": "Actions", "es": "Acciones", "de": "Aktionen", "fr": "Actions", "zh": "操作"},
    "admin_hint": {"ru": "Совет: запустите от имени администратора — иначе недоступны запись hosts и HTTPS-домены", "en": "Tip: run as administrator — otherwise hosts editing and HTTPS domains are unavailable", "es": "Consejo: ejecute como administrador — sin esto no hay hosts ni dominios HTTPS", "de": "Tipp: als Administrator starten — sonst keine Hosts- und HTTPS-Domains", "fr": "Astuce : lancer en administrateur — sinon pas de hosts ni domaines HTTPS", "zh": "提示：请以管理员身份运行，否则无法使用 hosts 和 HTTPS 域名"},
    "site_no_hosts": {"ru": "Домен {domain} не резолвится — нет записи hosts (нужен администратор). Открываю через localhost.", "en": "Domain {domain} does not resolve — no hosts entry (administrator needed). Opening via localhost.", "es": "El dominio {domain} no resuelve — sin entrada hosts (se necesita administrador). Abriendo vía localhost.", "de": "Domain {domain} löst nicht auf — kein Hosts-Eintrag (Administrator nötig). Öffne via localhost.", "fr": "Le domaine {domain} ne résout pas — pas d'entrée hosts (administrateur requis). Ouverture via localhost.", "zh": "域名 {domain} 无法解析——缺少 hosts 条目（需要管理员权限）。改用 localhost 打开。"},
}

PAGE_SUBTITLES = {
    "main": {"ru": "Сервисы и управление локальной средой", "en": "Services and local environment control", "es": "Servicios y entorno local", "de": "Dienste und lokale Umgebung", "fr": "Services et environnement local", "zh": "服务与本地环境管理"},
    "logs": {"ru": "Журнал работы сервисов и системные события", "en": "Service logs and system events", "es": "Registros de servicios y eventos del sistema", "de": "Dienstprotokolle und Systemereignisse", "fr": "Journaux des services et événements système", "zh": "服务日志与系统事件"},
    "db": {"ru": "SQL, базы данных и управление подключениями", "en": "SQL, databases and connection management", "es": "SQL, bases de datos y conexiones", "de": "SQL, Datenbanken und Verbindungen", "fr": "SQL, bases de données et connexions", "zh": "SQL、数据库与连接管理"},
    "projects": {"ru": "Файлы, сайты, задачи и серверные проекты", "en": "Files, sites, tasks and server projects", "es": "Archivos, sitios, tareas y proyectos", "de": "Dateien, Sites, Aufgaben und Serverprojekte", "fr": "Fichiers, sites, tâches et projets serveur", "zh": "文件、站点、任务与服务器项目"},
    "monitor": {"ru": "Docker, процессы и нагрузочное тестирование", "en": "Docker, processes and load testing", "es": "Docker, procesos y pruebas de carga", "de": "Docker, Prozesse und Lasttests", "fr": "Docker, processus et tests de charge", "zh": "Docker、进程与压力测试"},
}

LANG_FILE = APP_ROOT / "config" / "lang.json"

class LangManager:
    def __init__(self):
        self._lang = "en"
        self._load()
    def _load(self):
        try:
            if LANG_FILE.exists():
                data = json.loads(LANG_FILE.read_text(encoding="utf-8"))
                if data.get("lang") in LANGUAGES:
                    self._lang = data["lang"]
        except Exception:
            pass
    def save(self):
        LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LANG_FILE.write_text(json.dumps({"lang": self._lang}), encoding="utf-8")
    def get(self):
        return self._lang
    def set(self, code):
        if code in LANGUAGES:
            self._lang = code
            self.save()
    def t(self, key, **kwargs):
        entry = LOCALES.get(key, {})
        text = entry.get(self._lang, entry.get("en", key))
        if kwargs:
            text = text.format(**kwargs)
        return text
    def flag(self, code=None):
        code = code or self._lang
        return LANGUAGES.get(code, {}).get("flag", "?")

lang = LangManager()

APP_NAME = "Faraja WebServer"
APP_VERSION = "16.0"
for _entry in LOCALES.values():
    for _code, _text in _entry.items():
        if "MiniServer" in _text:
            _entry[_code] = _text.replace("MiniServer", APP_NAME)
del _entry, _code, _text

def comps(): return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
def is_component(item):
    return isinstance(item, dict) and "expected" in item and "archive" in item
def port_open(port):
    s=socket.socket(); s.settimeout(.25)
    try:return s.connect_ex(("127.0.0.1",int(port)))==0
    finally:s.close()
def wait_port(port,timeout=20):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if port_open(port):return True
        time.sleep(.2)
    return False
def pids_on_port(port):
    pids = set()
    ps = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"Get-NetTCPConnection -State Listen -LocalPort {int(port)} | "
        "Select-Object -ExpandProperty OwningProcess"
    )
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps],
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=8,
        )
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit():
                pids.add(int(line))
    except Exception:
        pass
    if pids:
        return sorted(pids)
    try:
        out = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"],
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return []
    for line in out.splitlines():
        cols = line.split()
        if len(cols) < 5 or cols[0].upper() != "TCP":
            continue
        local = cols[1]
        state = cols[-2].upper()
        pid = cols[-1]
        try:
            local_port = int(local.rsplit(":", 1)[1])
        except Exception:
            continue
        if local_port == int(port) and state == "LISTENING" and pid.isdigit():
            pids.add(int(pid))
    return sorted(pids)

def process_name(pid):
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=6,
        ).strip()
        if not out or out.startswith("INFO:"):
            return ""
        import csv, io
        row = next(csv.reader(io.StringIO(out)), [])
        return row[0] if row else ""
    except Exception:
        return ""

def process_pids_by_name(image_name):
    target = image_name.lower()
    pids = set()
    ps = ("$ErrorActionPreference='SilentlyContinue';"
          "Get-CimInstance Win32_Process | "
          f"Where-Object {{$_.Name -and $_.Name.ToLower() -eq '{target}'}} | "
          "Select-Object -ExpandProperty ProcessId")
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps], text=True,
            encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=8)
        for line in out.splitlines():
            if line.strip().isdigit(): pids.add(int(line.strip()))
    except Exception:
        pass
    return sorted(pids)

def web_server_running(kind):
    names = ("httpd.exe", "apache.exe") if kind == "apache" else ("nginx.exe",) if kind == "nginx" else ()
    return any(process_pids_by_name(n) for n in names)

def web_server_pids(kind):
    names = ("httpd.exe", "apache.exe") if kind == "apache" else ("nginx.exe",) if kind == "nginx" else ()
    out=[]
    for n in names: out.extend(process_pids_by_name(n))
    return sorted(set(out))

def stop_web_server_processes(kind):
    pids=web_server_pids(kind)
    for pid in pids: kill_pid_tree(pid)
    return pids

def port_owners(port):
    return [(pid, process_name(pid)) for pid in pids_on_port(port)]

def kill_pid_tree(pid):
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=12,
        )
    except Exception:
        pass

def stop_named_processes_on_port(port, allowed_names):
    allowed = {x.lower() for x in allowed_names}
    stopped = []
    foreign = []
    for pid, name in port_owners(port):
        if (name or "").lower() in allowed:
            kill_pid_tree(pid)
            stopped.append((pid, name))
        else:
            foreign.append((pid, name))
    return stopped, foreign

def wait_port_closed(port, timeout=12):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if not port_open(port):
            return True
        time.sleep(.2)
    return not port_open(port)


def is_admin():
    try:
        import ctypes as _ct
        return bool(_ct.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def hosts_path():
    return Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "drivers" / "etc" / "hosts"

def hosts_add(domain):
    p = hosts_path()
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        text = ""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) >= 2 and parts[0] in ("127.0.0.1", "::1") and domain in parts[1:]:
            return False
    bak = p.with_name(p.name + ".faraja.bak")
    try:
        if not bak.exists() and p.exists():
            shutil.copy2(str(p), str(bak))
    except OSError:
        pass
    with open(str(p), "a", encoding="utf-8") as f:
        f.write(f"\n127.0.0.1 {domain}  # faraja\n")
    return True

def hosts_remove(domain):
    p = hosts_path()
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except FileNotFoundError:
        return False
    kept = [l for l in lines if not (l.strip().endswith("# faraja") and domain in l.split())]
    if len(kept) == len(lines):
        return False
    p.write_text("".join(kept), encoding="utf-8")
    return True

def stop_proc(p,timeout=3):
    if p and p.poll() is None:
        try:
            p.terminate()
            p.wait(timeout=max(0.5, timeout))
        except subprocess.TimeoutExpired:
            try:p.kill()
            except Exception:pass
            try:p.wait(1)
            except Exception:pass
        except Exception:
            pass

def emergency_kill():
    CF = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    apache_bin = RUNTIME / "Apache24" / "bin" / "httpd.exe"
    if apache_bin.exists():
        try:
            subprocess.run(
                [str(apache_bin), "-k", "stop"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=5, cwd=str(apache_bin.parent),
                creationflags=CF
            )
            time.sleep(1)
        except Exception:
            pass
    nginx_bin = RUNTIME / "nginx" / "nginx.exe"
    if nginx_bin.exists():
        try:
            subprocess.run(
                [str(nginx_bin), "-s", "stop"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=5, cwd=str(nginx_bin.parent),
                creationflags=CF
            )
            time.sleep(1)
        except Exception:
            pass
    for port in (CONFIG.get("mariadb_port", 3306), CONFIG.get("php_cgi_port", 9074),
                 CONFIG.get("postgresql_port", 5432), CONFIG.get("redis_port", 6379)):
        for pid in pids_on_port(port):
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=5, creationflags=CF)
            except Exception:
                pass
    remaining = []
    for port in (CONFIG.get("apache_port", 8080), CONFIG.get("nginx_port", 80)):
        remaining.extend(pids_on_port(port))
    for pid in remaining:
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                           creationflags=CF)
        except Exception:
            pass

atexit.register(emergency_kill)

def download(url,out,progress,log):
    part=out.with_suffix(out.suffix+".part"); last=None
    h={"User-Agent":"Mozilla/5.0","Accept-Encoding":"identity"}
    for attempt in range(1,4):
        try:
            if part.exists():part.unlink()
            log(f"Connecting ({attempt}/3): {url}")
            with requests.get(url,stream=True,allow_redirects=True,headers=h,timeout=(30,300)) as r:
                log(f"HTTP {r.status_code}: {r.url}"); r.raise_for_status()
                try:total=int(r.headers.get("Content-Length","0"))
                except ValueError:total=0
                got=0; start=time.monotonic(); lastui=0
                with open(part,"wb") as f:
                    for chunk in r.iter_content(262144):
                        if not chunk:continue
                        f.write(chunk); got+=len(chunk); now=time.monotonic()
                        if now-lastui>.1:progress(got,total,got/max(now-start,.001)); lastui=now
            if not got:raise RuntimeError("Downloaded file is empty")
            part.replace(out); progress(got,total,got/max(time.monotonic()-start,.001)); return
        except Exception as e:
            last=e; log(f"Download failed: {e}")
            try:
                if part.exists():part.unlink()
            except OSError:pass
            if attempt<3:time.sleep(attempt*2)
    raise RuntimeError(f"Failed to download:\n{url}\n\nLast error:\n{last}")

def resolve_maria(item,log):
    log("Resolving official MariaDB download link...")
    r=requests.get(item["browse_url"],headers={"User-Agent":"Mozilla/5.0"},timeout=(30,60));r.raise_for_status()
    fn=item["filename"].lower()
    for href in re.findall(r'href=["\']([^"\']+)["\']',r.text,re.I):
        if fn in href.lower():return urljoin(r.url,href).replace("&amp;","&")
    for u in re.findall(r'https?://[^"\'<>\s]+',r.text):
        if fn in u.lower():return u.replace("&amp;","&")
    raise RuntimeError("Could not resolve MariaDB ZIP URL")

def find_local_archive(name):
    item = comps()[name]
    patterns = {
        "apache": ["apache.zip", "httpd-*.zip", "apache*.zip"],
        "php": ["php.zip", "php-*-nts-*.zip", "php-*.zip"],
        "mariadb": ["mariadb.zip", "mariadb-*-winx64*.zip", "mariadb-*.zip"],
        "postgresql": ["postgresql.zip", "postgresql-*.zip", "pg-*.zip"],
        "redis": ["redis.zip", "redis-*.zip"],
        "nginx": ["nginx.zip", "nginx-*.zip"],
        "nodejs": ["nodejs.zip", "node-*.zip"],
        "phpmyadmin": ["phpmyadmin.zip", "phpMyAdmin-*.zip", "phpmyadmin-*.zip"],
    }
    candidates = []
    for pattern in patterns.get(name, [item["archive"]]):
        candidates.extend(DOWNLOADS.glob(pattern))
    if not candidates:
        for p in DOWNLOADS.iterdir():
            if not p.is_file() or p.suffix.lower() != ".zip":
                continue
            n = p.name.lower()
            if name == "apache" and ("httpd" in n or "apache" in n):
                candidates.append(p)
            elif name == "php" and n.startswith("php-") and "phpmyadmin" not in n:
                candidates.append(p)
            elif name == "mariadb" and "mariadb" in n:
                candidates.append(p)
            elif name == "phpmyadmin" and "phpmyadmin" in n:
                candidates.append(p)
            elif name == "postgresql" and ("postgresql" in n or "pg" in n):
                candidates.append(p)
            elif name == "redis" and "redis" in n:
                candidates.append(p)
            elif name == "nginx" and "nginx" in n:
                candidates.append(p)
            elif name == "nodejs" and ("node" in n and "node_modules" not in n):
                candidates.append(p)
    seen = set()
    valid = []
    for p in candidates:
        key = str(p.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            if p.stat().st_size > 0 and zipfile.is_zipfile(p):
                valid.append(p)
        except OSError:
            pass
    valid.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return valid[0] if valid else None


def install_component(name,log,progress,item=None,prearchive=None):
    item = item or comps()[name]
    tmp = DOWNLOADS/(name+"_extract")
    shutil.rmtree(tmp,ignore_errors=True)
    tmp.mkdir(parents=True)
    arc = prearchive
    if arc is not None and not (arc.is_file() and zipfile.is_zipfile(arc)):
        arc = None
    if arc is None:
        arc = find_local_archive(name)
    if arc is not None:
        log(f"{name}: installing from local archive: {arc.name}")
        progress(arc.stat().st_size, arc.stat().st_size, 0)
    else:
        log(f"{name}: local archive not found in downloads")
        url = resolve_maria(item,log) if name=="mariadb" else item["url"]
        arc = DOWNLOADS/item["archive"]
        log(f"{name}: downloading because no local archive is available...")
        download(url,arc,progress,log)
    if not zipfile.is_zipfile(arc):
        raise RuntimeError(f"{name}: invalid ZIP archive: {arc.name}")
    log(f"Extracting {name} from {arc.name}...")
    progress(-1, 0, 0)
    with zipfile.ZipFile(arc) as z:
        z.extractall(tmp)
    if name=="apache":
        for p in tmp.iterdir():
            target=RUNTIME/p.name
            if target.exists():
                shutil.rmtree(target,ignore_errors=True) if target.is_dir() else target.unlink()
            shutil.move(str(p),str(target))
    elif name=="php":
        target=RUNTIME/"php"
        shutil.rmtree(target,ignore_errors=True)
        target.mkdir()
        for p in tmp.iterdir():
            shutil.move(str(p),str(target/p.name))
    elif name=="mariadb":
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        target=RUNTIME/"MariaDB"
        shutil.rmtree(target,ignore_errors=True)
        shutil.move(str(source),str(target))
    elif name=="postgresql":
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        target=RUNTIME/"PostgreSQL"
        shutil.rmtree(target,ignore_errors=True)
        shutil.move(str(source),str(target))
    elif name=="redis":
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        target=RUNTIME/"Redis"
        shutil.rmtree(target,ignore_errors=True)
        shutil.move(str(source),str(target))
    elif name=="nginx":
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        target=RUNTIME/"nginx"
        shutil.rmtree(target,ignore_errors=True)
        shutil.move(str(source),str(target))
    elif name=="nodejs":
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        target=RUNTIME/"Nodejs"
        shutil.rmtree(target,ignore_errors=True)
        shutil.move(str(source),str(target))
    elif name in ("php82", "php83", "php84"):
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        target=RUNTIME/("php"+name.replace("php", ""))
        shutil.rmtree(target,ignore_errors=True)
        shutil.move(str(source),str(target))
    elif name.startswith("python3"):
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        target=RUNTIME/("Python"+name.replace("python", ""))
        shutil.rmtree(target,ignore_errors=True)
        shutil.move(str(source),str(target))
    else:
        ds=[p for p in tmp.iterdir() if p.is_dir()]
        source=ds[0] if len(ds)==1 else tmp
        shutil.rmtree(PMA,ignore_errors=True)
        shutil.move(str(source),str(PMA))
        sample=PMA/"config.sample.inc.php"
        cfg=PMA/"config.inc.php"
        if sample.exists() and not cfg.exists():
            text=sample.read_text(encoding="utf-8",errors="replace")
            text=text.replace(
                "$cfg['blowfish_secret'] = '';",
                "$cfg['blowfish_secret'] = 'MiniServerV11PortableLocalSecretKey2026!';"
            )
            if "AllowNoPassword" not in text:
                text=text.replace(
                    "$cfg['Servers'][$i]['AllowNoPassword'] = false;",
                    "$cfg['Servers'][$i]['AllowNoPassword'] = true;"
                )
                if "AllowNoPassword" not in text:
                    text+="$cfg['Servers'][$i]['AllowNoPassword'] = true;\\n"
            cfg.write_text(text,encoding="utf-8")
    shutil.rmtree(tmp,ignore_errors=True)
    if not (APP_ROOT/item["expected"]).exists():
        raise RuntimeError(f"{name}: expected file missing after extracting {arc.name}")
    log(f"{name}: installed successfully from local archive")

class Services:
    def __init__(self,log):self.log=log;self.apache=None;self.db=None;self.php=None;self.pg=None;self.redis_proc=None;self.nginx=None;self.handles=[];self.ui_progress=None;self._port_cache={};self.node_servers={};self.node_routes={};self.node_processes={};self.sites_cache=[];self.py_servers={};self.py_routes={};self.php_extra={}
    @property
    def ad(self):return RUNTIME/"Apache24"
    @property
    def pd(self):return RUNTIME/"php"
    @property
    def md(self):return RUNTIME/"MariaDB"
    @property
    def pgd(self):return RUNTIME/"PostgreSQL"
    @property
    def rdd(self):return RUNTIME/"Redis"
    @property
    def nd(self):return RUNTIME/"nginx"
    @property
    def node_dir(self):
        bundled=RUNTIME/"Nodejs"
        if bundled.exists():return bundled
        import shutil as _sh
        sys_node=_sh.which("node")
        if sys_node:return Path(sys_node).parent
        return bundled
    def logfile(self,name):
        f=open(LOGS/name,"a",encoding="mbcs",errors="replace");self.handles.append(f);return f
    def _ensure_component(self, name):
        item = comps()[name]
        expected = APP_ROOT / item["expected"]
        if expected.exists():
            return
        self.log(f"{name} is not installed. Installing now...")
        def progress(got, total, speed):
            if total:
                pct = got / total * 100
                self.log(f"  {name}: {got/1048576:.1f}/{total/1048576:.1f} MB ({pct:.0f}%)")
            cb = getattr(self, "ui_progress", None)
            if cb:
                try:
                    cb(name, got, total)
                except Exception:
                    pass
        install_component(name, self.log, progress)
        if name == "nginx" and hasattr(self, "_nginx_feat"):
            try:
                del self._nginx_feat
            except Exception:
                pass
        cb = getattr(self, "ui_progress", None)
        if cb:
            try:
                cb(name, 0, 0)
            except Exception:
                pass
        if not expected.exists():
            raise RuntimeError(f"{name} installation failed: {expected} not found after install")
        self.log(f"{name} installed successfully")
    def _apache_modules(self):
        mods_dir = self.ad / "modules"
        wanted = [
            ("authn_core_module", "mod_authn_core.so"),
            ("authz_core_module", "mod_authz_core.so"),
            ("mime_module", "mod_mime.so"),
            ("dir_module", "mod_dir.so"),
            ("alias_module", "mod_alias.so"),
            ("log_config_module", "mod_log_config.so"),
            ("actions_module", "mod_actions.so"),
            ("cgi_module", "mod_cgi.so"),
            ("env_module", "mod_env.so"),
        ]
        lines = []
        for mod_name, so_file in wanted:
            if (mods_dir / so_file).exists():
                lines.append(f"LoadModule {mod_name} modules/{so_file}")
        return "\n".join(lines)
    PHP_INI_MANAGED = [
        ("display_errors", "bool"), ("display_startup_errors", "bool"),
        ("log_errors", "bool"), ("error_reporting", "text"),
        ("memory_limit", "text"), ("max_execution_time", "text"),
        ("max_input_time", "text"), ("upload_max_filesize", "text"),
        ("post_max_size", "text"), ("max_file_uploads", "text"),
        ("max_input_vars", "text"), ("default_charset", "text"),
        ("date.timezone", "text"), ("expose_php", "bool"),
        ("short_open_tag", "bool"), ("allow_url_fopen", "bool"),
        ("allow_url_include", "bool"), ("cgi.fix_pathinfo", "text"),
        ("opcache.enable", "bool"), ("opcache.memory_consumption", "text"),
        ("opcache.max_accelerated_files", "text"), ("opcache.validate_timestamps", "bool"),
        ("session.save_path", "text"), ("session.gc_maxlifetime", "text"),
        ("realpath_cache_size", "text"), ("sys_temp_dir", "text"),
    ]

    def php_ini_file(self):
        return self.pd / "php.ini"

    def php_ini_parse(self):
        """Returns (values dict, ext_enabled set, lines list). Missing file -> RuntimeError."""
        p = self.php_ini_file()
        if not p.is_file():
            raise RuntimeError("php.ini not found — is PHP installed?")
        values, exts, lines = {}, set(), []
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.strip()
            if not s or s.startswith(";") or s.startswith("#") or "=" not in s:
                lines.append((raw, None, None))
                continue
            key, val = s.split("=", 1)
            key, val = key.strip(), val.strip().strip("\"'")
            lines.append((raw, key, val))
            kl = key.lower()
            if kl in ("extension", "zend_extension"):
                exts.add(val.lower())
            else:
                values[kl] = val
        return values, exts, lines

    def php_ini_extensions(self):
        """Returns (available list, enabled set)."""
        ext_dir = self.pd / "ext"
        avail = set()
        try:
            if ext_dir.is_dir():
                for f in ext_dir.iterdir():
                    if f.suffix.lower() == ".dll" and f.is_file():
                        avail.add(f.name.lower())
        except OSError:
            pass
        try:
            _, enabled, _ = self.php_ini_parse()
        except RuntimeError:
            enabled = set()
        known = {"php_mysqli.dll", "php_pdo_mysql.dll", "php_mbstring.dll", "php_curl.dll",
                 "php_openssl.dll", "php_fileinfo.dll", "php_gd.dll", "php_intl.dll",
                 "php_zip.dll", "php_bz2.dll", "php_ftp.dll", "php_sockets.dll",
                 "php_opcache.dll", "php_pdo_sqlite.dll", "php_sqlite3.dll", "php_xml.dll",
                 "php_exif.dll", "php_gettext.dll"}
        return sorted(avail | (known & enabled) | (known & avail)), enabled

    def php_ini_save(self, values, extensions):
        p = self.php_ini_file()
        if not p.is_file():
            raise RuntimeError("php.ini not found — is PHP installed?")
        try:
            bak = p.with_suffix(".ini.bak")
            shutil.copy2(str(p), str(bak))
        except OSError:
            pass
        _, _, lines = self.php_ini_parse()
        managed = {k.lower() for k, _ in self.PHP_INI_MANAGED}
        out, written = [], set()
        for raw, key, _val in lines:
            if key is None:
                out.append(raw)
                continue
            kl = key.lower()
            if kl in ("extension", "zend_extension"):
                continue
            if kl in managed and kl in values:
                out.append(f"{key}={values[kl]}")
                written.add(kl)
            else:
                out.append(raw)
        for k, _ in self.PHP_INI_MANAGED:
            if k not in written and k in values:
                out.append(f"{k}={values[k]}")
        if extensions:
            out.append("; Extensions enabled via Faraja WebServer")
            for ext in sorted(extensions):
                if "opcache" in ext or "xdebug" in ext:
                    out.append(f"zend_extension={ext}")
                else:
                    out.append(f"extension={ext}")
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
        self.log("php.ini saved (backup: php.ini.bak)")

    def app_settings(self):
        try:
            return json.loads((APP_ROOT/"config"/"settings.json").read_text(encoding="utf-8"))
        except Exception:
            return {}
    def php_mode(self):
        return self.app_settings().get("php_mode", "dev")
    def dir_listing(self):
        return bool(self.app_settings().get("dir_listing", False))
    def set_sites(self, sites):
        try:
            self.sites_cache = [dict(s) for s in (sites or [])]
        except Exception:
            self.sites_cache = []
    @staticmethod
    def check_domain(domain):
        if not re.fullmatch(r"[A-Za-z0-9]([A-Za-z0-9.-]{0,61}[A-Za-z0-9])?", domain or ""):
            raise RuntimeError(f"Bad domain name: {domain}")
        return domain
    PHP_EXTRA_PORTS = {"8.2": 9174, "8.4": 9274}

    def default_php_ver(self):
        try:
            return self.env_active()[0] or "8.3"
        except Exception:
            return "8.3"

    def ensure_all_site_php(self):
        for s in getattr(self, "sites_cache", []):
            if s.get("type", "php") not in ("php", "static"):
                continue
            ver = (s.get("phpver") or "").strip()
            if not ver or ver == self.default_php_ver():
                continue
            try:
                self.ensure_site_php(ver)
            except Exception as e:
                self.log(f"Site PHP {ver} ERROR: {e}")

    def ensure_site_php(self, ver):
        """Make sure a side PHP runtime + persistent CGI exist for a site. Returns version dir or None for default."""
        if not ver or ver == self.default_php_ver():
            return None
        tag = "php" + ver.replace(".", "")
        if tag not in ("php82", "php83", "php84"):
            raise RuntimeError(f"Unsupported site PHP version: {ver} (use 8.2/8.3/8.4)")
        vdir = RUNTIME / ("php" + ver.replace(".", ""))
        if not (vdir / "php-cgi.exe").exists():
            info = comps().get("php_versions", {}).get(ver)
            if not info:
                raise RuntimeError(f"Unknown PHP version: {ver}")
            arc = DOWNLOADS / info["archive"]
            if not (arc.is_file() and zipfile.is_zipfile(arc)):
                self.log(f"Downloading PHP {ver} for site...")
                download(info["url"], arc,
                         lambda g, t, s: (self.ui_progress and self.ui_progress(f"php {ver}", g, t)),
                         self.log)
            install_component(tag, self.log,
                              lambda g, t, s: (self.ui_progress and self.ui_progress(f"php {ver}", g, t)),
                              prearchive=arc)
        main_ini = self.pd / "php.ini"
        vini = vdir / "php.ini"
        if main_ini.is_file() and not vini.is_file():
            try:
                shutil.copy2(str(main_ini), str(vini))
            except OSError:
                pass
        port = self.PHP_EXTRA_PORTS.get(ver)
        if port is None:
            raise RuntimeError(f"No CGI port mapped for PHP {ver}")
        proc = self.php_extra.get(ver)
        try:
            alive = proc is not None and proc.poll() is None
        except Exception:
            alive = False
        if not alive:
            f = self.logfile("php-process.log")
            proc = subprocess.Popen(
                [str(vdir / "php-cgi.exe"), "-b", f"127.0.0.1:{port}", "-c", str(vini if vini.is_file() else vdir)],
                cwd=vdir, stdout=f, stderr=f,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.php_extra[ver] = proc
            if not wait_port(port, 15):
                raise RuntimeError(f"PHP {ver} CGI did not start on port {port}")
            self.log(f"PHP {ver} CGI ready on port {port} for sites")
        return vdir

    def write_apache_vhosts(self):
        vdir = self.ad / "conf" / "vhosts"
        vdir.mkdir(parents=True, exist_ok=True)
        for old in vdir.glob("*.conf"):
            try:
                old.unlink()
            except OSError:
                pass
        a_port = CONFIG["apache_port"]
        listing = "+Indexes" if self.dir_listing() else "-Indexes"
        www_root = WWW.resolve().as_posix()
        (vdir / "000-default.conf").write_text(
            f'<VirtualHost 127.0.0.1:{a_port}>\n'
            f'    ServerName 127.0.0.1\n'
            f'    ServerAlias localhost\n'
            f'    DocumentRoot "{www_root}"\n'
            f'    <Directory "{www_root}">\n'
            f'        Require all granted\n'
            f'        AllowOverride All\n'
            f'        Options {listing} +FollowSymLinks\n'
            f'        DirectoryIndex index.html index.php index.htm\n'
            f'    </Directory>\n'
            f'</VirtualHost>\n', encoding="utf-8")
        for s in getattr(self, "sites_cache", []):
            if s.get("type", "php") in ("node", "python"):
                continue
            try:
                domain = self.check_domain(s.get("domain", ""))
            except RuntimeError:
                continue
            root_p = Path(s.get("root", ""))
            if not root_p.is_dir():
                self.log(f"Site '{s.get('name', domain)}': root folder is missing, vhost skipped")
                continue
            root = root_p.resolve().as_posix()
            site_php = (s.get("phpver") or "").strip()
            handler = ""
            if site_php and site_php != self.default_php_ver():
                tag = "php" + site_php.replace(".", "")
                vphp = (RUNTIME / ("php" + site_php.replace(".", ""))).resolve().as_posix()
                handler = (
                    f'    ScriptAlias /php-cgi-bin-{tag}/ "{vphp}/"\n'
                    f'    Action {tag}-handler /php-cgi-bin-{tag}/php-cgi.exe virtual\n'
                    f'    <FilesMatch "\\.php$">\n'
                    f'        SetHandler {tag}-handler\n'
                    f'    </FilesMatch>\n'
                )
            (vdir / f"{domain}.conf").write_text(
                f'<VirtualHost 127.0.0.1:{a_port}>\n'
                f'    ServerName {domain}\n'
                f'    DocumentRoot "{root}"\n'
                f'    <Directory "{root}">\n'
                f'        Require all granted\n'
                f'        AllowOverride All\n'
                f'        Options {listing} +FollowSymLinks\n'
                f'        DirectoryIndex index.html index.php index.htm\n'
                f'    </Directory>\n'
                f'{handler}</VirtualHost>\n', encoding="utf-8")
    def mkcert_domain(self, domain):
        self.check_domain(domain)
        mkcert = RUNTIME / "mkcert" / "mkcert.exe"
        if not mkcert.exists():
            raise RuntimeError("mkcert is not installed — press Setup SSL first")
        ssl_dir = APP_ROOT / "ssl"
        ssl_dir.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([str(mkcert), domain], capture_output=True, text=True, timeout=30,
                           cwd=str(ssl_dir),
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError("mkcert failed: " + ((r.stderr or "")[:200]))
        cert = ssl_dir / f"{domain}.pem"
        if not cert.is_file():
            raise RuntimeError(f"Certificate was not created for {domain}")
        self.log(f"SSL certificate issued: {domain}")
        return cert, ssl_dir / f"{domain}-key.pem"
    def write_configs(self):
        a=self.ad.resolve().as_posix(); w=WWW.resolve().as_posix(); p=PMA.resolve().as_posix()
        ph=self.pd.resolve().as_posix(); m=self.md.resolve().as_posix(); l=LOGS.resolve().as_posix()
        apache_modules = self._apache_modules()
        idx_opt = "+Indexes" if self.dir_listing() else "-Indexes"
        apache=f'''ServerRoot "{a}"
Listen 127.0.0.1:{CONFIG["apache_port"]}
ServerName 127.0.0.1:{CONFIG["apache_port"]}

{apache_modules}

TypesConfig conf/mime.types
DocumentRoot "{w}"

<Directory "{w}">
    Require all granted
    AllowOverride All
    Options {idx_opt} +FollowSymLinks
    DirectoryIndex index.html index.php index.htm
</Directory>

Alias /phpmyadmin "{p}"

<Directory "{p}">
    Require all granted
    AllowOverride None
    Options FollowSymLinks
    DirectoryIndex index.php
</Directory>

ScriptAlias /php-cgi-bin/ "{ph}/"
Action php-handler /php-cgi-bin/php-cgi.exe virtual
<FilesMatch "\\.php$">
    SetHandler php-handler
</FilesMatch>

IncludeOptional conf/vhosts/*.conf

ErrorLog "{l}/apache-error.log"
LogFormat "%h %l %u %t \\"%r\\" %>s %b" combined
CustomLog "{l}/apache-access.log" combined
LogLevel warn
'''
        (self.ad/"conf").mkdir(parents=True,exist_ok=True)
        (self.ad/"conf/httpd.conf").write_text(apache,encoding="utf-8")
        self.write_apache_vhosts()
        if self.php_mode() == "safe":
            php_err = "display_errors=Off\ndisplay_startup_errors=Off\nerror_reporting=E_ALL\n"
        else:
            php_err = "display_errors=On\ndisplay_startup_errors=On\nerror_reporting=E_ALL\n"
        php=f'''[PHP]
extension_dir="{ph}/ext"
extension=mysqli
extension=pdo_mysql
extension=mbstring
extension=curl
{php_err}log_errors=On
error_log="{l}/php-error.log"
session.save_path="{(APP_ROOT/"tmp").resolve().as_posix()}"
date.timezone=UTC
'''
        if self.pd.exists():
            (self.pd/"php.ini").write_text(php,encoding="utf-8")
        maria=f'''[mysqld]
basedir={m}
datadir={m}/data
port={CONFIG["mariadb_port"]}
bind-address=127.0.0.1
character-set-server=utf8mb4
collation-server=utf8mb4_general_ci
log_error={l}/mariadb-error.log
skip-name-resolve

[client]
port={CONFIG["mariadb_port"]}
'''
        self.md.mkdir(parents=True, exist_ok=True)
        (self.md/"my.ini").write_text(maria,encoding="utf-8")
        pma_cfg=PMA/"config.inc.php"
        if pma_cfg.exists():
            txt=pma_cfg.read_text(encoding="utf-8",errors="replace")
            txt=re.sub(r"\$cfg\['Servers'\]\[\$i\]\['AllowNoPassword'\]\s*=\s*(?:true|false)\s*;", "", txt)
            txt+="\n$cfg['Servers'][$i]['AllowNoPassword'] = true;\n"
            pma_cfg.write_text(txt,encoding="utf-8")
    def _alive(self, proc):
        try:
            return proc is not None and proc.poll() is None
        except Exception:
            return False
    def _port_cached(self, port, ttl=8):
        now = time.monotonic()
        hit = self._port_cache.get(port)
        if hit and now - hit[0] < ttl:
            return hit[1]
        val = port_open(port)
        self._port_cache[port] = (now, val)
        return val
    def _drop_port_cache(self, port):
        self._port_cache.pop(port, None)
    def arun(self):
        if self._alive(self.apache):return True
        return self._port_cached(CONFIG["apache_port"])
    def drun(self):
        if self._alive(self.db):return True
        return self._port_cached(CONFIG["mariadb_port"], 15)
    def prun(self):
        if self._alive(self.php):return True
        return self._port_cached(CONFIG["php_cgi_port"])
    def start_php(self):
        if self.prun():self.log("PHP CGI is already running");return
        self.write_configs();exe=self.pd/"php-cgi.exe"
        if not exe.exists():raise RuntimeError("PHP is not installed")
        f=self.logfile("php-process.log")
        self.php=subprocess.Popen([str(exe),"-b",f'127.0.0.1:{CONFIG["php_cgi_port"]}',"-c",str(self.pd/"php.ini")],cwd=self.pd,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["php_cgi_port"],15):raise RuntimeError("PHP CGI did not start; see PHP Error / Process logs")
        self._drop_port_cache(CONFIG["php_cgi_port"])
        self.log("PHP CGI started")
    def stop_php(self):
        self._drop_port_cache(CONFIG["php_cgi_port"])
        stop_proc(self.php)
        self.php=None
        stopped, foreign = stop_named_processes_on_port(
            CONFIG["php_cgi_port"], {"php-cgi.exe"}
        )
        if foreign:
            detail = ", ".join(f"{name or 'unknown'} (PID {pid})" for pid, name in foreign)
            raise RuntimeError(
                f"PHP port {CONFIG['php_cgi_port']} is occupied by another program: {detail}"
            )
        if not wait_port_closed(CONFIG["php_cgi_port"], 12):
            raise RuntimeError("PHP CGI could not be stopped on port %s" % CONFIG["php_cgi_port"])
        self.log("PHP CGI stopped")
    def start_apache(self):
        # Apache and Nginx may run side by side on different ports
        # (Nginx proxies to Apache). Only identical ports conflict.
        if CONFIG["apache_port"] == CONFIG["nginx_port"] and self.nginxrun():
            raise RuntimeError(
                f"Apache and Nginx use the same port {CONFIG['apache_port']}. "
                "Change apache_port or nginx_port in config/server.json.")
        if self.arun():
            owners = port_owners(CONFIG["apache_port"])
            apache_names = {"httpd.exe", "apache.exe"}
            foreign = [(pid, name) for pid, name in owners if name.lower() not in apache_names]
            if foreign:
                detail = ", ".join(f"{name or 'unknown'} (PID {pid})" for pid, name in foreign)
                raise RuntimeError(
                    f"Port {CONFIG['apache_port']} is occupied by another program: {detail}. "
                    "Stop that program or change apache_port in config/server.json."
                )
            self.log("Apache is already running: " + ", ".join(f"{name} PID {pid}" for pid, name in owners))
            return
        if not self.prun():self.start_php()
        try:
            pid_file = self.ad / "logs" / "httpd.pid"
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass
        self.write_configs();exe=self.ad/"bin/httpd.exe"
        if not exe.exists():raise RuntimeError("Apache is not installed")
        testlog=self.logfile("apache-process.log")
        test=subprocess.run([str(exe),"-t","-f",str(self.ad/"conf/httpd.conf")],cwd=self.ad,stdout=testlog,stderr=testlog,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if test.returncode!=0:raise RuntimeError("Apache configuration test failed; see Process / Init log")
        f=self.logfile("apache-process.log")
        self.apache=subprocess.Popen([str(exe),"-f",str(self.ad/"conf/httpd.conf"),"-DFOREGROUND"],cwd=self.ad,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["apache_port"],15):
            raise RuntimeError("Apache did not start; see logs")
        try:
            r = requests.get(f'http://127.0.0.1:{CONFIG["apache_port"]}/', timeout=5)
            self.log(f"Apache HTTP check: {r.status_code}")
        except Exception as e:
            self.log(f"Apache HTTP check failed: {e}")
        self._drop_port_cache(CONFIG["apache_port"])
        self.log("Apache started")
    def stop_apache(self):
        self._drop_port_cache(CONFIG["apache_port"])
        exe=self.ad/"bin/httpd.exe"; conf=self.ad/"conf/httpd.conf"
        if not (web_server_running("apache") or self.arun()):
            self.apache=None; self.log("Apache is already stopped"); return
        if exe.exists():
            try:
                subprocess.run([str(exe),"-k","stop","-f",str(conf)],cwd=self.ad,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            except Exception as e:self.log(f"Apache control stop warning: {e}")
        stop_proc(self.apache,2); self.apache=None
        pids=stop_web_server_processes("apache")
        if pids:self.log("Stopped Apache process(es): "+", ".join(map(str,pids)))
        if self.arun():
            owners=port_owners(CONFIG["apache_port"])
            detail=", ".join(f"{name or 'unknown'} (PID {pid})" for pid,name in owners)
            raise RuntimeError(f"Apache could not be stopped on port {CONFIG['apache_port']}. Listener: {detail or 'unknown'}")
        try:
            pid_file=self.ad/"logs/httpd.pid"
            if pid_file.exists():pid_file.unlink()
        except Exception:pass
        self.log("Apache stopped")
    def initialize_db(self):
        data=self.md/"data";data.mkdir(parents=True,exist_ok=True)
        installer=self.md/"bin/mariadb-install-db.exe"
        if not installer.exists():installer=self.md/"bin/mysql_install_db.exe"
        if not installer.exists():raise RuntimeError("MariaDB install utility was not found")
        f=self.logfile("mariadb-init.log");self.log("Initializing MariaDB...")
        attempts=[
            [str(installer),f"--datadir={data.resolve()}"]
        ]
        for cmd in attempts:
            result=subprocess.run(cmd,cwd=self.md,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if result.returncode==0:return
        raise RuntimeError("MariaDB initialization failed; open Process / Init and MariaDB Error logs")
    def _setup_pma_storage(self):
        pma_cfg=PMA/"config.inc.php"
        if not pma_cfg.exists():return
        txt=pma_cfg.read_text(encoding="utf-8",errors="replace")
        if "pmadb" not in txt or "//$cfg" in txt or "// $cfg['Servers'][$i]['pmadb']" in txt:
            sql_file=PMA/"sql/create_tables.sql"
            if sql_file.exists():
                mysql=self.md/"bin/mysql.exe"
                if mysql.exists():
                    try:
                        sql=sql_file.read_text(encoding="utf-8",errors="replace")
                        sql=sql.replace("`pma`@localhost","`root`@localhost")
                        result=subprocess.run(
                            [str(mysql),"-u","root","--port",str(CONFIG["mariadb_port"]),"-e",sql],
                            capture_output=True,text=True,timeout=30,
                            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)
                        )
                        if result.returncode==0:
                            self.log("phpMyAdmin configuration storage database created")
                        else:
                            self.log("phpMyAdmin storage DB setup skipped: "+result.stderr.strip()[:200])
                    except Exception as e:
                        self.log("phpMyAdmin storage DB setup error: "+str(e)[:200])
            txt=pma_cfg.read_text(encoding="utf-8",errors="replace")
            txt=txt.replace("// $cfg['Servers'][$i]['controluser'] = 'pma';","$cfg['Servers'][$i]['controluser'] = 'root';")
            txt=txt.replace("// $cfg['Servers'][$i]['controlpass'] = 'pmapass';","$cfg['Servers'][$i]['controlpass'] = '';")
            for key in ['pmadb','bookmarktable','relation','table_info','table_coords','pdf_pages','column_info','history','table_uiprefs','tracking','userconfig','recent','favorite','users','usergroups','navigationhiding','savedsearches','central_columns','designer_settings','export_templates']:
                txt=txt.replace(f"// $cfg['Servers'][$i]['{key}']","$cfg['Servers'][$i]['{key}']")
            pma_cfg.write_text(txt,encoding="utf-8")
    def start_db(self):
        if self.drun():self.log("MariaDB is already running");return
        self.write_configs();exe=self.md/"bin/mariadbd.exe"
        if not exe.exists():raise RuntimeError("MariaDB is not installed")
        if not (self.md/"data/mysql").exists():self.initialize_db()
        f=self.logfile("mariadb-process.log")
        self.db=subprocess.Popen([str(exe),f'--defaults-file={self.md/"my.ini"}'],cwd=self.md,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["mariadb_port"],20):raise RuntimeError("MariaDB did not start; see MariaDB Error and Process / Init logs")
        self._drop_port_cache(CONFIG["mariadb_port"])
        self.log("MariaDB started")
        try: self._setup_pma_storage()
        except Exception: pass
    def stop_db(self):
        self._drop_port_cache(CONFIG["mariadb_port"])
        stop_proc(self.db,10)
        self.db=None
        stopped, foreign = stop_named_processes_on_port(
            CONFIG["mariadb_port"], {"mariadbd.exe", "mysqld.exe", "mariadb.exe", "mysql.exe"}
        )
        if stopped:
            self.log("Stopped MariaDB listener(s): " + ", ".join(f"{n} PID {pid}" for pid, n in stopped))
        if foreign:
            detail = ", ".join(f"{name or 'unknown'} (PID {pid})" for pid, name in foreign)
            self.log(
                f"Port {CONFIG['mariadb_port']} is occupied by another program: {detail}. "
                "It was not terminated."
            )
        if not wait_port_closed(CONFIG["mariadb_port"], 12):
            raise RuntimeError("MariaDB could not be stopped on port %s" % CONFIG["mariadb_port"])
        self.log("MariaDB stopped")
    def pgrun(self):
        if self._alive(self.pg):return True
        return self._port_cached(CONFIG["postgresql_port"], 15)
    def initialize_pg(self):
        data=self.pgd/"data";data.mkdir(parents=True,exist_ok=True)
        exe=self.pgd/"bin/initdb.exe"
        if not exe.exists():raise RuntimeError("PostgreSQL initdb not found")
        f=self.logfile("postgresql-init.log");self.log("Initializing PostgreSQL...")
        env=os.environ.copy()
        env["PATH"]=str(self.pgd/"lib")+";"+str(self.pgd/"bin")+";"+env.get("PATH","")
        result=subprocess.run([str(exe),"-D",str(data.resolve()),"--encoding=UTF8","--locale=C"],
            cwd=self.pgd,stdout=f,stderr=f,env=env,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if result.returncode!=0:raise RuntimeError("PostgreSQL initialization failed; see Process / Init log")
        self.log("PostgreSQL initialized")
    def start_pg(self):
        if self.pgrun():self.log("PostgreSQL is already running");return
        self._ensure_component("postgresql")
        exe=self.pgd/"bin/pg_ctl.exe"
        data=self.pgd/"data"
        if not data.exists():self.initialize_pg()
        env=os.environ.copy()
        env["PATH"]=str(self.pgd/"lib")+";"+str(self.pgd/"bin")+";"+env.get("PATH","")
        env["PGLIB"]=str(self.pgd/"lib")
        self.pg=subprocess.Popen([str(exe),"start","-D",str(data.resolve()),"-w",
            "-l",str((LOGS/"postgresql-process.log").resolve())],
            cwd=self.pgd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            env=env,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["postgresql_port"],20):raise RuntimeError("PostgreSQL did not start; see Process / Init log")
        self._drop_port_cache(CONFIG["postgresql_port"])
        self.log("PostgreSQL started")
    def stop_pg(self):
        self._drop_port_cache(CONFIG["postgresql_port"])
        stop_proc(self.pg,10)
        self.pg=None
        exe=self.pgd/"bin/pg_ctl.exe"
        if exe.exists():
            data=self.pgd/"data"
            subprocess.run([str(exe),"stop","-D",str(data.resolve()),"-m","fast"],
                cwd=self.pgd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        stopped, foreign = stop_named_processes_on_port(
            CONFIG["postgresql_port"], {"postgres.exe", "pg_ctl.exe"}
        )
        if stopped:
            self.log("Stopped PostgreSQL listener(s): " + ", ".join(f"{n} PID {pid}" for pid, n in stopped))
        if foreign:
            detail = ", ".join(f"{name or 'unknown'} (PID {pid})" for pid, name in foreign)
            self.log(f"Port {CONFIG['postgresql_port']} is occupied by another program: {detail}.")
        if not wait_port_closed(CONFIG["postgresql_port"], 12):
            raise RuntimeError("PostgreSQL could not be stopped on port %s" % CONFIG["postgresql_port"])
        self.log("PostgreSQL stopped")
    def redisrun(self):
        if self._alive(self.redis_proc):return True
        return self._port_cached(CONFIG["redis_port"], 15)
    def redis_conf(self):
        try:
            d = json.loads((APP_ROOT/"config"/"redis.json").read_text(encoding="utf-8"))
            if not isinstance(d, dict):
                d = {}
        except Exception:
            d = {}
        d.setdefault("bind", "127.0.0.1")
        d.setdefault("password", "")
        return d
    def start_redis(self):
        if self.redisrun():self.log("Redis is already running");return
        self._ensure_component("redis")
        exe=self.rdd/"redis-server.exe"
        f=self.logfile("redis-process.log")
        rc = self.redis_conf()
        args=[str(exe),"--port",str(CONFIG["redis_port"]),"--bind",rc.get("bind") or "127.0.0.1",
              "--loglevel","warning"]
        if rc.get("password"):
            args += ["--requirepass", rc["password"]]
        self.redis_proc=subprocess.Popen(args,
            cwd=self.rdd,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["redis_port"],10):raise RuntimeError("Redis did not start; see Process / Init log")
        self._drop_port_cache(CONFIG["redis_port"])
        self.log("Redis started on port %s" % CONFIG["redis_port"])
    def stop_redis(self):
        self._drop_port_cache(CONFIG["redis_port"])
        stop_proc(self.redis_proc,5)
        self.redis_proc=None
        stopped, foreign = stop_named_processes_on_port(
            CONFIG["redis_port"], {"redis-server.exe"}
        )
        if stopped:
            self.log("Stopped Redis listener(s): " + ", ".join(f"{n} PID {pid}" for pid, n in stopped))
        if not wait_port_closed(CONFIG["redis_port"], 8):
            raise RuntimeError("Redis could not be stopped on port %s" % CONFIG["redis_port"])
        self.log("Redis stopped")
    def nginxrun(self):
        if self._alive(self.nginx):return True
        return self._port_cached(CONFIG["nginx_port"])
    def start_nginx(self):
        # Nginx proxies to Apache, so both may run together on different ports.
        if CONFIG["nginx_port"] == CONFIG["apache_port"]:
            raise RuntimeError(
                f"Nginx and Apache use the same port {CONFIG['nginx_port']}. "
                "Change apache_port or nginx_port in config/server.json.")
        if self.nginxrun():self.log("Nginx is already running");return
        self._ensure_component("nginx")
        exe=self.nd/"nginx.exe"
        self._write_nginx_conf()
        f=self.logfile("nginx-process.log")
        self.nginx=subprocess.Popen([str(exe),"-c",str((self.nd/"conf/nginx.conf").resolve())],
            cwd=self.nd,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["nginx_port"],10):raise RuntimeError("Nginx did not start; see Process / Init log")
        self._drop_port_cache(CONFIG["nginx_port"])
        self.log(f"Nginx started on port {CONFIG['nginx_port']}, proxying to Apache on port {CONFIG['apache_port']}")
    def stop_nginx(self):
        self._drop_port_cache(CONFIG["nginx_port"])
        exe=self.nd/"nginx.exe"; conf=self.nd/"conf/nginx.conf"
        if not (web_server_running("nginx") or self.nginxrun()):
            self.nginx=None; self.log("Nginx is already stopped"); return
        if exe.exists():
            try:
                subprocess.run([str(exe),"-p",str(self.nd),"-c",str(conf),"-s","stop"],cwd=self.nd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            except Exception as e:self.log(f"Nginx control stop warning: {e}")
        stop_proc(self.nginx,2); self.nginx=None
        pids=stop_web_server_processes("nginx")
        if pids:self.log("Stopped Nginx process(es): "+", ".join(map(str,pids)))
        if self.nginxrun():
            owners=port_owners(CONFIG["nginx_port"])
            detail=", ".join(f"{name or 'unknown'} (PID {pid})" for pid,name in owners)
            raise RuntimeError(f"Nginx could not be stopped on port {CONFIG['nginx_port']}. Listener: {detail or 'unknown'}")
        self.log("Nginx stopped")
    def nginx_features(self):
        if hasattr(self, "_nginx_feat"):
            return self._nginx_feat
        feat = {"http_v3": False, "brotli": False}
        try:
            exe = self.nd / "nginx.exe"
            if exe.exists():
                r = subprocess.run([str(exe), "-V"], capture_output=True, text=True, timeout=10,
                                   cwd=str(self.nd),
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                out = (r.stdout or "") + (r.stderr or "")
                feat["http_v3"] = "http_v3" in out
                feat["brotli"] = "brotli" in out
        except Exception:
            pass
        self._nginx_feat = feat
        return feat
    def _write_nginx_conf(self):
        www_path = WWW.resolve().as_posix()
        a_port = CONFIG["apache_port"]
        n_port = CONFIG["nginx_port"]
        log_path = LOGS.resolve().as_posix()
        ssl_dir = APP_ROOT / "ssl"
        ssl_cert = ssl_dir / "localhost.pem"
        ssl_key = ssl_dir / "localhost-key.pem"
        feat = self.nginx_features()
        quic443 = "\n        listen 443 quic reuseport;" if feat["http_v3"] else ""
        brotli_block = ""
        if feat["brotli"]:
            brotli_block = ("\n    brotli on;\n    brotli_comp_level 6;\n"
                            "    brotli_types text/plain text/css application/json application/javascript text/xml;")
        ssl_block = ""
        if ssl_cert.exists() and ssl_key.exists():
            ssl_block = f'''
    server {{
        listen 443 ssl http2;{quic443}
        server_name localhost;
        ssl_certificate "{ssl_cert.resolve().as_posix()}";
        ssl_certificate_key "{ssl_key.resolve().as_posix()}";
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        location / {{
            proxy_pass http://127.0.0.1:{a_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
    }}'''
        node_blocks = ""
        for nport in sorted(self.node_routes):
            node_blocks += f'''
        location /node/{nport}/ {{
            proxy_pass http://127.0.0.1:{nport}/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }}'''
        for pport in sorted(self.py_routes):
            node_blocks += f'''
        location /py/{pport}/ {{
            proxy_pass http://127.0.0.1:{pport}/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }}'''
        site_blocks = ""
        for s in getattr(self, "sites_cache", []):
            try:
                domain = self.check_domain(s.get("domain", ""))
            except RuntimeError:
                continue
            typ = s.get("type", "php")
            ssl_listen = ""
            ssl_lines = ""
            if s.get("https"):
                cert = ssl_dir / f"{domain}.pem"
                key = ssl_dir / f"{domain}-key.pem"
                if cert.is_file() and key.is_file():
                    ssl_listen = "\n        listen 443 ssl http2;" + quic443
                    ssl_lines = (f'\n        ssl_certificate "{cert.resolve().as_posix()}";'
                                 f'\n        ssl_certificate_key "{key.resolve().as_posix()}";'
                                 '\n        ssl_protocols TLSv1.2 TLSv1.3;')
            if typ in ("node", "python"):
                try:
                    sport = int(s.get("port") or 3000)
                except (TypeError, ValueError):
                    sport = 3000
                loc = f'''location / {{
                proxy_pass http://127.0.0.1:{sport};
                proxy_set_header Host $host;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
            }}'''
            elif typ == "static":
                rpath = Path(s.get("root", "")).resolve().as_posix()
                loc = f'''location / {{
                root {rpath};
                try_files $uri $uri/ =404;
            }}'''
            else:
                loc = f'''location / {{
                proxy_pass http://127.0.0.1:{a_port};
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }}'''
            site_blocks += f'''
    server {{
        listen 80;{ssl_listen}
        server_name {domain};{ssl_lines}
        {loc}
    }}'''
        conf = f'''worker_processes 1;
events {{ worker_connections 1024; }}
http {{
    include mime.types;
    default_type application/octet-stream;
    error_log "{log_path}/nginx-error.log" warn;
    sendfile on;
    etag on;
    keepalive_timeout 65;
    client_max_body_size 64m;
    proxy_connect_timeout 60s;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_min_length 256;
    gzip_types text/plain text/css application/json application/javascript text/xml;{brotli_block}
    server {{
        listen {n_port};
        server_name localhost;{node_blocks}
        access_log "{log_path}/nginx-access.log" combined;
        location / {{
            proxy_pass http://127.0.0.1:{a_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
        location ~* \\.(css|js|png|jpg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
            root {www_path};
            expires 1d;
            add_header Cache-Control "public, immutable";
        }}
    }}{site_blocks}{ssl_block}
}}'''
        conf_dir = self.nd / "conf"
        conf_dir.mkdir(parents=True, exist_ok=True)
        (conf_dir / "nginx.conf").write_text(conf, encoding="utf-8")
    def setup_ssl(self):
        mkcert = RUNTIME / "mkcert" / "mkcert.exe"
        if not mkcert.exists():
            self.log("mkcert is not installed. Downloading...")
            mkcert_dir = RUNTIME / "mkcert"
            mkcert_dir.mkdir(parents=True, exist_ok=True)
            url = "https://dl.filippo.io/mkcert/v1.4.4?for=windows/amd64"
            self.log("Downloading mkcert from " + url)
            r = requests.get(url, timeout=60, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            mkcert.write_bytes(r.content)
            self.log("mkcert downloaded: %d bytes" % len(r.content))
        ssl_dir = APP_ROOT / "ssl"
        ssl_dir.mkdir(parents=True, exist_ok=True)
        cert = ssl_dir / "localhost.pem"
        key = ssl_dir / "localhost-key.pem"
        self.log("Installing mkcert root CA...")
        result = subprocess.run([str(mkcert), "-install"],
            capture_output=True, text=True, timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode != 0:
            self.log("mkcert -install warning: " + result.stderr.strip()[:200])
        self.log("Generating SSL certificate for localhost...")
        result = subprocess.run(
            [str(mkcert), "localhost", "127.0.0.1", "::1"],
            capture_output=True, text=True, timeout=30,
            cwd=str(ssl_dir),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode != 0:
            raise RuntimeError("mkcert failed: " + result.stderr.strip()[:300])
        self.log("SSL certificate created: " + str(cert))
        if self.nginxrun():
            self._write_nginx_conf()
            self.log("Nginx config updated with SSL")
    def get_node_exe(self):
        nd=self.node_dir
        exe=nd/"node.exe"
        if exe.exists():return str(exe)
        import shutil
        sys_node=shutil.which("node")
        if sys_node:return sys_node
        raise RuntimeError("Node.js is not installed")
    def get_npx_exe(self):
        nd=self.node_dir
        npx=nd/"npx.cmd"
        if npx.exists():return str(npx)
        npx=nd/"npx.exe"
        if npx.exists():return str(npx)
        import shutil
        sys_npx=shutil.which("npx")
        if sys_npx:return sys_npx
        raise RuntimeError("npx is not found")
    def install_tsx(self):
        try:
            npx=self.get_npx_exe()
            result=subprocess.run([npx,"--yes","tsx","--version"],
                capture_output=True,text=True,timeout=60,
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            return result.returncode==0
        except Exception:
            return False
    def run_script(self, script_path):
        p=Path(script_path)
        if not p.exists():raise RuntimeError(f"Script not found: {script_path}")
        if p.suffix.lower()==".ts":
            npx=self.get_npx_exe()
            cmd=[npx,"--yes","tsx",str(p.resolve())]
        elif p.suffix.lower()==".js":
            node=self.get_node_exe()
            cmd=[node,str(p.resolve())]
        else:
            raise RuntimeError(f"Unsupported script type: {p.suffix}")
        self.log(f"Running script: {p.name}")
        f=self.logfile("node-process.log")
        proc=subprocess.Popen(cmd,cwd=str(p.parent),stdout=f,stderr=f,
            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        self.log(f"Script started: {p.name} (PID {proc.pid})")
        self.node_processes[proc.pid] = {"script": p.name, "path": str(p.resolve()),
                                         "started": time.strftime("%Y-%m-%d %H:%M:%S"), "proc": proc}
        return proc
    def node_server_running(self, name):
        info = self.node_servers.get(name)
        try:
            return info is not None and info["proc"].poll() is None
        except Exception:
            return False
    def node_server_start(self, name, directory, entry, port):
        self._ensure_component("nodejs")
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise RuntimeError(f"Bad Node.js port: {port}")
        self.node_server_stop(name, quiet=True)
        entry_path = Path(directory) / entry
        if not entry_path.exists():
            raise RuntimeError(f"Entry not found: {entry_path}")
        if entry_path.suffix.lower() == ".ts":
            cmd = [self.get_npx_exe(), "--yes", "tsx", str(entry_path.resolve())]
        elif entry_path.suffix.lower() == ".js":
            cmd = [self.get_node_exe(), str(entry_path.resolve())]
        else:
            raise RuntimeError(f"Unsupported entry type: {entry_path.suffix} (use .js or .ts)")
        env = os.environ.copy()
        env["PORT"] = str(port)
        f = self.logfile("node-process.log")
        proc = subprocess.Popen(cmd, cwd=str(Path(directory).resolve()), stdout=f, stderr=f,
                                env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.node_servers[name] = {"proc": proc, "dir": str(directory), "entry": entry,
                                   "port": port, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
        self.node_processes[proc.pid] = {"script": f"{name}: {entry}", "path": str(entry_path.resolve()),
                                         "started": self.node_servers[name]["started"], "proc": proc}
        self.node_routes[port] = name
        self._write_nginx_conf()
        if not wait_port(port, 15):
            raise RuntimeError(f"Node.js server '{name}' did not open port {port}; see Process / Init log")
        self.log(f"Node.js server '{name}' started on port {port} (PID {proc.pid}); route: /node/{port}/")
        return proc
    def node_server_stop(self, name, quiet=False):
        info = self.node_servers.pop(name, None)
        if info is None:
            if not quiet:
                self.log(f"Node.js server '{name}' is not running")
            return
        try:
            kill_pid_tree(info["proc"].pid)
        except Exception:
            pass
        self.node_processes.pop(info["proc"].pid, None)
        self.node_routes.pop(info["port"], None)
        self._write_nginx_conf()
        wait_port_closed(info["port"], 8)
        if not quiet:
            self.log(f"Node.js server '{name}' stopped")
    def node_servers_stop_all(self):
        for name in list(self.node_servers.keys()):
            try:
                self.node_server_stop(name, quiet=True)
            except Exception:
                pass
        self.log("All Node.js servers stopped")
    def docker_check(self):
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False
    def docker_install(self):
        self.log("Docker not found. Please install Docker Desktop from https://docker.com/products/docker-desktop")
        raise RuntimeError(lang.t("docker_not_found"))
    def start_docker(self):
        if not self.docker_check():
            self.docker_install()
        self.log("Docker is available")
    def stop_docker(self):
        self.log("Docker containers can be stopped with: docker stop <container>")
    def dockerun(self):
        return self.docker_check()
    def docker_ps(self):
        try:
            r = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"],
                               capture_output=True, text=True, timeout=15,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError:
            raise RuntimeError(lang.t("dock_notfound"))
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200] or "docker ps failed")
        rows = []
        for line in r.stdout.splitlines():
            parts = (line.split("|") + ["", "", "", ""])[:4]
            if parts[0]:
                rows.append(parts)
        return rows
    def docker_ctl(self, action, name):
        r = subprocess.run(["docker", action, name], capture_output=True, text=True, timeout=60,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:200] or f"docker {action} failed")
        self.log(f"docker {action} {name}: OK")
    def _compose_base(self, compose_file):
        p = Path(compose_file)
        if not p.is_file():
            raise RuntimeError(f"Compose file not found: {compose_file}")
        return ["docker", "compose", "-f", str(p.resolve())], str(p.parent.resolve())
    def docker_compose(self, action, compose_file):
        if action not in ("up", "down", "restart", "pull", "build"):
            raise RuntimeError(f"Bad compose action: {action}")
        base, cwd = self._compose_base(compose_file)
        cmd = base + (["up", "-d"] if action == "up" else [action])
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()[-2000:]
        if r.returncode != 0:
            raise RuntimeError(f"docker compose {action} failed:\n{out[-500:]}")
        self.log(f"docker compose {action}: OK")
        return out
    def docker_compose_logs(self, compose_file, tail=200):
        base, cwd = self._compose_base(compose_file)
        try:
            tail = max(10, int(tail))
        except (TypeError, ValueError):
            tail = 200
        r = subprocess.run(base + ["logs", f"--tail={tail}", "--no-color"], cwd=cwd,
                           capture_output=True, text=True, timeout=60,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:300] or "docker compose logs failed")
        return r.stdout
    def docker_images(self):
        try:
            r = subprocess.run(["docker", "images", "--format", "{{.Repository}}|{{.Tag}}|{{.ID}}|{{.Size}}"],
                               capture_output=True, text=True, timeout=30,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError:
            raise RuntimeError(lang.t("dock_notfound"))
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200] or "docker images failed")
        rows = []
        for line in r.stdout.splitlines():
            parts = (line.split("|") + ["", "", "", ""])[:4]
            if parts[0]:
                rows.append(parts)
        return rows
    def docker_rmi(self, image_id):
        r = subprocess.run(["docker", "rmi", image_id], capture_output=True, text=True, timeout=120,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:200] or "docker rmi failed")
        self.log(f"docker rmi {image_id}: OK")
    def pg_conf_path(self):
        return self.pgd / "data" / "postgresql.conf"
    def pg_apply_port(self, port):
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise RuntimeError(f"Bad PostgreSQL port: {port}")
        conf = self.pg_conf_path()
        if conf.is_file():
            text = conf.read_text(encoding="utf-8", errors="replace")
            new_text, n = re.subn(r"(?m)^#?\s*port\s*=.*$", f"port = {port}", text, count=1)
            if n == 0:
                new_text = text + f"\nport = {port}\n"
            conf.write_text(new_text, encoding="utf-8")
            self.log(f"postgresql.conf: port = {port}")
        CONFIG["postgresql_port"] = port
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
        except Exception as e:
            self.log(f"server.json save warning: {e}")
        if self.pgrun():
            self.log("Restarting PostgreSQL to apply new port...")
            self.stop_pg()
            self.start_pg()
    def _pg_run(self, admin_user, admin_pass, dbname, sql):
        psql = self.pgd / "bin" / "psql.exe"
        if not psql.exists():
            raise RuntimeError("psql.exe not found — is PostgreSQL installed?")
        env = os.environ.copy()
        if admin_pass:
            env["PGPASSWORD"] = admin_pass
        r = subprocess.run([str(psql), "-U", admin_user, "-h", "127.0.0.1",
                            "-p", str(CONFIG["postgresql_port"]), "-d", dbname,
                            "-v", "ON_ERROR_STOP=1", "-c", sql],
                           capture_output=True, text=True, timeout=30, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:300] or "psql failed")
        return (r.stdout or "").strip()
    def pg_set_password(self, admin_user, admin_pass, target, new_pass):
        if not target or not new_pass:
            raise RuntimeError("Target user and new password are required")
        safe_target = '"' + target.replace('"', '""') + '"'
        safe_pass = new_pass.replace("'", "''")
        self._pg_run(admin_user, admin_pass, "postgres",
                     f"ALTER USER {safe_target} WITH PASSWORD '{safe_pass}';")
        self.log(f"PostgreSQL password set for user {target}")
    def pg_create_db(self, admin_user, admin_pass, dbname):
        if not dbname:
            raise RuntimeError("Database name is required")
        safe_db = '"' + dbname.replace('"', '""') + '"'
        self._pg_run(admin_user, admin_pass, "postgres", f"CREATE DATABASE {safe_db};")
        self.log(f"PostgreSQL database created: {dbname}")
    def proc_list(self):
        ps = ("Get-CimInstance Win32_Process | ForEach-Object { \"{0}|{1}|{2}|{3}\" -f $_.Name,$_.ProcessId,$_.ParentProcessId,$_.WorkingSetSize }; "
              "'---CONN---'; "
              "Get-NetTCPConnection -State Listen | ForEach-Object { \"{0}|{1}\" -f $_.LocalPort,$_.OwningProcess }")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True,
                           text=True, timeout=30,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError("process list failed")
        procs, ports, section = [], {}, 0
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line == "---CONN---":
                section = 1
                continue
            p = line.split("|")
            if section == 0:
                try:
                    procs.append({"name": p[0], "pid": int(p[1]), "ppid": int(p[2]),
                                  "mem": int(p[3]) // 1048576})
                except (ValueError, IndexError):
                    continue
            else:
                try:
                    ports.setdefault(int(p[1]), []).append(p[0])
                except (ValueError, IndexError):
                    continue
        for pr in procs:
            pr["ports"] = ",".join(ports.get(pr["pid"], []))
        procs.sort(key=lambda x: -x["mem"])
        return procs
    def _my_run(self, user, passwd, db, sql):
        mysql = self.md / "bin" / "mysql.exe"
        if not mysql.exists():
            raise RuntimeError("mysql.exe not found — is MariaDB installed?")
        cmd = [str(mysql), "-u", user or "root", "--port", str(CONFIG["mariadb_port"]),
               "-N", "-B", "-e", sql]
        if db:
            cmd += [db]
        if passwd:
            cmd += ["-p" + passwd]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:300] or "mysql failed")
        return (r.stdout or "").strip()
    def _pg_run(self, admin_user, admin_pass, dbname, sql, tuples=False):
        psql = self.pgd / "bin" / "psql.exe"
        if not psql.exists():
            raise RuntimeError("psql.exe not found — is PostgreSQL installed?")
        env = os.environ.copy()
        if admin_pass:
            env["PGPASSWORD"] = admin_pass
        cmd = [str(psql), "-U", admin_user, "-h", "127.0.0.1",
               "-p", str(CONFIG["postgresql_port"]), "-d", dbname,
               "-v", "ON_ERROR_STOP=1"]
        if tuples:
            cmd += ["-t", "-A"]
        cmd += ["-c", sql]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:300] or "psql failed")
        return (r.stdout or "").strip()
    def db_list(self, engine, user, passwd):
        if engine == "PostgreSQL":
            out = self._pg_run(user or "postgres", passwd, "postgres",
                               "SELECT datname FROM pg_database WHERE NOT datistemplate ORDER BY 1;",
                               tuples=True)
        else:
            out = self._my_run(user, passwd, "", "SHOW DATABASES;")
        return [l for l in out.splitlines() if l.strip()]
    def db_users(self, engine, user, passwd):
        if engine == "PostgreSQL":
            out = self._pg_run(user or "postgres", passwd, "postgres",
                               "SELECT usename FROM pg_user ORDER BY 1;", tuples=True)
        else:
            out = self._my_run(user, passwd, "", "SELECT CONCAT(user, '@', host) FROM mysql.user ORDER BY 1;")
        return [l for l in out.splitlines() if l.strip()]
    def db_create(self, engine, user, passwd, dbname):
        if not dbname:
            raise RuntimeError("Database name is required")
        if engine == "PostgreSQL":
            safe = '"' + dbname.replace('"', '""') + '"'
            self._pg_run(user or "postgres", passwd, "postgres", f"CREATE DATABASE {safe};")
        else:
            safe = "`" + dbname.replace("`", "``") + "`"
            self._my_run(user, passwd, "", f"CREATE DATABASE {safe} CHARACTER SET utf8mb4;")
        self.log(f"Database created: {dbname}")
    def db_drop(self, engine, user, passwd, dbname):
        if not dbname:
            raise RuntimeError("Database name is required")
        if engine == "PostgreSQL":
            safe = '"' + dbname.replace('"', '""') + '"'
            self._pg_run(user or "postgres", passwd, "postgres", f"DROP DATABASE {safe};")
        else:
            safe = "`" + dbname.replace("`", "``") + "`"
            self._my_run(user, passwd, "", f"DROP DATABASE {safe};")
        self.log(f"Database dropped: {dbname}")
    def db_mkuser(self, engine, user, passwd, new_user, new_pass):
        if not new_user or not new_pass:
            raise RuntimeError("New user and password are required")
        if engine == "PostgreSQL":
            u = '"' + new_user.replace('"', '""') + '"'
            p = new_pass.replace("'", "''")
            self._pg_run(user or "postgres", passwd, "postgres",
                         f"CREATE USER {u} WITH PASSWORD '{p}';")
        else:
            u = new_user.replace("'", "''")
            pw = new_pass.replace("'", "''")
            self._my_run(user, passwd, "",
                         f"CREATE USER '{u}'@'%' IDENTIFIED BY '{pw}'; "
                         f"GRANT ALL PRIVILEGES ON *.* TO '{u}'@'%'; FLUSH PRIVILEGES;")
        self.log(f"User created: {new_user}")
    def db_backup(self, engine, user, passwd, dbname, filepath):
        if not dbname:
            raise RuntimeError("Database name is required")
        if engine == "PostgreSQL":
            tool = self.pgd / "bin" / "pg_dump.exe"
            if not tool.exists():
                raise RuntimeError("pg_dump.exe not found")
            env = os.environ.copy()
            if passwd:
                env["PGPASSWORD"] = passwd
            cmd = [str(tool), "-U", user or "postgres", "-h", "127.0.0.1",
                   "-p", str(CONFIG["postgresql_port"]), "-d", dbname, "-f", filepath]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            tool = self.md / "bin" / "mysqldump.exe"
            if not tool.exists():
                raise RuntimeError("mysqldump.exe not found")
            cmd = [str(tool), "-u", user or "root", "--port", str(CONFIG["mariadb_port"])]
            if passwd:
                cmd += ["-p" + passwd]
            cmd += ["--databases", dbname, f"--result-file={filepath}"]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:300] or "backup failed")
        self.log(f"Backup saved: {filepath}")
    def db_restore(self, engine, user, passwd, dbname, filepath):
        p = Path(filepath)
        if not p.is_file():
            raise RuntimeError(f"Dump file not found: {filepath}")
        if engine == "PostgreSQL":
            tool = self.pgd / "bin" / "psql.exe"
            if not tool.exists():
                raise RuntimeError("psql.exe not found")
            env = os.environ.copy()
            if passwd:
                env["PGPASSWORD"] = passwd
            cmd = [str(tool), "-U", user or "postgres", "-h", "127.0.0.1",
                   "-p", str(CONFIG["postgresql_port"]), "-d", dbname or "postgres",
                   "-v", "ON_ERROR_STOP=1", "-f", str(p.resolve())]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            tool = self.md / "bin" / "mysql.exe"
            if not tool.exists():
                raise RuntimeError("mysql.exe not found")
            cmd = [str(tool), "-u", user or "root", "--port", str(CONFIG["mariadb_port"])]
            if passwd:
                cmd += ["-p" + passwd]
            if dbname:
                cmd += [dbname]
            with open(str(p.resolve()), "rb") as f:
                r = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=300,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:300] or "restore failed")
        self.log(f"Restored from: {filepath}")
    @staticmethod
    def _ver_tuple(v):
        try:
            return tuple(int(x) for x in str(v).lstrip("vV").split(".")[:3])
        except Exception:
            return (0,)

    def latest_release(self):
        r = requests.get("https://api.github.com/repos/nsmykh70-creator/FarajaWebServer/releases/latest",
                         timeout=10, headers={"User-Agent": "FarajaWebServer"})
        r.raise_for_status()
        return (r.json().get("tag_name", "") or "").strip()

    def snapshot_create(self):
        ts = time.strftime("%Y%m%d-%H%M%S")
        snap_dir = APP_ROOT / "backups"
        snap_dir.mkdir(parents=True, exist_ok=True)
        out = snap_dir / f"faraja-snap-{ts}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in WWW.rglob("*"):
                if p.is_file():
                    z.write(p, Path("www") / p.relative_to(WWW))
            for cfg in ("server.json", "sites.json", "tasks.json", "settings.json",
                        "node.json", "python.json", "env.json", "lang.json"):
                p = APP_ROOT / "config" / cfg
                if p.is_file():
                    z.write(p, Path("config") / cfg)
        dumps = []
        try:
            tool = self.md / "bin" / "mysqldump.exe"
            if tool.exists() and self.drun():
                dump = snap_dir / f"mariadb-{ts}.sql"
                r = subprocess.run([str(tool), "-u", "root", "--port", str(CONFIG["mariadb_port"]),
                                    "--all-databases", f"--result-file={dump}"],
                                   capture_output=True, text=True, timeout=300,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if r.returncode == 0:
                    dumps.append(str(dump))
                else:
                    self.log("Snapshot: mysqldump skipped (check root access)")
        except Exception as e:
            self.log(f"Snapshot: mysqldump skipped ({e})")
        try:
            tool = self.pgd / "bin" / "pg_dumpall.exe"
            if tool.exists() and self.pgrun():
                dump = snap_dir / f"postgres-{ts}.sql"
                env = os.environ.copy()
                r = subprocess.run([str(tool), "-U", "postgres", "-h", "127.0.0.1",
                                    "-p", str(CONFIG["postgresql_port"]), "-f", str(dump)],
                                   capture_output=True, text=True, timeout=300, env=env,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if r.returncode == 0:
                    dumps.append(str(dump))
                else:
                    self.log("Snapshot: pg_dumpall skipped (check postgres access)")
        except Exception as e:
            self.log(f"Snapshot: pg_dumpall skipped ({e})")
        self.log(f"Snapshot saved: {out.name}" + (f" + {len(dumps)} dumps" if dumps else ""))
        return out

    def snapshot_restore(self, snap_path):
        snap = Path(snap_path)
        if not snap.is_file() or not zipfile.is_zipfile(snap):
            raise RuntimeError(f"Bad snapshot file: {snap_path}")
        with zipfile.ZipFile(snap) as z:
            names = z.namelist()
            if not any(n.startswith("www/") for n in names):
                raise RuntimeError("Not a Faraja snapshot (no www/ inside)")
            for n in names:
                parts = Path(n).parts
                if not parts or Path(n).is_absolute() or ".." in parts:
                    continue
                if not (n.startswith("www/") or n.startswith("config/")):
                    continue
                target = APP_ROOT.joinpath(*parts)
                if n.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(n) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        self.log(f"Snapshot restored from: {snap.name} (restart services to apply)")

    def redis_flush(self, password):
        cli = self.rdd / "redis-cli.exe"
        if not cli.exists():
            raise RuntimeError("redis-cli.exe not found")
        cmd = [str(cli), "-h", "127.0.0.1", "-p", str(CONFIG["redis_port"])]
        if password:
            cmd += ["-a", password, "--no-auth-warning"]
        cmd += ["FLUSHALL"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:200] or "redis flush failed")
        self.log("Redis FLUSHALL: OK")
    def maria_apply_port(self, port):
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise RuntimeError(f"Bad MariaDB port: {port}")
        CONFIG["mariadb_port"] = port
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
        except Exception as e:
            self.log(f"server.json save warning: {e}")
        self.write_configs()
        self.log(f"my.ini: port = {port}")
        if self.drun():
            self.log("Restarting MariaDB to apply new port...")
            self.stop_db()
            self.start_db()
    def maria_set_root_password(self, cur_pass, new_pass):
        if not new_pass:
            raise RuntimeError("New password is required")
        pw = new_pass.replace("'", "''")
        self._my_run("root", cur_pass, "",
                     f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{pw}'; FLUSH PRIVILEGES;")
        self.log("MariaDB root password updated")
    def docker_networks(self):
        r = subprocess.run(["docker", "network", "ls", "--format", "{{.Name}}|{{.Driver}}|{{.Scope}}"],
                           capture_output=True, text=True, timeout=30,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200] or "docker network ls failed")
        rows = []
        for line in (r.stdout or "").splitlines():
            p = (line.split("|") + ["", "", ""])[:3]
            if p[0]:
                rows.append(p)
        return rows
    def docker_volumes(self):
        r = subprocess.run(["docker", "volume", "ls", "--format", "{{.Name}}|{{.Driver}}"],
                           capture_output=True, text=True, timeout=30,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200] or "docker volume ls failed")
        rows = []
        for line in (r.stdout or "").splitlines():
            p = (line.split("|") + ["", ""])[:2]
            if p[0]:
                rows.append(p)
        return rows
    def docker_net_rm(self, name):
        r = subprocess.run(["docker", "network", "rm", name], capture_output=True, text=True,
                           timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:200] or "docker network rm failed")
        self.log(f"docker network rm {name}: OK")
    def docker_vol_rm(self, name):
        r = subprocess.run(["docker", "volume", "rm", name], capture_output=True, text=True,
                           timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(((r.stderr or r.stdout) or "").strip()[:200] or "docker volume rm failed")
        self.log(f"docker volume rm {name}: OK")
    def env_active(self):
        try:
            d = json.loads((APP_ROOT/"config"/"env.json").read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d.get("php", ""), d.get("node", ""), d.get("python", "")
        except Exception:
            pass
        return "", "", ""

    def env_save(self, **kv):
        d = {}
        try:
            d = json.loads((APP_ROOT/"config"/"env.json").read_text(encoding="utf-8"))
            if not isinstance(d, dict):
                d = {}
        except Exception:
            pass
        d.update(kv)
        (APP_ROOT/"config").mkdir(parents=True, exist_ok=True)
        (APP_ROOT/"config"/"env.json").write_text(json.dumps(d, indent=2), encoding="utf-8")

    def resolve_node_url(self, major):
        self.log(f"Resolving Node.js {major} download link...")
        r = requests.get("https://nodejs.org/dist/index.json", timeout=30,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        for e in r.json():
            v = e.get("version", "")
            if v.startswith(f"v{major}."):
                return (f"https://nodejs.org/dist/{v}/node-{v}-win-x64.zip",
                        f"node-{v}-win-x64.zip")
        raise RuntimeError(f"No Node.js {major} release found")

    def install_runtime_version(self, kind, ver, progress):
        if kind == "php":
            name = "php"
            info = comps().get("php_versions", {}).get(ver)
            if not info:
                raise RuntimeError(f"Unknown PHP version: {ver}")
            arc = DOWNLOADS / info["archive"]
            if not (arc.is_file() and zipfile.is_zipfile(arc)):
                self.log(f"Downloading PHP {ver}...")
                download(info["url"], arc, progress, self.log)
            install_component(name, self.log, progress, prearchive=arc)
        elif kind == "node":
            name = "nodejs"
            url, archive = self.resolve_node_url(ver)
            arc = DOWNLOADS / archive
            if not (arc.is_file() and zipfile.is_zipfile(arc)):
                self.log(f"Downloading Node.js {ver}...")
                download(url, arc, progress, self.log)
            install_component(name, self.log, progress, prearchive=arc)
        elif kind == "python":
            name = "python" + ver.replace(".", "")
            info = comps().get("python_versions", {}).get(ver)
            if not info:
                raise RuntimeError(f"Unknown Python version: {ver}")
            arc = DOWNLOADS / info["archive"]
            if not (arc.is_file() and zipfile.is_zipfile(arc)):
                self.log(f"Downloading Python {ver}...")
                download(info["url"], arc, progress, self.log)
            install_component(name, self.log, progress, prearchive=arc)
        else:
            raise RuntimeError(f"Unknown runtime: {kind}")
        self.env_save(**{kind: ver})
        self.log(f"{kind} {ver} installed and activated")

    def php_version_detect(self):
        for exe in (self.pd/"php.exe", self.pd/"php-cgi.exe"):
            if exe.exists():
                try:
                    r = subprocess.run([str(exe), "-v"], capture_output=True, text=True,
                                       timeout=10,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    m = re.search(r"PHP\s+(\d+\.\d+\.\d+)", r.stdout or "")
                    if m:
                        return m.group(1)
                except Exception:
                    pass
        return "?"

    def node_version_detect(self):
        try:
            exe = self.get_node_exe()
        except Exception:
            return "?"
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return (r.stdout or "").strip() or "?"
        except Exception:
            return "?"

    def tools_versions(self):
        import shutil as _sh
        out = {}
        for tool, args in (("Composer", ["--version"]), ("npm", ["--version"]), ("Git", ["--version"])):
            try:
                exe = _sh.which(tool.lower())
                if not exe:
                    out[tool] = "—"
                    continue
                shell = exe.lower().endswith((".cmd", ".bat"))
                r = subprocess.run([exe] + args, capture_output=True, text=True, timeout=10,
                                   shell=shell,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                out[tool] = (r.stdout or "").strip().splitlines()[0][:60] if r.returncode == 0 else "—"
            except Exception:
                out[tool] = "—"
        return out

    def node_installed(self):
        if (RUNTIME/"Nodejs"/"node.exe").exists():
            return True
        import shutil as _shn
        return _shn.which("node") is not None
    def start_node(self):
        self._ensure_component("nodejs")
        exe = self.get_node_exe()
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            ver = r.stdout.strip() or "unknown"
        except Exception:
            ver = "unknown"
        self.install_tsx()
        self.log(f"Node.js {ver} ready (tsx available)")
    def stop_node(self):
        self.log("Node.js has no background daemon; nothing to stop")
    def noderun(self):
        return self.node_installed()
    def py_dir(self, ver=None):
        if ver is None:
            try:
                ver = self.env_active()[2] or "3.12"
            except Exception:
                ver = "3.12"
        cand = RUNTIME / f"Python{ver.replace('.', '')}"
        if (cand / "python.exe").exists():
            return cand
        import shutil as _shp
        for d in sorted(RUNTIME.glob("Python*")):
            if (d / "python.exe").exists():
                return d
        sys_py = _shp.which("python") or _shp.which("python3")
        if sys_py:
            return Path(sys_py).parent
        return cand
    def get_python_exe(self, ver=None):
        exe = self.py_dir(ver) / "python.exe"
        if exe.exists():
            return str(exe)
        import shutil as _shp
        sys_py = _shp.which("python") or _shp.which("python3")
        if sys_py:
            return sys_py
        raise RuntimeError("Python is not installed (see Environment settings)")
    def python_version_detect(self):
        try:
            exe = self.get_python_exe()
        except Exception:
            return "?"
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            m = re.search(r"Python\s+(\d+\.\d+\.\d+)", (r.stdout or "") + (r.stderr or ""))
            return m.group(1) if m else "?"
        except Exception:
            return "?"
    def py_server_running(self, name):
        info = self.py_servers.get(name)
        try:
            return info is not None and info["proc"].poll() is None
        except Exception:
            return False
    def py_server_start(self, name, directory, entry, port, pyver=None):
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise RuntimeError(f"Bad Python port: {port}")
        self.py_server_stop(name, quiet=True)
        entry_path = Path(directory) / entry
        if not entry_path.exists():
            raise RuntimeError(f"Entry not found: {entry_path}")
        if entry_path.suffix.lower() != ".py":
            raise RuntimeError(f"Unsupported entry type: {entry_path.suffix} (use .py)")
        exe = self.get_python_exe(pyver)
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["PYTHONUNBUFFERED"] = "1"
        f = self.logfile("python-process.log")
        proc = subprocess.Popen([exe, "-u", str(entry_path.resolve())],
                                cwd=str(Path(directory).resolve()), stdout=f, stderr=f,
                                env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.py_servers[name] = {"proc": proc, "dir": str(directory), "entry": entry,
                                 "port": port, "pyver": pyver or "",
                                 "started": time.strftime("%Y-%m-%d %H:%M:%S")}
        self.node_processes[proc.pid] = {"script": f"{name}: {entry}", "path": str(entry_path.resolve()),
                                         "started": self.py_servers[name]["started"], "proc": proc}
        self.py_routes[port] = name
        self._write_nginx_conf()
        if not wait_port(port, 15):
            raise RuntimeError(f"Python server '{name}' did not open port {port}; see Process / Init log")
        self.log(f"Python server '{name}' started on port {port} (PID {proc.pid}); route: /py/{port}/")
        return proc
    def py_server_stop(self, name, quiet=False):
        info = self.py_servers.pop(name, None)
        if info is None:
            if not quiet:
                self.log(f"Python server '{name}' is not running")
            return
        try:
            kill_pid_tree(info["proc"].pid)
        except Exception:
            pass
        self.node_processes.pop(info["proc"].pid, None)
        self.py_routes.pop(info["port"], None)
        self._write_nginx_conf()
        wait_port_closed(info["port"], 8)
        if not quiet:
            self.log(f"Python server '{name}' stopped")
    def py_servers_stop_all(self):
        for name in list(self.py_servers.keys()):
            try:
                self.py_server_stop(name, quiet=True)
            except Exception:
                pass
        self.log("All Python servers stopped")
    def shutdown(self):
        # Stop all MiniServer-managed services concurrently so one slow server
        # cannot hold up the shutdown of every other service. Console windows are
        # suppressed by CREATE_NO_WINDOW in the individual stop commands.
        funcs = (self.stop_apache, self.stop_nginx, self.stop_php,
                 self.stop_db, self.stop_pg, self.stop_redis)
        workers = []
        for fn in funcs:
            t = threading.Thread(target=lambda f=fn: self._safe_shutdown_call(f), daemon=True)
            t.start()
            workers.append(t)
        deadline = time.monotonic() + 5
        for t in workers:
            remaining = max(0.05, deadline - time.monotonic())
            t.join(remaining)
        # Kill every tracked Node.js / Python process tree (servers + one-off scripts),
        # so nothing survives the application exit.
        for name in list(self.node_servers.keys()):
            try:
                self.node_server_stop(name, quiet=True)
            except Exception:
                pass
        for name in list(self.py_servers.keys()):
            try:
                self.py_server_stop(name, quiet=True)
            except Exception:
                pass
        for ver, proc in list(self.php_extra.items()):
            try:
                if proc is not None and proc.poll() is None:
                    kill_pid_tree(proc.pid)
            except Exception:
                pass
        self.php_extra.clear()
        for pid, info in list(self.node_processes.items()):
            try:
                proc = info.get("proc")
                if proc is not None and proc.poll() is None:
                    kill_pid_tree(pid)
            except Exception:
                pass
        self.node_processes.clear()
        for f in self.handles:
            try:f.close()
            except Exception:pass

    def _safe_shutdown_call(self, fn):
        try:
            fn()
        except Exception:
            pass


class StyledButton(tk.Canvas):
    """Modern flat/rounded button used throughout the UI."""
    def __init__(self, parent, text, command=None, color="#4f8cff", hover_color="#6aa2ff",
                 active_color="#3975e8", width=110, height=34, font_size=9, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                         bg=parent.cget("bg") if isinstance(parent, tk.Frame) else THEME["bg"],
                         cursor="hand2", **kwargs)
        self._color, self._hover_color, self._active_color = color, hover_color, active_color
        self._command, self._width, self._height, self._text = command, width, height, text
        self._enabled = True
        self._font = (THEME["font_family"], font_size, "bold")
        self._draw(color)
        self.bind("<Enter>", self._on_enter); self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press); self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, bg):
        self.delete("all")
        r, w, h = 9, self._width, self._height
        self.create_rectangle(r, 0, w-r, h, fill=bg, outline="")
        self.create_rectangle(0, r, w, h-r, fill=bg, outline="")
        for box, a in [((0,0,2*r,2*r),90),((w-2*r,0,w,2*r),0),((0,h-2*r,2*r,h),180),((w-2*r,h-2*r,w,h),270)]:
            self.create_arc(*box, start=a, extent=90, fill=bg, outline="")
        fg = THEME["white"] if self._enabled else THEME["text_muted"]
        self.create_text(w//2, h//2, text=self._text, fill=fg, font=self._font)

    def _on_enter(self, e):
        if self._enabled: self._draw(self._hover_color)
    def _on_leave(self, e):
        if self._enabled: self._draw(self._color)
    def _on_press(self, e):
        if self._enabled: self._draw(self._active_color)
    def _on_release(self, e):
        if self._enabled and self._command:
            self._draw(self._hover_color); self._command()
    def set_state(self, state):
        self._enabled = (state == "normal")
        self.configure(cursor="hand2" if self._enabled else "arrow")
        self._draw(self._color if self._enabled else THEME["bg_input"])


class ToolTip:
    def __init__(self, widget, text, delay=600):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after = None
        self._tip = None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<ButtonPress>", self._leave, add="+")

    def _enter(self, e=None):
        self._leave()
        self._after = self.widget.after(self.delay, self._show)

    def _leave(self, e=None):
        if self._after:
            try:
                self.widget.after_cancel(self._after)
            except Exception:
                pass
            self._after = None
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None

    def _show(self):
        if not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        tip.configure(bg=THEME["border"])
        lbl = tk.Label(tip, text=self.text, bg=THEME["bg_elevated"], fg=THEME["text"],
                       font=(THEME["font_family"], 8), padx=10, pady=6,
                       wraplength=280, justify="left")
        lbl.pack()
        self._tip = tip


class IconButton(tk.Canvas):
    """Square button with a vector-drawn pictogram (language-independent)."""
    def __init__(self, parent, kind, command=None, color="#4f8cff", hover_color="#6aa2ff",
                 active_color="#3975e8", size=34, tip=None, fg="#ffffff", **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0,
                         bg=parent.cget("bg") if isinstance(parent, tk.Frame) else THEME["bg"],
                         cursor="hand2", **kwargs)
        self._color = color
        self._hover_color = hover_color
        self._active_color = active_color
        self._command = command
        self._size = size
        self._kind = kind
        self._fg = fg
        self._enabled = True
        self._draw(color)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        if tip:
            ToolTip(self, tip)

    def set_kind(self, kind):
        self._kind = kind
        self._draw(self._color)

    def set_colors(self, color, hover_color, active_color):
        self._color = color
        self._hover_color = hover_color
        self._active_color = active_color
        self._draw(color)

    def set_state(self, state):
        self._enabled = (state == "normal")
        self.configure(cursor="hand2" if self._enabled else "arrow")
        self._draw(self._color if self._enabled else THEME["bg_input"])

    def _draw(self, bg):
        self.delete("all")
        w = h = self._size
        r = max(6, w // 4)
        self.create_arc(0, 0, 2 * r, 2 * r, start=90, extent=90, fill=bg, outline="")
        self.create_arc(w - 2 * r, 0, w, 2 * r, start=0, extent=90, fill=bg, outline="")
        self.create_arc(0, h - 2 * r, 2 * r, h, start=180, extent=90, fill=bg, outline="")
        self.create_arc(w - 2 * r, h - 2 * r, w, h, start=270, extent=90, fill=bg, outline="")
        self.create_rectangle(r, 0, w - r, h, fill=bg, outline="")
        self.create_rectangle(0, r, w, h - r, fill=bg, outline="")
        fg = self._fg if self._enabled else THEME["text_muted"]
        self._icon(self._kind, w / 2.0, h / 2.0, w / 34.0, fg)

    def _icon(self, kind, cx, cy, u, fg):
        import math
        lw = max(2, round(2 * u))
        if kind == "play":
            self.create_polygon(cx - 5 * u, cy - 7 * u, cx - 5 * u, cy + 7 * u,
                                cx + 7 * u, cy, fill=fg, outline="")
        elif kind == "stop":
            self.create_rectangle(cx - 6 * u, cy - 6 * u, cx + 6 * u, cy + 6 * u,
                                  fill=fg, outline="")
        elif kind in ("restart", "refresh"):
            self.create_arc(cx - 7 * u, cy - 7 * u, cx + 7 * u, cy + 7 * u,
                            start=90, extent=270, style="arc", outline=fg, width=lw)
            if kind == "restart":
                tx, ty, dx, dy = cx + 7 * u, cy, 0, -1
            else:
                tx, ty, dx, dy = cx, cy - 7 * u, -1, 0
            bx, by = tx - dx * 4.5 * u, ty - dy * 4.5 * u
            px, py = -dy, dx
            self.create_polygon(tx, ty, bx + px * 2.6 * u, by + py * 2.6 * u,
                                bx - px * 2.6 * u, by - py * 2.6 * u, fill=fg, outline="")
        elif kind == "plus":
            self.create_rectangle(cx - 2 * u, cy - 7 * u, cx + 2 * u, cy + 7 * u,
                                  fill=fg, outline="")
            self.create_rectangle(cx - 7 * u, cy - 2 * u, cx + 7 * u, cy + 2 * u,
                                  fill=fg, outline="")
        elif kind == "cross":
            self.create_line(cx - 5.5 * u, cy - 5.5 * u, cx + 5.5 * u, cy + 5.5 * u,
                             fill=fg, width=lw + 1, capstyle="round")
            self.create_line(cx - 5.5 * u, cy + 5.5 * u, cx + 5.5 * u, cy - 5.5 * u,
                             fill=fg, width=lw + 1, capstyle="round")
        elif kind in ("folder", "folder_plus"):
            self.create_rectangle(cx - 8 * u, cy - 3 * u, cx + 8 * u, cy + 7 * u,
                                  fill=fg, outline="")
            self.create_polygon(cx - 8 * u, cy - 3 * u, cx - 8 * u, cy - 6 * u,
                                cx - 3 * u, cy - 6 * u, cx - 1 * u, cy - 3 * u,
                                fill=fg, outline="")
            if kind == "folder_plus":
                self.create_rectangle(cx + 3 * u, cy + 1 * u, cx + 5.4 * u, cy + 9 * u,
                                      fill=self._color, outline="")
                self.create_rectangle(cx + 1 * u, cy + 4 * u, cx + 9 * u, cy + 6 * u,
                                      fill=self._color, outline="")
        elif kind in ("doc", "doc_plus"):
            self.create_polygon(cx - 5 * u, cy - 8 * u, cx + 2 * u, cy - 8 * u,
                                cx + 6 * u, cy - 4 * u, cx + 6 * u, cy + 8 * u,
                                cx - 5 * u, cy + 8 * u, fill=fg, outline="")
            if kind == "doc_plus":
                self.create_rectangle(cx + 2 * u, cy + 1 * u, cx + 4.4 * u, cy + 9 * u,
                                      fill=self._color, outline="")
                self.create_rectangle(cx - 1 * u, cy + 4 * u, cx + 7 * u, cy + 6.4 * u,
                                      fill=self._color, outline="")
        elif kind == "trash":
            self.create_line(cx - 7 * u, cy - 5 * u, cx + 7 * u, cy - 5 * u,
                             fill=fg, width=lw)
            self.create_line(cx - 2 * u, cy - 8 * u, cx + 2 * u, cy - 8 * u,
                             fill=fg, width=lw)
            self.create_polygon(cx - 5.5 * u, cy - 3 * u, cx + 5.5 * u, cy - 3 * u,
                                cx + 4 * u, cy + 8 * u, cx - 4 * u, cy + 8 * u,
                                fill=fg, outline="")
        elif kind == "save":
            self.create_rectangle(cx - 7 * u, cy - 6 * u, cx + 7 * u, cy + 8 * u,
                                  outline=fg, width=lw, fill="")
            self.create_rectangle(cx - 3.5 * u, cy - 6 * u, cx + 3.5 * u, cy, outline=fg,
                                  width=max(1, lw - 1), fill="")
            self.create_rectangle(cx - 4.5 * u, cy + 2 * u, cx + 4.5 * u, cy + 8 * u,
                                  outline=fg, width=max(1, lw - 1), fill="")
        elif kind == "search":
            self.create_oval(cx - 7 * u, cy - 7 * u, cx + 2 * u, cy + 2 * u,
                             outline=fg, width=lw, fill="")
            self.create_line(cx + 1 * u, cy + 1 * u, cx + 7 * u, cy + 7 * u,
                             fill=fg, width=lw + 1, capstyle="round")
        elif kind == "lock":
            self.create_arc(cx - 4.5 * u, cy - 7 * u, cx + 4.5 * u, cy + 1 * u,
                            start=0, extent=180, style="arc", outline=fg, width=lw)
            self.create_rectangle(cx - 6 * u, cy - 1 * u, cx + 6 * u, cy + 8 * u,
                                  fill=fg, outline="")
        elif kind == "globe":
            self.create_oval(cx - 7 * u, cy - 7 * u, cx + 7 * u, cy + 7 * u,
                             outline=fg, width=lw, fill="")
            self.create_line(cx, cy - 7 * u, cx, cy + 7 * u, fill=fg, width=max(1, lw - 1))
            self.create_line(cx - 7 * u, cy, cx + 7 * u, cy, fill=fg, width=max(1, lw - 1))
        elif kind == "cylinder":
            self.create_oval(cx - 6 * u, cy - 7 * u, cx + 6 * u, cy - 2 * u,
                             outline=fg, width=lw, fill="")
            self.create_line(cx - 6 * u, cy - 4.5 * u, cx - 6 * u, cy + 4.5 * u,
                             fill=fg, width=lw)
            self.create_line(cx + 6 * u, cy - 4.5 * u, cx + 6 * u, cy + 4.5 * u,
                             fill=fg, width=lw)
            self.create_arc(cx - 6 * u, cy + 0 * u, cx + 6 * u, cy + 8 * u,
                            start=180, extent=180, style="arc", outline=fg, width=lw)
        elif kind == "check":
            self.create_line(cx - 7 * u, cy + 0.5 * u, cx - 2 * u, cy + 5 * u,
                             cx + 7 * u, cy - 5 * u, fill=fg, width=lw + 1,
                             capstyle="round", joinstyle="round", smooth=False)
        elif kind == "up":
            self.create_line(cx, cy + 7 * u, cx, cy - 4 * u, fill=fg, width=lw + 1,
                             capstyle="round")
            self.create_polygon(cx, cy - 8 * u, cx - 3.5 * u, cy - 3 * u,
                                cx + 3.5 * u, cy - 3 * u, fill=fg, outline="")
        elif kind == "down":
            self.create_line(cx, cy - 7 * u, cx, cy + 4 * u, fill=fg, width=lw + 1,
                             capstyle="round")
            self.create_polygon(cx, cy + 8 * u, cx - 3.5 * u, cy + 3 * u,
                                cx + 3.5 * u, cy + 3 * u, fill=fg, outline="")
        elif kind == "list":
            for dy in (-5, 0, 5):
                self.create_line(cx - 7 * u, cy + dy * u, cx + 7 * u, cy + dy * u,
                                 fill=fg, width=lw + 1, capstyle="round")
        elif kind == "person":
            self.create_oval(cx - 3 * u, cy - 7 * u, cx + 3 * u, cy - 1 * u,
                             fill=fg, outline="")
            self.create_arc(cx - 7 * u, cy - 1 * u, cx + 7 * u, cy + 9 * u,
                            start=0, extent=180, style="arc", outline=fg, width=lw + 1)
        elif kind == "heart":
            self.create_oval(cx - 6.5 * u, cy - 4.5 * u, cx + 0.5 * u, cy + 3 * u,
                             fill=fg, outline="")
            self.create_oval(cx - 0.5 * u, cy - 4.5 * u, cx + 6.5 * u, cy + 3 * u,
                             fill=fg, outline="")
            self.create_polygon(cx - 6 * u, cy, cx + 6 * u, cy, cx, cy + 8 * u,
                                fill=fg, outline="")
        elif kind == "bookmark":
            self.create_polygon(cx - 5 * u, cy - 8 * u, cx + 5 * u, cy - 8 * u,
                                cx + 5 * u, cy + 8 * u, cx, cy + 4 * u,
                                cx - 5 * u, cy + 8 * u, fill=fg, outline="")
        elif kind == "pencil":
            self.create_line(cx - 4 * u, cy + 4 * u, cx + 3 * u, cy - 3 * u,
                             fill=fg, width=max(3, int(4 * u)), capstyle="round")
            self.create_polygon(cx - 4 * u, cy + 4 * u, cx - 6.5 * u, cy + 6.5 * u,
                                cx - 2.5 * u, cy + 6 * u, fill=fg, outline="")
            self.create_rectangle(cx + 1 * u, cy - 5 * u, cx + 5 * u, cy - 1 * u,
                                  fill=fg, outline="")
        elif kind == "help":
            self.create_text(cx, cy, text="?", fill=fg,
                             font=(THEME["font_family"], int(14 * u), "bold"))
        elif kind == "copy":
            self.create_rectangle(cx - 7 * u, cy - 3 * u, cx + 1 * u, cy + 7 * u,
                                  outline=fg, width=lw, fill="")
            self.create_rectangle(cx - 1 * u, cy - 7 * u, cx + 7 * u, cy + 3 * u,
                                  outline=fg, width=lw, fill=self._color)
        elif kind == "paste":
            self.create_rectangle(cx - 6 * u, cy - 3 * u, cx + 6 * u, cy + 8 * u,
                                  outline=fg, width=lw, fill="")
            self.create_rectangle(cx - 2.5 * u, cy - 7 * u, cx + 2.5 * u, cy - 1 * u,
                                  fill=fg, outline="")
            self.create_line(cx - 3 * u, cy + 2 * u, cx + 3 * u, cy + 2 * u,
                             fill=fg, width=max(1, lw - 1))
        else:
            self.create_rectangle(cx - 5 * u, cy - 5 * u, cx + 5 * u, cy + 5 * u,
                                  outline=fg, width=lw, fill="")

    def _on_enter(self, e):
        if self._enabled:
            self._draw(self._hover_color)

    def _on_leave(self, e):
        if self._enabled:
            self._draw(self._color)

    def _on_press(self, e):
        if self._enabled:
            self._draw(self._active_color)

    def _on_release(self, e):
        if self._enabled and self._command:
            self._draw(self._hover_color)
            self._command()


class OfficeTabs:
    def __init__(self, parent, active_size=11, passive_size=9):
        self.header = tk.Frame(parent, bg=THEME["bg_card"],
                               highlightbackground=THEME["border"], highlightthickness=1)
        self.header.pack(fill="x", padx=12, pady=(2, 8))
        self.separator = tk.Frame(parent, bg=THEME["bg"])
        self.separator.pack_forget()
        self.body = tk.Frame(parent, bg=THEME["bg"])
        self.body.pack(fill="both", expand=True)
        self._tabs = []
        self._selected = -1
        self._active_size = active_size
        self._passive_size = passive_size

    def hide_header(self):
        """Hide the tab strip when the host provides its own navigation."""
        self.header.pack_forget()
        self.separator.pack_forget()

    def add(self, frame, text):
        idx = len(self._tabs)
        cv = tk.Canvas(self.header, bg=THEME["bg_card"], highlightthickness=0,
                       cursor="hand2", bd=0)
        cv.pack(side="left", padx=(0, 6), anchor="s")
        cv.bind("<Button-1>", lambda e, i=idx: self.select(i))
        ToolTip(cv, text)
        self._tabs.append({"canvas": cv, "frame": frame, "text": text})
        frame.pack_forget()
        if self._selected == -1:
            self.select(0)
        else:
            self._draw_tab(idx)
        return frame

    def select(self, idx):
        if not (0 <= idx < len(self._tabs)):
            return
        self._selected = idx
        for i, t in enumerate(self._tabs):
            if i == idx:
                t["frame"].pack(fill="both", expand=True)
            else:
                t["frame"].pack_forget()
            self._draw_tab(i)

    def _draw_tab(self, idx):
        import tkinter.font as tkfont
        t = self._tabs[idx]
        cv = t["canvas"]
        active = (idx == self._selected)
        size = self._active_size if active else self._passive_size
        font = tkfont.Font(family=THEME["font_family"], size=size, weight="bold")
        w = font.measure(t["text"]) + (52 if active else 40)
        h = 38 if active else 30
        cv.configure(width=w, height=h)
        cv.delete("all")
        r = 10
        bg = THEME["bg_elevated"] if active else THEME["bg_card"]
        fg = THEME["accent"] if active else THEME["text_dim"]
        cv.create_arc(2, 2, 2 + 2 * r, 2 + 2 * r, start=90, extent=90, fill=bg, outline="")
        cv.create_arc(w - 2 - 2 * r, 2, w - 2, 2 + 2 * r, start=0, extent=90, fill=bg, outline="")
        cv.create_rectangle(2 + r, 2, w - 2 - r, h - 2, fill=bg, outline="")
        cv.create_rectangle(2, 2 + r, w - 2, h - 2, fill=bg, outline="")
        if active:
            cv.create_rectangle(2, h - 5, w - 2, h - 2, fill=THEME["accent"], outline="")
        cv.create_text(w // 2, (h - 2) // 2, text=t["text"], fill=fg, font=font)


class DarkPrompt:
    @staticmethod
    def _center(win, parent, w, h):
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
            win.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
        except Exception:
            win.geometry(f"{w}x{h}")

    @staticmethod
    def ask_string(parent, title, prompt, initial=""):
        win = tk.Toplevel(parent)
        win.title(title)
        win.configure(bg=THEME["bg_card"], highlightbackground=THEME["accent"],
                      highlightthickness=1)
        try:
            win.iconbitmap(str(ICON))
        except Exception:
            pass
        DarkPrompt._center(win, parent, 420, 170)
        win.transient(parent)
        win.grab_set()
        tk.Label(win, text=prompt, bg=THEME["bg_card"], fg=THEME["text"],
                 font=(THEME["font_family"], 10), wraplength=380,
                 justify="left").pack(fill="x", padx=18, pady=(16, 8))
        var = tk.StringVar(value=initial)
        entry = tk.Entry(win, textvariable=var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                         insertbackground=THEME["entry_fg"], font=("Cascadia Code", 10),
                         relief="flat", bd=0)
        entry.pack(fill="x", padx=18, pady=4)
        entry.focus_set()
        entry.select_range(0, "end")
        result = {"value": None}
        btns = tk.Frame(win, bg=THEME["bg_card"])
        btns.pack(fill="x", padx=18, pady=12)
        StyledButton(btns, lang.t("btn_ok"), lambda: (result.update(value=var.get()), win.destroy()),
                     color=THEME["success"], hover_color="#55e39a",
                     active_color=THEME["success_dim"],
                     width=90, height=28, font_size=9).pack(side="right", padx=4)
        StyledButton(btns, lang.t("btn_cancel"), win.destroy, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=90, height=28, font_size=9).pack(side="right", padx=4)
        entry.bind("<Return>", lambda e: (result.update(value=var.get()), win.destroy()))
        win.bind("<Escape>", lambda e: win.destroy())
        parent.wait_window(win)
        return result["value"]

    @staticmethod
    def ask_yes_no(parent, title, prompt):
        win = tk.Toplevel(parent)
        win.title(title)
        win.configure(bg=THEME["bg_card"], highlightbackground=THEME["accent"],
                      highlightthickness=1)
        try:
            win.iconbitmap(str(ICON))
        except Exception:
            pass
        DarkPrompt._center(win, parent, 400, 150)
        win.transient(parent)
        win.grab_set()
        tk.Label(win, text=prompt, bg=THEME["bg_card"], fg=THEME["text"],
                 font=(THEME["font_family"], 10), wraplength=360,
                 justify="left").pack(fill="x", padx=18, pady=(18, 10))
        result = {"value": False}
        btns = tk.Frame(win, bg=THEME["bg_card"])
        btns.pack(fill="x", padx=18, pady=10)
        StyledButton(btns, lang.t("btn_yes"), lambda: (result.update(value=True), win.destroy()),
                     color=THEME["success"], hover_color="#55e39a",
                     active_color=THEME["success_dim"],
                     width=90, height=28, font_size=9).pack(side="right", padx=4)
        StyledButton(btns, lang.t("btn_no"), win.destroy, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=90, height=28, font_size=9).pack(side="right", padx=4)
        win.bind("<Escape>", lambda e: win.destroy())
        parent.wait_window(win)
        return result["value"]


COLOR_SCHEMES = {
    "Dark+ (VS Code)": {
        "bg": "#1e1e1e", "fg": "#d4d4d4", "sel_bg": "#264f78", "sel_fg": "#ffffff",
        "keyword": "#569cd6", "string": "#ce9178", "comment": "#6a9955",
        "number": "#b5cea8", "function": "#dcdcaa", "operator": "#d4d4d4",
        "tag": "#569cd6", "attr": "#9cdcfe", "value": "#ce9178",
        "builtin": "#4ec9b0", "decorator": "#dcdcaa",
    },
    "Monokai": {
        "bg": "#272822", "fg": "#f8f8f2", "sel_bg": "#49483e", "sel_fg": "#ffffff",
        "keyword": "#f92672", "string": "#e6db74", "comment": "#75715e",
        "number": "#ae81ff", "function": "#a6e22e", "operator": "#f92672",
        "tag": "#f92672", "attr": "#a6e22e", "value": "#e6db74",
        "builtin": "#66d9ef", "decorator": "#a6e22e",
    },
    "Dracula": {
        "bg": "#282a36", "fg": "#f8f8f2", "sel_bg": "#44475a", "sel_fg": "#ffffff",
        "keyword": "#ff79c6", "string": "#f1fa8c", "comment": "#6272a4",
        "number": "#bd93f9", "function": "#50fa7b", "operator": "#ff79c6",
        "tag": "#ff79c6", "attr": "#50fa7b", "value": "#f1fa8c",
        "builtin": "#8be9fd", "decorator": "#50fa7b",
    },
    "Light": {
        "bg": "#ffffff", "fg": "#383a42", "sel_bg": "#a0a0a0", "sel_fg": "#ffffff",
        "keyword": "#a626a4", "string": "#50a14f", "comment": "#a0a1a7",
        "number": "#986801", "function": "#4078f2", "operator": "#383a42",
        "tag": "#e45649", "attr": "#986801", "value": "#50a14f",
        "builtin": "#c18401", "decorator": "#4078f2",
    },
    "Nord": {
        "bg": "#2e3440", "fg": "#d8dee9", "sel_bg": "#434c5e", "sel_fg": "#eceff4",
        "keyword": "#81a1c1", "string": "#a3be8c", "comment": "#616e88",
        "number": "#b48ead", "function": "#88c0d0", "operator": "#81a1c1",
        "tag": "#81a1c1", "attr": "#8fbcbb", "value": "#a3be8c",
        "builtin": "#8fbcbb", "decorator": "#88c0d0",
    },
    "One Dark": {
        "bg": "#282c34", "fg": "#abb2bf", "sel_bg": "#3e4451", "sel_fg": "#ffffff",
        "keyword": "#c678dd", "string": "#98c379", "comment": "#5c6370",
        "number": "#d19a66", "function": "#61afef", "operator": "#56b6c2",
        "tag": "#e06c75", "attr": "#d19a66", "value": "#98c379",
        "builtin": "#56b6c2", "decorator": "#61afef",
    },
    "Solarized Dark": {
        "bg": "#002b36", "fg": "#839496", "sel_bg": "#073642", "sel_fg": "#fdf6e3",
        "keyword": "#859900", "string": "#2aa198", "comment": "#586e75",
        "number": "#d33682", "function": "#268bd2", "operator": "#859900",
        "tag": "#268bd2", "attr": "#b58900", "value": "#2aa198",
        "builtin": "#2aa198", "decorator": "#268bd2",
    },
    "Night Owl": {
        "bg": "#011627", "fg": "#d6deeb", "sel_bg": "#1d3b53", "sel_fg": "#ffffff",
        "keyword": "#c792ea", "string": "#addb67", "comment": "#637777",
        "number": "#f78c6c", "function": "#82aaff", "operator": "#89ddff",
        "tag": "#7fdbca", "attr": "#addb67", "value": "#ecc48d",
        "builtin": "#7fdbca", "decorator": "#82aaff",
    },
}

HIGHLIGHT_RULES = {
    ".py": [
        ("keyword", r"\b(def|class|import|from|return|if|elif|else|for|while|try|except|finally|with|as|lambda|yield|True|False|None|and|or|not|in|is|global|nonlocal|assert|del|raise|break|continue|pass)\b"),
        ("builtin", r"\b(print|len|range|int|str|float|list|dict|set|tuple|type|isinstance|hasattr|getattr|setattr|open|super|enumerate|zip|map|filter|sorted|reversed|abs|sum|min|max|round|format|input|property|staticmethod|classmethod)\b"),
        ("decorator", r"@\w+"),
        ("string", r'""".*?"""|\'\'\'.*?\'\'\'|"[^"\n]*"|\'[^\'\n]*\''),
        ("comment", r"#.*$"),
        ("number", r"\b\d+\.?\d*\b"),
        ("function", r"\b\w+(?=\()"),
    ],
    ".js": [
        ("keyword", r"\b(var|let|const|function|return|if|else|for|while|do|switch|case|break|continue|try|catch|finally|throw|new|delete|typeof|instanceof|in|of|class|extends|super|import|export|default|from|async|await|yield|this|null|undefined|true|false)\b"),
        ("builtin", r"\b(console|document|window|Math|JSON|Array|Object|String|Number|Boolean|Date|RegExp|Error|Promise|Map|Set|Symbol|Proxy|Reflect|parseInt|parseFloat|isNaN|isFinite|encodeURI|decodeURI)\b"),
        ("string", r'`[^`]*`|"[^"\n]*"|\'[^\'\n]*\''),
        ("comment", r"//.*$|/\*.*?\*/"),
        ("number", r"\b\d+\.?\d*([eE][+-]?\d+)?\b"),
        ("function", r"\b\w+(?=\()"),
    ],
    ".ts": [
        ("keyword", r"\b(var|let|const|function|return|if|else|for|while|do|switch|case|break|continue|try|catch|finally|throw|new|delete|typeof|instanceof|in|of|class|extends|super|import|export|default|from|async|await|yield|this|null|undefined|true|false|interface|type|enum|namespace|declare|abstract|implements|readonly|private|protected|public|static|as|is|keyof|infer|never|unknown|any|void|string|number|boolean|bigint|symbol|object)\b"),
        ("builtin", r"\b(console|document|window|Math|JSON|Array|Object|String|Number|Boolean|Date|RegExp|Error|Promise|Map|Set|Record|Partial|Required|Pick|Omit|Exclude|Extract|ReturnType|InstanceType|Parameters|ConstructorParameters)\b"),
        ("string", r'`[^`]*`|"[^"\n]*"|\'[^\'\n]*\''),
        ("comment", r"//.*$|/\*.*?\*/"),
        ("number", r"\b\d+\.?\d*([eE][+-]?\d+)?\b"),
        ("function", r"\b\w+(?=\()"),
    ],
    ".html": [
        ("tag", r"</?[a-zA-Z][a-zA-Z0-9]*"),
        ("attr", r"\b[a-zA-Z-]+(?==)"),
        ("value", r'"[^"]*"|\'[^\']*\''),
        ("comment", r"<!--.*?-->"),
        ("string", r"[^<>&\"'\s]+"),
    ],
    ".htm": [
        ("tag", r"</?[a-zA-Z][a-zA-Z0-9]*"),
        ("attr", r"\b[a-zA-Z-]+(?==)"),
        ("value", r'"[^"]*"|\'[^\']*\''),
        ("comment", r"<!--.*?-->"),
        ("string", r"[^<>&\"'\s]+"),
    ],
    ".css": [
        ("keyword", r"@[a-zA-Z-]+"),
        ("string", r'"[^"]*"|\'[^\']*\''),
        ("comment", r"/\*.*?\*/"),
        ("number", r"#[0-9a-fA-F]{3,8}\b|\b\d+\.?\d*(px|em|rem|%|vh|vw|s|ms)?\b"),
        ("function", r"\b[a-zA-Z-]+(?=\()"),
        ("attr", r"[.#][a-zA-Z_][\w-]*"),
    ],
    ".php": [
        ("keyword", r"\b(function|class|return|if|else|elseif|for|foreach|while|do|switch|case|break|continue|try|catch|finally|throw|new|instanceof|isset|unset|empty|echo|print|require|include|require_once|include_once|namespace|use|public|protected|private|static|final|abstract|interface|extends|implements|trait|yield|match|fn|readonly|enum)\b"),
        ("builtin", r"\b(array|bool|float|int|string|null|object|callable|iterable|void|never|self|parent|static|mixed|true|false|TRUE|FALSE|NULL)\b"),
        ("string", r'"[^"$]*?\$[^"$]*?"|\'[^\'\n]*\''),
        ("comment", r"//.*$|#.*$|/\*.*?\*/"),
        ("number", r"\b\d+\.?\d*\b"),
        ("function", r"\b\w+(?=\()"),
    ],
    ".json": [
        ("string", r'"[^"]*"(?=\s*:)'),
        ("keyword", r'"[^"]*"'),
        ("number", r"\b-?\d+\.?\d*([eE][+-]?\d+)?\b"),
        ("builtin", r"\b(true|false|null)\b"),
    ],
    ".md": [
        ("keyword", r"^#{1,6}\s|^\*\*|^-\s|^\d+\.\s"),
        ("string", r"`[^`]+`"),
        ("comment", r"^\>.*$"),
        ("function", r"\[.*?\]\(.*?\)"),
    ],
    ".sql": [
        ("keyword", r"\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|DROP|ALTER|TABLE|INDEX|VIEW|DATABASE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|EXISTS|BETWEEN|LIKE|ORDER|BY|GROUP|HAVING|LIMIT|OFFSET|UNION|ALL|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|NULL|IS|PRIMARY|KEY|FOREIGN|REFERENCES|CONSTRAINT|DEFAULT|AUTO_INCREMENT|VARCHAR|INT|INTEGER|TEXT|BOOLEAN|DATE|DATETIME|TIMESTAMP|FLOAT|DOUBLE|DECIMAL|CHAR|BLOB|ENUM|SET|TRUNCATE|REPLACE|GRANT|REVOKE|COMMIT|ROLLBACK|BEGIN|TRANSACTION)\b"),
        ("string", r"'[^']*'|\"[^\"]*\""),
        ("comment", r"--.*$|/\*.*?\*/"),
        ("number", r"\b\d+\.?\d*\b"),
        ("function", r"\b\w+(?=\()"),
    ],
    ".ini": [
        ("keyword", r"^\[[^\]]+\]"),
        ("comment", r"[;#].*$"),
        ("function", r"^\w+(?==)"),
        ("string", r"=.*$"),
    ],
    ".conf": [
        ("keyword", r"^\w[\w-]*(?=\s)"),
        ("comment", r"[#;].*$"),
        ("string", r".*"),
    ],
    ".xml": [
        ("tag", r"</?[a-zA-Z][a-zA-Z0-9:]*"),
        ("attr", r"\b[a-zA-Z:]+(?==)"),
        ("value", r'"[^"]*"|\'[^\']*\''),
        ("comment", r"<!--.*?-->"),
    ],
}


EDITOR_CONF = APP_ROOT / "config" / "editor.json"

class CodeEditor:
    def __init__(self, parent, filepath, save_callback=None):
        self.filepath = filepath
        self.save_callback = save_callback
        self.ext = filepath.suffix.lower()
        self._editor_conf = {}
        try:
            if EDITOR_CONF.exists():
                self._editor_conf = json.loads(EDITOR_CONF.read_text(encoding="utf-8"))
        except Exception:
            self._editor_conf = {}
        theme_name = self._editor_conf.get("theme", "Dark+ (VS Code)")
        self.scheme = COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Dark+ (VS Code)"])
        self._theme_name = theme_name if theme_name in COLOR_SCHEMES else "Dark+ (VS Code)"
        self.font_family = self._editor_conf.get("font", "Cascadia Code")
        try:
            self.font_size = int(self._editor_conf.get("size", 11))
        except (TypeError, ValueError):
            self.font_size = 11

        self.win = tk.Toplevel(parent)
        self.win.title(f"Edit: {filepath.name}")
        self.win.geometry("1000x650")
        self.win.configure(bg=self.scheme["bg"])

        toolbar = tk.Frame(self.win, bg="#2d2d2d")
        toolbar.pack(fill="x")

        tk.Label(toolbar, text=str(filepath.name), bg="#2d2d2d", fg="#cccccc",
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)

        tk.Label(toolbar, text="Font:", bg="#2d2d2d", fg="#888888",
                 font=("Segoe UI", 8)).pack(side="left", padx=(20, 2))
        self._font_var = tk.StringVar(value=self.font_family)
        font_menu = tk.OptionMenu(toolbar, self._font_var, "Cascadia Code", "Consolas",
                                  "Courier New", "Source Code Pro", "Fira Code",
                                  command=self._change_font)
        font_menu.configure(bg="#3c3c3c", fg="#cccccc", activebackground="#505050",
                            activeforeground="#ffffff", relief="flat", font=("Segoe UI", 8),
                            highlightthickness=0)
        font_menu["menu"].configure(bg="#2d2d2d", fg="#cccccc", activebackground="#505050")
        font_menu.pack(side="left", padx=4)

        tk.Label(toolbar, text="Size:", bg="#2d2d2d", fg="#888888",
                 font=("Segoe UI", 8)).pack(side="left", padx=(8, 2))
        self._size_var = tk.StringVar(value=str(self.font_size))
        size_menu = tk.OptionMenu(toolbar, self._size_var, "8", "9", "10", "11", "12",
                                  "13", "14", "16", "18", "20", "24",
                                  command=self._change_font)
        size_menu.configure(bg="#3c3c3c", fg="#cccccc", activebackground="#505050",
                            activeforeground="#ffffff", relief="flat", font=("Segoe UI", 8),
                            highlightthickness=0)
        size_menu["menu"].configure(bg="#2d2d2d", fg="#cccccc", activebackground="#505050")
        size_menu.pack(side="left", padx=4)

        tk.Label(toolbar, text="Theme:", bg="#2d2d2d", fg="#888888",
                 font=("Segoe UI", 8)).pack(side="left", padx=(8, 2))
        self._theme_var = tk.StringVar(value=self._theme_name)
        theme_menu = tk.OptionMenu(toolbar, self._theme_var, *COLOR_SCHEMES.keys(),
                                   command=self._change_theme)
        theme_menu.configure(bg="#3c3c3c", fg="#cccccc", activebackground="#505050",
                             activeforeground="#ffffff", relief="flat", font=("Segoe UI", 8),
                             highlightthickness=0)
        theme_menu["menu"].configure(bg="#2d2d2d", fg="#cccccc", activebackground="#505050")
        theme_menu.pack(side="left", padx=4)

        save_btn = StyledButton(toolbar, "Save", self._save,
                                color=THEME["success"], hover_color="#10d8a0",
                                active_color=THEME["success_dim"], width=70, height=26, font_size=8)
        save_btn.pack(side="right", padx=5, pady=3)
        close_btn = StyledButton(toolbar, "Close", self.win.destroy,
                                 color=THEME["danger"], hover_color="#ff6b5a",
                                 active_color=THEME["danger_dim"], width=70, height=26, font_size=8)
        close_btn.pack(side="right", padx=5, pady=3)
        wrap_btn = StyledButton(toolbar, "Wrap", self._toggle_wrap,
                                color="#3c3c3c", hover_color="#505050",
                                active_color="#2d2d2d", width=60, height=26, font_size=8)
        wrap_btn.pack(side="right", padx=5, pady=3)
        find_btn = StyledButton(toolbar, "Find", self._find_dialog,
                                color="#3c3c3c", hover_color="#505050",
                                active_color="#2d2d2d", width=60, height=26, font_size=8)
        find_btn.pack(side="right", padx=5, pady=3)

        body = tk.Frame(self.win, bg=self.scheme["bg"])
        body.pack(fill="both", expand=True)

        statusbar = tk.Frame(self.win, bg="#2d2d2d")
        statusbar.pack(fill="x", side="bottom")
        self._status_var = tk.StringVar(value="Ln 1, Col 1")
        tk.Label(statusbar, textvariable=self._status_var, bg="#2d2d2d", fg="#888888",
                 font=("Segoe UI", 8), anchor="w").pack(side="left", padx=10)
        tk.Label(statusbar, text="Ctrl+F find · Ctrl+H replace · Ctrl+G line · Ctrl+D duplicate · Ctrl+/ comment",
                 bg="#2d2d2d", fg="#666666", font=("Segoe UI", 8)).pack(side="right", padx=10)

        self._line_numbers = tk.Text(body, width=5, padx=6, pady=8,
                                     bg="#1e1e1e", fg="#858585",
                                     font=(self.font_family, self.font_size),
                                     state="disabled", relief="flat", bd=0,
                                     selectbackground="#1e1e1e", cursor="arrow",
                                     takefocus=0)
        self._line_numbers.pack(side="left", fill="y")

        self._minimap = tk.Text(body, width=60, padx=2, pady=8,
                                bg=self.scheme["bg"], fg=self.scheme["fg"],
                                font=(self.font_family, 3),
                                state="disabled", relief="flat", bd=0,
                                cursor="arrow", takefocus=0, wrap="none")
        self._minimap.pack(side="right", fill="y")
        self._minimap.bind("<Button-1>", self._minimap_jump)
        self._minimap.bind("<B1-Motion>", self._minimap_jump)
        self._mm_after = None

        self._text = tk.Text(body, wrap="word", padx=10, pady=8,
                             bg=self.scheme["bg"], fg=self.scheme["fg"],
                             insertbackground="white",
                             font=(self.font_family, self.font_size),
                             relief="flat", bd=0,
                             selectbackground=self.scheme["sel_bg"],
                             selectforeground=self.scheme["sel_fg"],
                             undo=True, autoseparators=True)
        self._text.pack(side="left", fill="both", expand=True)

        self._text.bind("<KeyRelease>", self._on_change)
        self._text.bind("<ButtonRelease-1>", lambda e: self._update_status())
        self._text.bind("<MouseWheel>", self._on_scroll)
        self._text.bind("<Button-4>", self._on_scroll)
        self._text.bind("<Button-5>", self._on_scroll)
        self._text.bind("<Control-s>", lambda e: self._save())
        self._text.bind("<Control-a>", lambda e: self._select_all())
        self._text.bind("<Control-c>", lambda e: self._copy_or_line())
        self._text.bind("<Control-x>", lambda e: self._cut_or_line())
        self._text.bind("<Control-v>", lambda e: self._paste())
        self._text.bind("<Control-z>", lambda e: self._undo())
        self._text.bind("<Control-y>", lambda e: self._redo())
        self._text.bind("<Control-Shift-Z>", lambda e: self._redo())
        self._text.bind("<Control-f>", lambda e: self._find_dialog())
        self._text.bind("<Control-h>", lambda e: self._find_dialog(replace=True))
        self._text.bind("<Control-g>", lambda e: self._goto_line())
        self._text.bind("<Control-d>", lambda e: self._duplicate())
        self._text.bind("<Control-slash>", lambda e: self._toggle_comment())
        self._text.bind("<Control-equal>", lambda e: self._zoom(1))
        self._text.bind("<Control-plus>", lambda e: self._zoom(1))
        self._text.bind("<Control-minus>", lambda e: self._zoom(-1))
        self._text.bind("<Control-0>", lambda e: self._zoom(0))
        self._text.bind("<Alt-z>", lambda e: self._toggle_wrap())
        self._text.bind("<KeyPress>", self._auto_pair)
        self._text.bind("<Tab>", self._handle_tab)
        self._text.bind("<Shift-Tab>", lambda e: self._unindent())
        self._text.bind("<Button-3>", self._context_menu)
        self._find_last = ""

    def _context_menu(self, event):
        menu = tk.Menu(self.win, tearoff=False, bg="#2d2d2d", fg="#cccccc",
                       activebackground="#505050", activeforeground="#ffffff",
                       font=("Segoe UI", 9), relief="flat", bd=1)
        menu.add_command(label="Cut\tCtrl+X", command=lambda: self._cut_or_line())
        menu.add_command(label="Copy\tCtrl+C", command=lambda: self._copy_or_line())
        menu.add_command(label="Paste\tCtrl+V", command=lambda: self._paste())
        menu.add_separator()
        menu.add_command(label="Select All\tCtrl+A", command=lambda: self._select_all())
        menu.add_separator()
        menu.add_command(label="Find\tCtrl+F", command=lambda: self._find_dialog())
        menu.add_command(label="Replace\tCtrl+H",
                         command=lambda: self._find_dialog(replace=True))
        menu.add_command(label="Go to Line\tCtrl+G", command=lambda: self._goto_line())
        menu.add_separator()
        menu.add_command(label="Duplicate\tCtrl+D", command=lambda: self._duplicate())
        menu.add_command(label="Toggle Comment\tCtrl+/",
                         command=lambda: self._toggle_comment())
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

        self._setup_tags()
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            self._text.insert("1.0", content)
        except Exception as e:
            self._text.insert("1.0", f"Error reading file: {e}")

        self._update_line_numbers()
        self._highlight()
        self._refresh_minimap()

    def _refresh_minimap(self):
        self._mm_after = None
        try:
            content = self._text.get("1.0", "end-1c")
            self._minimap.configure(state="normal")
            self._minimap.delete("1.0", "end")
            self._minimap.insert("1.0", content)
            self._minimap.configure(state="disabled")
        except Exception:
            pass
        self._minimap_sync()

    def _minimap_schedule(self):
        if self._mm_after is not None:
            try:
                self.win.after_cancel(self._mm_after)
            except Exception:
                pass
            self._mm_after = None
        try:
            self._mm_after = self.win.after(400, self._refresh_minimap)
        except Exception:
            pass

    def _minimap_sync(self):
        try:
            self._minimap.yview_moveto(self._text.yview()[0])
        except Exception:
            pass

    def _minimap_jump(self, e=None):
        try:
            line = int(self._minimap.index(f"@0,{e.y}").split(".")[0])
            total = max(int(self._text.index("end-1c").split(".")[0]), 1)
            self._text.yview_moveto(max(0.0, min(1.0, (line - 2) / total)))
            self._minimap_sync()
        except Exception:
            pass
        return "break"

    def _sel_range(self):
        try:
            if self._text.tag_ranges("sel"):
                return (self._text.index("sel.first"), self._text.index("sel.last"))
        except tk.TclError:
            pass
        return None

    def _update_status(self):
        try:
            line, col = self._text.index("insert").split(".")
            nlines = int(self._text.index("end-1c").split(".")[0])
            nchars = len(self._text.get("1.0", "end-1c"))
            self._status_var.set(f"Ln {line}, Col {int(col) + 1}   |   {nlines} lines, {nchars} chars")
        except Exception:
            pass

    def _apply_font(self):
        font = (self.font_family, self.font_size)
        self._text.configure(font=font)
        self._line_numbers.configure(font=font)
        try:
            self._minimap.configure(font=(self.font_family, 3))
        except Exception:
            pass
        self._update_line_numbers()

    def _select_all(self):
        self._text.tag_add("sel", "1.0", "end-1c")
        self._text.mark_set("insert", "end-1c")
        self._text.see("insert")
        return "break"

    def _copy_or_line(self):
        rng = self._sel_range()
        try:
            self.win.clipboard_clear()
            if rng:
                self.win.clipboard_append(self._text.get(rng[0], rng[1]))
            else:
                line = int(self._text.index("insert").split(".")[0])
                self.win.clipboard_append(self._text.get(f"{line}.0", f"{line}.end") + "\n")
        except Exception:
            pass
        return "break"

    def _cut_or_line(self):
        rng = self._sel_range()
        try:
            self.win.clipboard_clear()
            if rng:
                self.win.clipboard_append(self._text.get(rng[0], rng[1]))
                self._text.delete(rng[0], rng[1])
            else:
                line = int(self._text.index("insert").split(".")[0])
                self.win.clipboard_append(self._text.get(f"{line}.0", f"{line}.end") + "\n")
                last = int(self._text.index("end-1c").split(".")[0])
                if line < last:
                    self._text.delete(f"{line}.0", f"{line + 1}.0")
                else:
                    self._text.delete(f"{line}.0", f"{line}.end")
            self._on_change()
        except Exception:
            pass
        return "break"

    def _paste(self):
        try:
            self._text.event_generate("<<Paste>>")
        except Exception:
            pass
        self.win.after_idle(self._on_change)
        return "break"

    def _undo(self):
        try:
            self._text.edit_undo()
            self._on_change()
        except Exception:
            pass
        return "break"

    def _redo(self):
        try:
            self._text.edit_redo()
            self._on_change()
        except Exception:
            pass
        return "break"

    def _zoom(self, step):
        if step == 0:
            self.font_size = 11
        else:
            self.font_size = max(6, min(32, self.font_size + step))
        self._size_var.set(str(self.font_size))
        self._apply_font()
        self._save_editor_conf()
        return "break"

    def _toggle_wrap(self):
        try:
            cur = str(self._text.cget("wrap"))
            self._text.configure(wrap="none" if cur == "word" else "word")
        except Exception:
            pass
        return "break"

    def _goto_line(self):
        try:
            val = DarkPrompt.ask_string(self.win, "Go to line", "Line number:")
            if not val:
                return "break"
            line = max(1, int(val))
            total = int(self._text.index("end-1c").split(".")[0])
            line = min(line, total)
            self._text.mark_set("insert", f"{line}.0")
            self._text.see(f"{line}.0")
            self._update_status()
        except Exception:
            pass
        return "break"

    def _duplicate(self):
        try:
            rng = self._sel_range()
            if rng:
                s, e = rng
                if not e.endswith(".0"):
                    e = self._text.index(f"{e.split('.')[0]}.end")
                else:
                    e = self._text.index(f"{int(e.split('.')[0]) - 1}.end")
                text = self._text.get(s, e)
                self._text.insert(e, "\n" + text)
            else:
                line = int(self._text.index("insert").split(".")[0])
                text = self._text.get(f"{line}.0", f"{line}.end")
                last = int(self._text.index("end-1c").split(".")[0])
                if line >= last:
                    self._text.insert("end-1c", "\n" + text)
                else:
                    self._text.insert(f"{line + 1}.0", text + "\n")
            self._on_change()
        except Exception:
            pass
        return "break"

    def _comment_prefix(self):
        mapping = {".py": "#", ".sh": "#", ".sql": "#", ".ini": "#", ".conf": "#",
                   ".js": "//", ".ts": "//", ".php": "//", ".java": "//", ".c": "//",
                   ".cpp": "//", ".cs": "//", ".go": "//", ".rs": "//",
                   ".html": "<!--", ".htm": "<!--", ".xml": "<!--", ".vue": "<!--",
                   ".css": "/*"}
        return mapping.get(self.ext)

    def _toggle_comment(self):
        try:
            pre = self._comment_prefix()
            if not pre:
                return "break"
            rng = self._sel_range()
            if rng:
                start = int(rng[0].split(".")[0])
                end = int(rng[1].split(".")[0])
                if rng[1].endswith(".0") and end > start:
                    end -= 1
            else:
                start = end = int(self._text.index("insert").split(".")[0])
            lines = []
            for ln in range(start, end + 1):
                lines.append(self._text.get(f"{ln}.0", f"{ln}.end"))
            non_empty = [l for l in lines if l.strip()]
            if not non_empty:
                return "break"
            if pre in ("<!--", "/*"):
                suf = {"<!--": " -->", "/*": " */"}[pre]
                if all(l.strip().startswith(pre) and l.strip().endswith(suf) for l in non_empty):
                    new = [l.replace(pre, "", 1).rsplit(suf, 1)[0] if l.strip().startswith(pre) else l
                           for l in lines]
                else:
                    new = [(l[:len(l) - len(l.lstrip())] + pre + " " + l.lstrip() + " " + suf)
                           if l.strip() else l for l in lines]
            else:
                if all(l.lstrip().startswith(pre) for l in non_empty):
                    new = []
                    for l in lines:
                        s = l.lstrip()
                        if s.startswith(pre):
                            indent = l[:len(l) - len(s)]
                            rest = s[len(pre):]
                            if rest.startswith(" "):
                                rest = rest[1:]
                            new.append(indent + rest)
                        else:
                            new.append(l)
                else:
                    new = [(l[:len(l) - len(l.lstrip())] + pre + " " + l.lstrip())
                           if l.strip() else l for l in lines]
            for i, ln in enumerate(range(start, end + 1)):
                self._text.delete(f"{ln}.0", f"{ln}.end")
                self._text.insert(f"{ln}.0", new[i])
            self._on_change()
        except Exception:
            pass
        return "break"

    def _auto_pair(self, e=None):
        try:
            if e is None or not e.char:
                return
            pairs = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
            closers = set(")]}'\"")
            if e.char in pairs:
                try:
                    nxt = self._text.get("insert")
                except Exception:
                    nxt = ""
                if e.char in "\"'" and nxt == e.char:
                    self._text.mark_set("insert", "insert+1c")
                    return "break"
                rng = self._sel_range()
                if rng:
                    s, ee = rng
                    self._text.insert(ee, pairs[e.char])
                    self._text.insert(s, e.char)
                    return "break"
                if e.char in "\"'":
                    try:
                        cur = self._text.get("insert linestart", "insert")
                    except Exception:
                        cur = ""
                    if cur and (cur[-1].isalnum() or cur[-1] == "_"):
                        return
                self._text.insert("insert", e.char + pairs[e.char])
                self._text.mark_set("insert", "insert-1c")
                self._on_change()
                return "break"
            elif e.char in closers:
                try:
                    nxt = self._text.get("insert")
                except Exception:
                    nxt = ""
                if nxt == e.char:
                    self._text.mark_set("insert", "insert+1c")
                    return "break"
        except Exception:
            pass

    def _find_dialog(self, replace=False):
        if getattr(self, "_find_win", None) is not None:
            try:
                if self._find_win.winfo_exists():
                    self._find_win.lift()
                    self._find_win.focus_force()
                    return
            except Exception:
                pass
        win = tk.Toplevel(self.win)
        self._find_win = win
        win.title("Replace" if replace else "Find")
        win.configure(bg="#2d2d2d")
        win.geometry("420x210" if replace else "420x130")
        win.transient(self.win)
        tk.Label(win, text="Find:", bg="#2d2d2d", fg="#cccccc",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(10, 0))
        fvar = tk.StringVar(value=getattr(self, "_find_last", ""))
        fentry = tk.Entry(win, textvariable=fvar, bg="#3c3c3c", fg="#ffffff",
                          insertbackground="white", font=("Consolas", 10),
                          relief="flat", bd=0)
        fentry.pack(fill="x", padx=12, pady=4)
        fentry.focus_set()
        fentry.select_range(0, "end")
        rvar = tk.StringVar(value="")
        rentry = None
        if replace:
            tk.Label(win, text="Replace with:", bg="#2d2d2d", fg="#cccccc",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=12)
            rentry = tk.Entry(win, textvariable=rvar, bg="#3c3c3c", fg="#ffffff",
                              insertbackground="white", font=("Consolas", 10),
                              relief="flat", bd=0)
            rentry.pack(fill="x", padx=12, pady=4)
        case_var = tk.BooleanVar(value=False)
        tk.Checkbutton(win, text="Match case", variable=case_var, bg="#2d2d2d", fg="#cccccc",
                       selectcolor="#3c3c3c", activebackground="#2d2d2d",
                       activeforeground="#cccccc", font=("Segoe UI", 8),
                       highlightthickness=0, bd=0).pack(anchor="w", padx=12)
        btns = tk.Frame(win, bg="#2d2d2d")
        btns.pack(fill="x", padx=12, pady=8)
        for label, cmd in ([("◀ Prev", lambda: self._find_step(fvar.get(), bool(case_var.get()), -1)),
                            ("Next ▶", lambda: self._find_step(fvar.get(), bool(case_var.get()), 1))] +
                           ([("Replace", lambda: self._find_replace(fvar.get(), rvar.get(), bool(case_var.get()))),
                             ("All", lambda: self._find_replace_all(fvar.get(), rvar.get(), bool(case_var.get())))]
                            if replace else [])):
            tk.Button(btns, text=label, command=cmd, bg="#3c3c3c", fg="#ffffff",
                      activebackground="#505050", activeforeground="#ffffff",
                      relief="flat", bd=0, font=("Segoe UI", 8), padx=10, pady=3).pack(side="left", padx=3)
        fentry.bind("<Return>", lambda e: self._find_step(fvar.get(), bool(case_var.get()), 1))
        fentry.bind("<Escape>", lambda e: win.destroy())

    def _find_step(self, pattern, case, direction):
        if not pattern:
            return
        self._find_last = pattern
        try:
            self._text.tag_remove("find_hit", "1.0", "end")
            self._text.tag_configure("find_hit", background="#515c6a", foreground="#ffffff")
            start = "insert+1c" if direction > 0 else "insert-1c"
            pos = self._text.search(pattern, start, stopindex="end" if direction > 0 else "1.0",
                                    forwards=direction > 0, backwards=direction < 0,
                                    nocase=not case)
            if not pos:
                pos = self._text.search(pattern, "1.0" if direction > 0 else "end",
                                        forwards=direction > 0, backwards=direction < 0,
                                        nocase=not case)
            if not pos:
                return
            count = tk.IntVar()
            self._text.search(pattern, pos, stopindex="end", regexp=False, count=count)
            ln = count.get() or len(pattern)
            end = f"{pos}+{ln}c"
            self._text.tag_add("find_hit", pos, end)
            self._text.tag_add("sel", pos, end)
            self._text.mark_set("insert", end if direction > 0 else pos)
            self._text.see(pos)
        except Exception:
            pass

    def _find_replace(self, pattern, repl, case):
        if not pattern:
            return
        try:
            rng = self._sel_range()
            if rng and self._text.get(rng[0], rng[1]) == (pattern if case else self._text.get(rng[0], rng[1])):
                check = self._text.get(rng[0], rng[1])
                if (check == pattern) or (not case and check.lower() == pattern.lower()):
                    self._text.delete(rng[0], rng[1])
                    self._text.insert(rng[0], repl)
                    self._on_change()
        except Exception:
            pass
        self._find_step(pattern, case, 1)

    def _find_replace_all(self, pattern, repl, case):
        if not pattern:
            return
        try:
            count = 0
            start = "1.0"
            while True:
                pos = self._text.search(pattern, start, stopindex="end", nocase=not case)
                if not pos:
                    break
                cvar = tk.IntVar()
                self._text.search(pattern, pos, stopindex="end", regexp=False, count=cvar)
                ln = cvar.get() or len(pattern)
                end = f"{pos}+{ln}c"
                self._text.delete(pos, end)
                self._text.insert(pos, repl)
                count += 1
                start = f"{pos}+{len(repl)}c"
                if count > 100000:
                    break
            self._on_change()
            self._find_last = pattern
        except Exception:
            pass

    def _setup_tags(self):
        for name, color in self.scheme.items():
            if name in ("bg", "fg", "sel_bg", "sel_fg"):
                continue
            self._text.tag_configure(name, foreground=color)
        self._text.tag_configure("sel", background=self.scheme["sel_bg"],
                                 foreground=self.scheme["sel_fg"])

    def _highlight(self):
        for tag in self._text.tag_names():
            if tag not in ("sel", "insert"):
                self._text.tag_remove(tag, "1.0", "end")
        rules = HIGHLIGHT_RULES.get(self.ext, [])
        if not rules:
            for ext_key in HIGHLIGHT_RULES:
                if self.ext.endswith(ext_key):
                    rules = HIGHLIGHT_RULES[ext_key]
                    break
        for tag_name, pattern in rules:
            start = "1.0"
            while True:
                count_var = tk.IntVar()
                match = self._text.search(pattern, start, stopindex="end",
                                          regexp=True, count=count_var)
                if not match:
                    break
                match_len = count_var.get()
                if match_len == 0:
                    start = f"{match}+1c"
                    continue
                end_pos = f"{match}+{match_len}c"
                self._text.tag_add(tag_name, match, end_pos)
                start = end_pos

    def _update_line_numbers(self):
        self._line_numbers.configure(state="normal")
        self._line_numbers.delete("1.0", "end")
        line_count = int(self._text.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self._line_numbers.insert("1.0", numbers)
        self._line_numbers.configure(state="disabled")

    def _on_change(self, e=None):
        self._update_line_numbers()
        self._highlight()
        self._minimap_schedule()
        self._update_status()

    def _on_scroll(self, e=None):
        if e:
            if hasattr(e, "delta"):
                self._line_numbers.yview_scroll(-1 * (e.delta // 120), "units")
            elif e.num == 4:
                self._line_numbers.yview_scroll(-1, "units")
            elif e.num == 5:
                self._line_numbers.yview_scroll(1, "units")
        self._line_numbers.yview_moveto(self._text.yview()[0])
        self._minimap_sync()

    def _handle_tab(self, e):
        try:
            rng = self._sel_range()
            if rng:
                start = int(rng[0].split(".")[0])
                end = int(rng[1].split(".")[0])
                if rng[1].endswith(".0") and end > start:
                    end -= 1
                for ln in range(start, end + 1):
                    self._text.insert(f"{ln}.0", "    ")
                self._on_change()
                return "break"
        except Exception:
            pass
        self._text.insert("insert", "    ")
        return "break"

    def _unindent(self):
        try:
            rng = self._sel_range()
            if rng:
                start = int(rng[0].split(".")[0])
                end = int(rng[1].split(".")[0])
                if rng[1].endswith(".0") and end > start:
                    end -= 1
                lines = list(range(start, end + 1))
            else:
                lines = [int(self._text.index("insert").split(".")[0])]
            for ln in lines:
                line = self._text.get(f"{ln}.0", f"{ln}.end")
                if line.startswith("    "):
                    self._text.delete(f"{ln}.0", f"{ln}.4")
                elif line.startswith("\t"):
                    self._text.delete(f"{ln}.0", f"{ln}.1")
            self._on_change()
        except Exception:
            pass
        return "break"

    def _save_editor_conf(self):
        self._editor_conf.update({"font": self.font_family, "size": self.font_size,
                                  "theme": self._theme_name})
        try:
            EDITOR_CONF.parent.mkdir(parents=True, exist_ok=True)
            EDITOR_CONF.write_text(json.dumps(self._editor_conf, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _change_font(self, e=None):
        self.font_family = self._font_var.get()
        self.font_size = int(self._size_var.get())
        self._apply_font()
        try:
            self._minimap.configure(font=(self.font_family, 3))
        except Exception:
            pass
        self._update_line_numbers()
        self._save_editor_conf()

    def _change_theme(self, e=None):
        name = self._theme_var.get()
        if name in COLOR_SCHEMES:
            self._theme_name = name
            self.scheme = COLOR_SCHEMES[name]
            self.win.configure(bg=self.scheme["bg"])
            self._text.configure(bg=self.scheme["bg"], fg=self.scheme["fg"],
                                 selectbackground=self.scheme["sel_bg"],
                                 selectforeground=self.scheme["sel_fg"])
            self._line_numbers.configure(bg="#1e1e1e")
            try:
                self._minimap.configure(bg=self.scheme["bg"], fg=self.scheme["fg"])
            except Exception:
                pass
            self._setup_tags()
            self._highlight()
            self._save_editor_conf()

    def _save(self):
        try:
            content = self._text.get("1.0", "end-1c")
            self.filepath.write_text(content, encoding="utf-8")
            self.win.title(f"Edit: {self.filepath.name} [Saved]")
            if self.save_callback:
                self.save_callback()
        except Exception as e:
            messagebox.showerror("Save Error", str(e))


def run_perf_child(cfg_path):
    import random as _r
    import threading as _th
    from concurrent.futures import ThreadPoolExecutor
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    base, users, dur = cfg["base"], int(cfg["users"]), int(cfg["dur"])
    paths = [(m, p, int(w)) for m, p, w in cfg["paths"]]
    weights = [x[2] for x in paths]
    out_path = cfg["out"]
    stop = _th.Event()
    lock = _th.Lock()
    tot = {"n": 0, "err": 0, "bytes": 0, "active": 0}
    sec = {"n": 0, "err": 0, "bytes": 0, "lat": []}
    local = _th.local()

    def get_session():
        s = getattr(local, "s", None)
        if s is None:
            s = requests.Session()
            s.trust_env = False
            local.s = s
        return s

    def worker(deadline):
        with lock:
            tot["active"] += 1
        try:
            while not stop.is_set() and time.monotonic() < deadline:
                m, p, _w = _r.choices(paths, weights=weights)[0]
                url = base + (p if p.startswith("/") else "/" + p)
                data = b"perf=1" if m in ("POST", "PUT", "PATCH") else None
                t1 = time.monotonic()
                try:
                    r = get_session().request(m, url, data=data, timeout=10)
                    dt = (time.monotonic() - t1) * 1000.0
                    ok = r.status_code < 400
                    ln = len(r.content or b"")
                except Exception:
                    dt = (time.monotonic() - t1) * 1000.0
                    ok = False
                    ln = 0
                with lock:
                    tot["n"] += 1
                    sec["n"] += 1
                    if not ok:
                        tot["err"] += 1
                        sec["err"] += 1
                    tot["bytes"] += ln
                    sec["bytes"] += ln
                    sec["lat"].append(dt)
        finally:
            with lock:
                tot["active"] -= 1

    t0 = time.monotonic()
    deadline = t0 + dur
    threads = max(1, min(users, 2000))
    ex = ThreadPoolExecutor(max_workers=threads)
    try:
        futs = [ex.submit(worker, deadline) for _ in range(users)]
        with open(out_path, "w", encoding="utf-8") as f:
            while time.monotonic() < deadline + 2 and not stop.is_set():
                time.sleep(1.0)
                with lock:
                    line = json.dumps({"t": round(time.monotonic() - t0, 1),
                                       "n": tot["n"], "err": tot["err"],
                                       "bytes": tot["bytes"], "active": tot["active"],
                                       "lat": sec["lat"]})
                    sec["n"] = 0
                    sec["err"] = 0
                    sec["bytes"] = 0
                    sec["lat"] = []
                f.write(line + "\n")
                f.flush()
            with lock:
                f.write(json.dumps({"done": True, "n": tot["n"], "err": tot["err"]}) + "\n")
                f.flush()
    finally:
        stop.set()
        ex.shutdown(wait=True)


class App:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title(f"{APP_NAME} V16")
        self.root.geometry("1280x860")
        self.root.minsize(1120,750)
        self.root.configure(bg=THEME["bg"])
        try:
            import ctypes as _ct
            _ct.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Faraja.WebServer.PRO")
        except Exception:
            pass
        try:
            if LOGO_PNG.exists():
                self._app_icon_img = ImageTk.PhotoImage(Image.open(str(LOGO_PNG)).resize((32, 32), Image.LANCZOS))
                self.root.iconphoto(True, self._app_icon_img)
            else:
                self.root.iconbitmap(str(ICON))
        except Exception:
            try:
                self.root.iconbitmap(str(ICON))
            except Exception:
                pass
        self.lines=[];self.svc=Services(self.log);self.tray=None;self.closing=False
        # Scrollable pages register their canvases here.  A single application-wide
        # wheel handler then routes the wheel to the currently visible page, so
        # scrolling is not dependent on the mouse being over a narrow scrollbar.
        self._scroll_canvases = []
        self._install_global_wheel()
        self._pulse = 0
        self._docker_ok = False
        self.build()
        if not is_admin():
            self.log(lang.t("admin_hint"))
        threading.Thread(target=self._docker_poll, daemon=True).start()
        threading.Thread(target=self._startup_site_php, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW",self.hide)
        self.root.bind("<Unmap>",self.unmap)
        self.root.after(500,self.refresh)
        self.root.after(1000,self.refresh_logs)
        self.root.after(1200, self._reconcile_web_servers)
        signal.signal(signal.SIGINT, lambda s,f: self.exit())
        signal.signal(signal.SIGTERM, lambda s,f: self.exit())

    def _reconcile_web_servers(self):
        if self.closing:
            return
        try:
            if web_server_running("apache") and web_server_running("nginx"):
                self.log("Both Apache and Nginx detected; stopping Nginx to keep only one web server active.")
                self.svc.stop_nginx()
        except Exception as e:
            self.log("Web server reconciliation error: " + str(e))

    def _install_global_wheel(self):
        """Route mouse-wheel input to the active scrollable page.

        The handler is intentionally application-wide.  If the pointer is over a
        native text/tree widget, its own class binding is allowed to handle the
        wheel.  Otherwise the visible page canvas receives the scroll event.
        """
        def _native_scroll_widget(widget):
            try:
                w = widget
                while w is not None and w is not self.root:
                    if isinstance(w, (tk.Text, ttk.Treeview, tk.Listbox)):
                        return True
                    w = w.master
            except Exception:
                pass
            return False

        def _wheel(event):
            if self.closing:
                return
            try:
                under = self.root.winfo_containing(event.x_root, event.y_root)
            except Exception:
                under = None

            # Let Text/Treeview/Listbox widgets keep their native scrolling.
            if under is not None and _native_scroll_widget(under):
                return

            canvas = None
            # The visible scrollable canvas is the active page.  Hidden notebook
            # pages are not mapped and therefore are ignored automatically.
            for candidate in reversed(getattr(self, "_scroll_canvases", [])):
                try:
                    if candidate.winfo_exists() and candidate.winfo_viewable():
                        canvas = candidate
                        break
                except Exception:
                    continue
            if canvas is None:
                return

            try:
                if getattr(event, "delta", 0):
                    units = -1 if event.delta > 0 else 1
                    # Windows wheel messages are commonly multiples of 120.
                    count = max(1, abs(int(event.delta)) // 120)
                    canvas.yview_scroll(units * count, "units")
                elif getattr(event, "num", 0) == 4:
                    canvas.yview_scroll(-1, "units")
                elif getattr(event, "num", 0) == 5:
                    canvas.yview_scroll(1, "units")
                return "break"
            except Exception:
                return

        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self.root.bind_all(seq, _wheel, add="+")
            except Exception:
                pass

    def _page_header(self, parent, title, subtitle, icon="▦"):
        """Standard page header shared by every top-level workspace section."""
        head = tk.Frame(parent, bg=THEME["bg"])
        head.pack(fill="x", padx=16, pady=(14, 8))

        icon_box = tk.Frame(head, bg=THEME["accent"], width=40, height=40)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        tk.Label(icon_box, text=icon, bg=THEME["accent"], fg=THEME["white"],
                 font=("Segoe UI Symbol", 18, "bold")).pack(expand=True)

        copy = tk.Frame(head, bg=THEME["bg"])
        copy.pack(side="left", padx=11)
        tk.Label(copy, text=title, bg=THEME["bg"], fg=THEME["text"],
                 font=(THEME["font_family"], 16, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(copy, text=subtitle, bg=THEME["bg"], fg=THEME["text_dim"],
                     font=(THEME["font_family"], 8)).pack(anchor="w", pady=(2, 0))
        return head

    def _page_body(self, parent):
        """Card-like body shell used behind non-settings pages."""
        shell = tk.Frame(parent, bg=THEME["bg_card"],
                         highlightbackground=THEME["border"], highlightthickness=1)
        shell.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return shell

    def _header(self, parent):
        hdr = tk.Frame(parent, bg=THEME["bg"])
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg=THEME["bg"])
        inner.pack(fill="x", padx=24, pady=(18, 14))

        brand = tk.Frame(inner, bg=THEME["bg"])
        brand.pack(side="left")
        self._logo_img = None
        try:
            if LOGO_PNG.exists():
                _li = Image.open(str(LOGO_PNG))
                _li.thumbnail((210, 52), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(_li)
        except Exception:
            self._logo_img = None
        if self._logo_img is not None:
            tk.Label(brand, image=self._logo_img, bg=THEME["bg"]).pack(side="left", padx=(0, 12))
        else:
            mark = tk.Frame(brand, bg=THEME["accent"], width=42, height=42)
            mark.pack(side="left", padx=(0, 12))
            mark.pack_propagate(False)
            tk.Label(mark, text="F", bg=THEME["accent"], fg=THEME["white"],
                     font=(THEME["font_family"], 18, "bold")).pack(expand=True)
        title_box = tk.Frame(brand, bg=THEME["bg"])
        title_box.pack(side="left")
        tk.Label(title_box, text=APP_NAME, bg=THEME["bg"], fg=THEME["text"],
                 font=(THEME["font_family"], 19, "bold")).pack(anchor="w")
        self._subtitle = tk.Label(title_box, text=lang.t("app_subtitle"), bg=THEME["bg"],
                                   fg=THEME["text_dim"], font=(THEME["font_family"], 9))
        self._subtitle.pack(anchor="w", pady=(1,0))

        controls = tk.Frame(inner, bg=THEME["bg"])
        controls.pack(side="right")
        self._lang_buttons = {}
        for code, info in LANGUAGES.items():
            btn = tk.Label(controls, text=info["flag"], bg=THEME["bg_card"], fg=THEME["text"],
                           font=(THEME["font_family"], 11), padx=6, pady=4, cursor="hand2",
                           highlightbackground=THEME["accent"] if code == lang.get() else THEME["border"],
                           highlightthickness=1 if code == lang.get() else 0)
            btn.pack(side="left", padx=2)
            ToolTip(btn, info["name"])
            btn.bind("<Button-1>", lambda e, c=code: self._switch_lang(c))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=THEME["bg_elevated"]))
            btn.bind("<Leave>", lambda e, b=btn, c=code: b.configure(bg=THEME["bg_card"],
                highlightbackground=THEME["accent"] if c == lang.get() else THEME["border"],
                highlightthickness=1 if c == lang.get() else 0))
            self._lang_buttons[code] = btn

        _start_all_btn = IconButton(controls, "play", self.start_all,
            color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"],
            size=34, tip=lang.t("start_all") + " — " + lang.t("tip_start_all"))
        _start_all_btn.pack(side="right", padx=(10,0))
        _stop_all_btn = IconButton(controls, "stop", self.stop_all,
            color=THEME["danger"], hover_color="#ff6b5a", active_color=THEME["danger_dim"],
            size=34, tip=lang.t("stop_all") + " — " + lang.t("tip_stop_all"))
        _stop_all_btn.pack(side="right", padx=4)
        _restart_all_btn = IconButton(controls, "restart", self.restart_all, color=THEME["warning_dim"],
            hover_color=THEME["warning"], active_color="#ba5e17", size=34,
            tip=lang.t("restart_all") + " — " + lang.t("tip_restart_all"))
        _restart_all_btn.pack(side="right", padx=4)
        _help_btn = IconButton(controls, "help", self._show_help, color=THEME["accent"],
            hover_color=THEME["accent_hover"], active_color=THEME["accent_active"], size=34,
            tip=lang.t("help_btn") + " — " + lang.t("tip_help"))
        _help_btn.pack(side="right", padx=4)
        _donate_btn = IconButton(controls, "heart", self._show_donate, color="#e17055",
            hover_color="#f0816e", active_color="#c0392b", size=34,
            tip=lang.t("btn_donate") + " — " + lang.t("donate_title"))
        _donate_btn.pack(side="right", padx=4)

        self._port_strip = tk.Frame(parent, bg=THEME["bg_card"])
        self._port_strip.pack(fill="x")
        tk.Label(self._port_strip, text="LOCAL SERVICES   •  ", bg=THEME["bg_card"],
                 fg=THEME["text_muted"], font=("Cascadia Code", 8, "bold")).pack(side="left", padx=(24, 0), pady=7)
        self._port_labels = {}
        for key, cfgkey, attr in (("Apache", "apache_port", "apache"),
                                  ("MariaDB", "mariadb_port", "db"),
                                  ("PHP", "php_cgi_port", "php"),
                                  ("PostgreSQL", "postgresql_port", "pg"),
                                  ("Redis", "redis_port", "redis"),
                                  ("Nginx", "nginx_port", "nginx")):
            lbl = tk.Label(self._port_strip, text=f"{key} {CONFIG[cfgkey]}", bg=THEME["bg_card"],
                           fg=THEME["text_dim"], font=("Cascadia Code", 8))
            lbl.pack(side="left", pady=7)
            self._port_labels[attr] = (lbl, key, cfgkey)
            tk.Label(self._port_strip, text="   ·   ", bg=THEME["bg_card"],
                     fg=THEME["text_muted"], font=("Cascadia Code", 8)).pack(side="left", pady=7)
        self._refresh_port_label()


    def _switch_lang(self, code):
        lang.set(code)
        for c, btn in self._lang_buttons.items():
            btn.configure(
                highlightbackground=THEME["accent"] if c == code else THEME["border"],
                highlightthickness=1 if c == code else 0)
        self._rebuild_ui()

    def _rebuild_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.build()

    def _service_card(self, parent, name_key, icon_text, attr, start_cmd, stop_cmd, restart_cmd=None):
        card = tk.Frame(parent, bg=THEME["bg_card"], highlightbackground=THEME["border"],
                        highlightthickness=1, padx=0, pady=0)
        card.grid(row=getattr(self, "_service_row", 0), column=getattr(self, "_service_col", 0),
                  sticky="nsew", padx=6, pady=6)
        self._service_col = getattr(self, "_service_col", 0) + 1
        if self._service_col >= 2:
            self._service_col = 0; self._service_row = getattr(self, "_service_row", 0) + 1

        inner = tk.Frame(card, bg=THEME["bg_card"])
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        top = tk.Frame(inner, bg=THEME["bg_card"]); top.pack(fill="x")
        icon_box = tk.Frame(top, bg=THEME["bg_elevated"], width=36, height=36,
                            highlightbackground=THEME["border"], highlightthickness=1)
        icon_box.pack(side="left", padx=(0,10)); icon_box.pack_propagate(False)
        tk.Label(icon_box, text=icon_text, bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=("Segoe UI Emoji", 14)).pack(expand=True)
        name_box = tk.Frame(top, bg=THEME["bg_card"]); name_box.pack(side="left", fill="x", expand=True)
        tk.Label(name_box, text=lang.t(name_key), bg=THEME["bg_card"], fg=THEME["text"],
                 font=(THEME["font_family"], 10, "bold")).pack(anchor="w")
        port_map = {"apache":"apache_port","db":"mariadb_port","php":"php_cgi_port",
                    "pg":"postgresql_port","redis":"redis_port","nginx":"nginx_port"}
        port_text = f"PORT {CONFIG[port_map[attr]]}" if attr in port_map else "LOCAL SERVICE"
        tk.Label(name_box, text=port_text, bg=THEME["bg_card"], fg=THEME["text_muted"],
                 font=("Cascadia Code", 7, "bold")).pack(anchor="w", pady=(2,0))
        status_lbl = tk.Label(top, text=lang.t("stopped"), bg=THEME["danger"], fg=THEME["white"],
                              font=(THEME["font_family"], 7, "bold"), padx=8, pady=3)
        status_lbl.pack(side="right", anchor="n")
        setattr(self, attr + "_status", status_lbl)

        actions = tk.Frame(inner, bg=THEME["bg_card"]); actions.pack(fill="x", pady=(12,0))
        toggle_btn = IconButton(actions, "play", lambda a=attr: self._toggle_svc(a),
            color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"],
            size=30, tip=lang.t("start") + " / " + lang.t("stop") + " — " + lang.t("tip_start"))
        toggle_btn.pack(side="left")
        setattr(self, attr + "_toggle", toggle_btn)
        if restart_cmd:
            restart_btn = IconButton(actions, "restart", restart_cmd, color=THEME["warning_dim"],
                hover_color=THEME["warning"], active_color="#ba5e17", size=30,
                tip=lang.t("restart") + " — " + lang.t("tip_restart"))
            restart_btn.pack(side="left", padx=5); setattr(self, attr + "_restart", restart_btn)


    def _action_bar(self, parent):
        shell = tk.Frame(parent, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        shell.pack(fill="x", padx=12, pady=(10,14))
        title = tk.Frame(shell, bg=THEME["bg_card"]); title.pack(fill="x", padx=12, pady=(10, 2))
        glyph = tk.Frame(title, bg=THEME["bg_elevated"], width=28, height=28,
                         highlightbackground=THEME["border"], highlightthickness=1)
        glyph.pack(side="left"); glyph.pack_propagate(False)
        tk.Label(glyph, text="⚡", bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=("Segoe UI Emoji", 12)).pack(expand=True)
        tk.Label(title, text=lang.t("quick_actions"), bg=THEME["bg_card"], fg=THEME["text"],
                 font=(THEME["font_family"], 10, "bold")).pack(side="left", padx=9)
        left = tk.Frame(shell, bg=THEME["bg_card"]); left.pack(side="left", padx=10, pady=9)
        for kind, cmd, color, hover, active, tip in [
            ("globe", self.localhost, THEME["accent"], THEME["accent_hover"],
             THEME["accent_active"], lang.t("open_localhost") + " — " + lang.t("tip_localhost")),
            ("cylinder", self.pma, "#1f6feb", "#4b9bff",
             "#1a5fd0", "phpMyAdmin — " + lang.t("tip_pma")),
            ("folder", lambda: os.startfile(str(WWW)), THEME["bg_input"], THEME["border_light"],
             THEME["border"], lang.t("open_www") + " — " + lang.t("tip_www")),
            ("lock", self.setup_ssl_cmd, THEME["warning_dim"], THEME["warning"],
             "#ba5e17", lang.t("setup_ssl") + " — " + lang.t("tip_ssl")),
            ("play", self.run_script_cmd, THEME["success"], "#55e39a",
             THEME["success_dim"], lang.t("run_script") + " — " + lang.t("tip_script"))]:
            _ab = IconButton(left, kind, cmd, color=color, hover_color=hover,
                             active_color=active, size=32, tip=tip)
            _ab.pack(side="left", padx=2)
        right = tk.Frame(shell, bg=THEME["bg_card"]); right.pack(side="right", padx=10, pady=9)
        self._progress_label = tk.Label(right, text="", bg=THEME["bg_card"], fg=THEME["text_dim"],
                                         font=("Cascadia Code", 7)); self._progress_label.pack(side="right", padx=5)
        self._progress_bar = ttk.Progressbar(right, mode="determinate", length=130, style="Modern.Horizontal.TProgressbar")
        self._progress_bar.pack(side="right", padx=5)
        _clear_btn = IconButton(right, "trash", self.clear, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"], size=32,
                     tip=lang.t("clear_logs") + " — " + lang.t("tip_clear"))
        _clear_btn.pack(side="right", padx=2)


    def _log_tabs(self, parent):
        self._page_header(parent, lang.t("tab_logs"),
                          PAGE_SUBTITLES["logs"].get(lang.get(), PAGE_SUBTITLES["logs"]["en"]), "≡")
        page = self._page_body(parent)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TNotebook", background=THEME["bg"], borderwidth=0,
                        tabmargins=[8, 4, 8, 0])
        style.configure("Dark.TNotebook.Tab",
                        background=THEME["bg_card"], foreground=THEME["text_dim"],
                        padding=[18, 8], font=(THEME["font_family"], 10),
                        borderwidth=0, focuscolor=THEME["bg"])
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", THEME["bg_elevated"]),
                              ("active", THEME["bg_input"])],
                  foreground=[("selected", THEME["accent"]),
                              ("active", THEME["text"])],
                  expand=[("selected", [0, 0, 0, 2])])
        style.configure("Big.Treeview", background=THEME["bg_elevated"],
                        fieldbackground=THEME["bg_elevated"], foreground=THEME["text"],
                        font=(THEME["font_family"], 11), rowheight=36, borderwidth=0)
        style.map("Big.Treeview", background=[("selected", THEME["accent"])],
                  foreground=[("selected", THEME["white"])])
        style.configure("Big.Treeview.Heading", background=THEME["bg_card"],
                        foreground=THEME["text"], font=(THEME["font_family"], 10, "bold"),
                        relief="flat")
        style.map("Big.Treeview.Heading", background=[("active", THEME["bg_input"])])
        style.configure("Dark.TNotebook", borderwidth=0)
        style.layout("Dark.TNotebook.Tab",
                     [("Notebook.tab",
                       {"sticky": "nswe",
                        "children": [("Notebook.padding",
                                       {"side": "top", "sticky": "nswe",
                                        "children": [("Notebook.label", {"sticky": "nswe"})]})]})])

        nb = OfficeTabs(page, active_size=11, passive_size=9)
        self._extra_nb = nb
        self.views = {}
        self._view_cache = {}
        self._log_stat = {}

        tabs = [
            ("system", lang.t("tab_system"), None),
            ("apache_err", lang.t("tab_apache_err"), LOGS / "apache-error.log"),
            ("php_err", lang.t("tab_php_err"), LOGS / "php-error.log"),
            ("mariadb_err", lang.t("tab_mariadb_err"), LOGS / "mariadb-error.log"),
            ("pg_log", "PostgreSQL", LOGS / "postgresql-process.log"),
            ("redis_log", "Redis", LOGS / "redis-process.log"),
            ("node_log", lang.t("tab_node"), LOGS / "node-process.log"),
            ("nginx_log", "Nginx", LOGS / "nginx-error.log"),
            ("py_log", "Python", LOGS / "python-process.log"),
            ("proc", lang.t("tab_process"), None),
        ]

        self._log_level_var = tk.StringVar(value="ALL")
        self._log_search_var = tk.StringVar(value="")
        for vid, title, path in tabs:
            frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
            nb.add(frame, title)

            if vid == "system":
                fbar = tk.Frame(frame, bg=THEME["bg_elevated"])
                fbar.pack(fill="x", padx=10, pady=(5, 0))
                tk.Label(fbar, text=lang.t("log_level"), bg=THEME["bg_elevated"], fg=THEME["text"],
                         font=(THEME["font_family"], 9)).pack(side="left")
                lvl = tk.OptionMenu(fbar, self._log_level_var, "ALL", "ERROR", "WARNING", "INFO")
                lvl.configure(bg=THEME["entry_bg"], fg=THEME["entry_fg"], relief="flat",
                              activebackground=THEME["accent"], activeforeground=THEME["white"],
                              font=(THEME["font_family"], 9), highlightthickness=0)
                lvl["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
                lvl.pack(side="left", padx=4)
                tk.Label(fbar, text=lang.t("log_find"), bg=THEME["bg_elevated"], fg=THEME["text"],
                         font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
                tk.Entry(fbar, textvariable=self._log_search_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                         insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                         relief="flat", bd=0, width=24).pack(side="left", padx=4)

            t = ScrolledText(frame, wrap="word", bg="#0d0f16", fg="#b8bdd0",
                             insertbackground="white", font=("Cascadia Code", 9),
                             relief="flat", bd=0, padx=10, pady=6,
                             selectbackground=THEME["accent"], selectforeground=THEME["white"])
            t.pack(fill="both", expand=True, padx=0, pady=0)
            t.bind("<Key>", lambda e: "break")
            t.bind("<Control-c>", self.copy_sel)
            self.context(t)
            self.views[vid] = (t, path)
            self._view_cache[vid] = None

    def _scrollable(self, parent, bg=None):
        bg = bg or THEME["bg_elevated"]
        host = tk.Frame(parent, bg=bg)
        host.pack(fill="both", expand=True)

        canvas = tk.Canvas(host, bg=bg, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=bg)
        wid = canvas.create_window((0, 0), window=body, anchor="nw")

        # Register the canvas once.  The global wheel handler selects whichever
        # registered canvas is currently visible.
        self._scroll_canvases.append(canvas)

        def _fit(e=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfig(wid, width=max(1, canvas.winfo_width()))
                need = body.winfo_reqheight() > canvas.winfo_height() + 2
                if need:
                    if not vsb.winfo_ismapped():
                        vsb.pack(side="right", fill="y")
                else:
                    if vsb.winfo_ismapped():
                        vsb.pack_forget()
                    canvas.yview_moveto(0.0)
            except Exception:
                pass

        body.bind("<Configure>", _fit)
        canvas.bind("<Configure>", _fit)
        return body

    def _data_tabs(self, parent):
        self._page_header(parent, lang.t("tab_db"),
                          PAGE_SUBTITLES["db"].get(lang.get(), PAGE_SUBTITLES["db"]["en"]), "▦")
        page = self._page_body(parent)
        nb = OfficeTabs(page, active_size=11, passive_size=9)
        sql_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(sql_frame, lang.t('tab_sql'))
        self._build_sql_editor(sql_frame)

        db_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(db_frame, lang.t('tab_db'))
        self._build_db(self._scrollable(db_frame))

        dbm_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(dbm_frame, lang.t('tab_dbmanager'))
        self._build_dbmanager(self._scrollable(dbm_frame))

    def _projects_tabs(self, parent):
        self._page_header(parent, lang.t("tab_projects"),
                          PAGE_SUBTITLES["projects"].get(lang.get(), PAGE_SUBTITLES["projects"]["en"]), "□")
        page = self._page_body(parent)
        nb = OfficeTabs(page, active_size=11, passive_size=9)
        files_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(files_frame, lang.t('tab_files'))
        self._build_file_manager(files_frame)

        sites_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(sites_frame, lang.t('tab_sites'))
        self._build_sites_manager(sites_frame)

        tasks_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(tasks_frame, lang.t('tab_tasks'))
        self._build_task_scheduler(tasks_frame)

        node_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(node_frame, lang.t('tab_node'))
        self._build_node(self._scrollable(node_frame))

        phpini_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(phpini_frame, lang.t('tab_phpini'))
        self._build_phpini(self._scrollable(phpini_frame))

    def _monitor_tabs(self, parent):
        self._page_header(parent, lang.t("tab_monitor"),
                          PAGE_SUBTITLES["monitor"].get(lang.get(), PAGE_SUBTITLES["monitor"]["en"]), "⌁")
        page = self._page_body(parent)
        nb = OfficeTabs(page, active_size=11, passive_size=9)
        docker_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(docker_frame, lang.t('tab_docker'))
        self._build_docker(self._scrollable(docker_frame))

        procs_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(procs_frame, lang.t('tab_procs'))
        self._build_procs(procs_frame)

        perf_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(perf_frame, lang.t('tab_perf'))
        self._build_perf(self._scrollable(perf_frame))

    def _build_phpini(self, parent):
        try:
            values, _en0, _ln = self.svc.php_ini_parse()
            avail, enabled = self.svc.php_ini_extensions()
        except RuntimeError as e:
            tk.Label(parent, text=str(e), bg=THEME["bg_elevated"], fg=THEME["danger"],
                     font=(THEME["font_family"], 10)).pack(padx=12, pady=12, anchor="w")
            return
        self._phpini_vars = {}
        self._phpini_ext_vars = {}
        self._phpini_rows = []
        self._phpini_after = None
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        tk.Label(top, text=lang.t("phpini_search"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        self._phpini_search = tk.StringVar(value="")
        se = tk.Entry(top, textvariable=self._phpini_search, bg=THEME["entry_bg"],
                      fg=THEME["entry_fg"], insertbackground=THEME["entry_fg"],
                      font=("Cascadia Code", 9), relief="flat", bd=0, width=24)
        se.pack(side="left", padx=4)
        se.bind("<KeyRelease>", lambda e: self._phpini_filter())
        IconButton(top, "check", self._phpini_save_manual, color=THEME["success"],
                   hover_color="#55e39a", active_color=THEME["success_dim"],
                   size=28, tip=lang.t("phpini_save")).pack(side="left", padx=6)
        IconButton(top, "restart", self._phpini_restart, color=THEME["warning_dim"],
                   hover_color=THEME["warning"], active_color="#ba5e17",
                   size=28, tip=lang.t("phpini_restart")).pack(side="left", padx=2)
        self._phpini_status = tk.Label(top, text="", bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                                       font=(THEME["font_family"], 8))
        self._phpini_status.pack(side="left", padx=10)

        dbox = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        dbox.pack(fill="x", padx=10, pady=4)
        tk.Label(dbox, text=lang.t("phpini_directives"), bg=THEME["bg_elevated"],
                 fg=THEME["accent"], font=(THEME["font_family"], 10, "bold")).pack(
                     anchor="w", padx=10, pady=(8, 2))
        dg = tk.Frame(dbox, bg=THEME["bg_elevated"])
        dg.pack(fill="x", padx=10, pady=(0, 8))
        for key, kind in self.svc.PHP_INI_MANAGED:
            row = tk.Frame(dg, bg=THEME["bg_elevated"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=key, bg=THEME["bg_elevated"], fg=THEME["text"],
                     font=("Cascadia Code", 9), width=28, anchor="w").pack(side="left")
            cur = values.get(key.lower(), "")
            if kind == "bool":
                var = tk.BooleanVar(value=cur.lower() in ("1", "on", "true", "yes"))
                tk.Checkbutton(row, variable=var, bg=THEME["bg_elevated"],
                               selectcolor=THEME["entry_bg"],
                               activebackground=THEME["bg_elevated"],
                               highlightthickness=0, bd=0).pack(side="left")
                st = tk.StringVar(value="On" if var.get() else "Off")
                st_lbl = tk.Label(row, textvariable=st, bg=THEME["bg_elevated"],
                                  fg=THEME["success"] if var.get() else THEME["text_muted"],
                                  font=("Cascadia Code", 9), width=4, anchor="w")
                st_lbl.pack(side="left", padx=2)

                def _upd(*a, _v=var, _s=st, _l=st_lbl):
                    on = bool(_v.get())
                    _s.set("On" if on else "Off")
                    _l.configure(fg=THEME["success"] if on else THEME["text_muted"])
                    self._phpini_schedule()
                var.trace_add("write", _upd)
            else:
                var = tk.StringVar(value=cur)
                e = tk.Entry(row, textvariable=var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                             insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                             relief="flat", bd=0, width=30, highlightthickness=1,
                             highlightbackground=THEME["border"], highlightcolor=THEME["accent"])
                e.pack(side="left", fill="x", expand=True)
                var.trace_add("write", lambda *a: self._phpini_schedule())
            self._phpini_vars[key.lower()] = (kind, var)
            self._phpini_rows.append((key.lower(), key, row))

        ebox = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        ebox.pack(fill="x", padx=10, pady=4)
        tk.Label(ebox, text=lang.t("phpini_ext"), bg=THEME["bg_elevated"],
                 fg=THEME["accent"], font=(THEME["font_family"], 10, "bold")).pack(
                     anchor="w", padx=10, pady=(8, 2))
        eg = tk.Frame(ebox, bg=THEME["bg_elevated"])
        eg.pack(fill="x", padx=10, pady=(0, 8))
        self._phpini_ext_rows = []
        for idx, dll in enumerate(avail):
            var = tk.BooleanVar(value=dll in enabled)
            cb = tk.Checkbutton(eg, text=dll, variable=var, bg=THEME["bg_elevated"],
                                fg=THEME["text"], selectcolor=THEME["entry_bg"],
                                activebackground=THEME["bg_elevated"],
                                activeforeground=THEME["text"],
                                font=("Cascadia Code", 8),
                                highlightthickness=0, bd=0,
                                command=self._phpini_schedule)
            cb.grid(row=idx // 3, column=idx % 3, sticky="w", padx=8, pady=1)
            self._phpini_ext_vars[dll] = var
            self._phpini_ext_rows.append((dll, cb))

    def _phpini_filter(self):
        q = self._phpini_search.get().strip().lower()
        for _key, _label, row in getattr(self, "_phpini_rows", []):
            if q and q not in _key:
                row.pack_forget()
            else:
                row.pack(fill="x", pady=1)
        for dll, cb in getattr(self, "_phpini_ext_rows", []):
            if q and q not in dll:
                cb.grid_remove()
            else:
                cb.grid()

    def _phpini_collect(self):
        values = {}
        for key, (kind, var) in self._phpini_vars.items():
            values[key] = "On" if (kind == "bool" and var.get()) else (
                var.get() if kind != "bool" else "Off")
        exts = {dll for dll, var in self._phpini_ext_vars.items() if var.get()}
        return values, exts

    def _phpini_schedule(self):
        try:
            if self._phpini_after is not None:
                self.root.after_cancel(self._phpini_after)
        except Exception:
            pass
        try:
            self._phpini_after = self.root.after(800, self._phpini_autosave)
        except Exception:
            pass

    def _phpini_autosave(self):
        self._phpini_after = None
        try:
            values, exts = self._phpini_collect()
            self.svc.php_ini_save(values, exts)
            self._phpini_status.configure(
                text=time.strftime("%H:%M:%S") + " ✓")
        except Exception as e:
            self._phpini_status.configure(text=str(e)[:120])

    def _phpini_save_manual(self):
        try:
            if self._phpini_after is not None:
                self.root.after_cancel(self._phpini_after)
                self._phpini_after = None
        except Exception:
            pass
        try:
            values, exts = self._phpini_collect()
            self.svc.php_ini_save(values, exts)
            self.log("php.ini saved")
            self._phpini_status.configure(text=time.strftime("%H:%M:%S") + " ✓")
        except Exception as e:
            messagebox.showerror(lang.t("error"), str(e))

    def _phpini_restart(self):
        def w():
            try:
                if self.svc.prun():
                    self.svc.stop_php()
                self.svc.start_php()
            except Exception as e:
                self.log("PHP restart ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _build_node(self, parent):
        self._node_file = APP_ROOT / "config" / "node.json"
        try:
            self._node_defs = json.loads(self._node_file.read_text(encoding="utf-8")).get("servers", [])
        except Exception:
            self._node_defs = []
        form = tk.Frame(parent, bg=THEME["bg_elevated"])
        form.pack(fill="x", padx=10, pady=5)
        self._node_name_var = tk.StringVar(value="myapp")
        self._node_dir_var = tk.StringVar(value=str(WWW / "myapp"))
        self._node_entry_var = tk.StringVar(value="server.js")
        self._node_port_var = tk.StringVar(value="3000")
        r1 = tk.Frame(form, bg=THEME["bg_elevated"])
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text=lang.t("col_server"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        tk.Entry(r1, textvariable=self._node_name_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=16).pack(side="left", padx=4)
        tk.Label(r1, text=lang.t("node_project"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        tk.Entry(r1, textvariable=self._node_dir_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True, padx=4)
        IconButton(r1, "folder", self._node_browse_dir, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("first_run_browse") + " — " + lang.t("tip_browse")).pack(side="left", padx=2)
        r2 = tk.Frame(form, bg=THEME["bg_elevated"])
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text=lang.t("node_entry"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        tk.Entry(r2, textvariable=self._node_entry_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=24).pack(side="left", padx=4)
        tk.Label(r2, text=lang.t("node_port"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        tk.Entry(r2, textvariable=self._node_port_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=6).pack(side="left", padx=4)
        self._node_ver = tk.Label(r2, text="Node.js: …", bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                                  font=("Cascadia Code", 9))
        self._node_ver.pack(side="left", padx=12)
        btns = tk.Frame(parent, bg=THEME["bg_elevated"])
        btns.pack(fill="x", padx=10, pady=4)
        IconButton(btns, "play", self._node_start_sel, color=THEME["success"],
                     hover_color="#55e39a", active_color=THEME["success_dim"],
                     size=30, tip=lang.t("start") + " — " + lang.t("tip_run")).pack(side="left", padx=2)
        IconButton(btns, "stop", self._node_stop_sel, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("stop") + " — " + lang.t("tip_start")).pack(side="left", padx=2)
        IconButton(btns, "restart", self._node_restart_sel, color=THEME["warning_dim"],
                     hover_color=THEME["warning"], active_color="#ba5e17",
                     size=30, tip=lang.t("restart") + " — " + lang.t("tip_restart")).pack(side="left", padx=2)
        IconButton(btns, "globe", self._node_open_sel, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     size=30, tip=lang.t("btn_open_site") + " — " + lang.t("tip_open")).pack(side="left", padx=2)
        IconButton(btns, "cross", self._node_remove_sel, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        cols = ("server", "port", "pid", "started", "status")
        self._node_tree = ttk.Treeview(parent, columns=cols, show="headings", height=8,
                                       style="Big.Treeview")
        self._node_tree.heading("server", text=lang.t("col_server"))
        self._node_tree.heading("port", text=lang.t("col_port"))
        self._node_tree.heading("pid", text=lang.t("col_pid"))
        self._node_tree.heading("started", text=lang.t("col_started"))
        self._node_tree.heading("status", text=lang.t("col_status"))
        self._node_tree.column("server", width=140)
        self._node_tree.column("port", width=70)
        self._node_tree.column("pid", width=80)
        self._node_tree.column("started", width=130)
        self._node_tree.column("status", width=110)
        self._node_tree.pack(fill="both", expand=True, padx=10, pady=4)
        self._node_refresh_tree()
        threading.Thread(target=self._node_version, daemon=True).start()
        self._build_py(parent)

    def _node_save_defs(self):
        try:
            (APP_ROOT / "config").mkdir(parents=True, exist_ok=True)
            self._node_file.write_text(json.dumps({"servers": self._node_defs}, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _node_current_def(self):
        return {"name": self._node_name_var.get().strip() or "myapp",
                "dir": self._node_dir_var.get().strip(),
                "entry": self._node_entry_var.get().strip() or "server.js",
                "port": self._node_port_var.get().strip() or "3000"}

    def _node_upsert_def(self, d):
        self._node_defs = [s for s in self._node_defs if s.get("name") != d["name"]]
        self._node_defs.append(d)
        self._node_save_defs()

    def _node_refresh_tree(self):
        if not hasattr(self, "_node_tree"):
            return
        for item in self._node_tree.get_children():
            self._node_tree.delete(item)
        live = {}
        for name, info in self.svc.node_servers.items():
            try:
                alive = info["proc"].poll() is None
            except Exception:
                alive = False
            live[name] = (info, alive)
        for d in self._node_defs:
            name = d.get("name", "")
            if name in live:
                info, alive = live[name]
                pid = info["proc"].pid if alive else "—"
                self._node_tree.insert("", "end", iid=name,
                                       values=(name, info["port"], pid, info["started"],
                                               lang.t("running") if alive else lang.t("stopped")))
        for name, (info, alive) in live.items():
            if name not in [d.get("name") for d in self._node_defs]:
                self._node_tree.insert("", "end", iid=name,
                                       values=(name, info["port"], info["proc"].pid, info["started"],
                                               lang.t("running")))

    def _node_version(self):
        try:
            exe = self.svc.get_node_exe()
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            ver = r.stdout.strip() or "?"
            self.root.after(0, lambda: self._node_ver.configure(text=f"Node.js: {ver}"))
        except Exception as e:
            self.root.after(0, lambda: self._node_ver.configure(text=f"Node.js: {e}"[:80]))

    def _node_browse_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(initialdir=self._node_dir_var.get() or str(WWW))
        if d:
            self._node_dir_var.set(d)

    def _node_start_sel(self):
        sel = list(self._node_tree.selection())
        if sel:
            d = next((s for s in self._node_defs if s.get("name") == sel[0]), None)
            if d:
                self._node_name_var.set(d["name"])
                self._node_dir_var.set(d.get("dir", ""))
                self._node_entry_var.set(d.get("entry", "server.js"))
                self._node_port_var.set(str(d.get("port", "3000")))
        d = self._node_current_def()
        if not Path(d["dir"]).is_dir():
            messagebox.showerror(lang.t("error"), d["dir"])
            return
        def w():
            try:
                self.svc.node_server_start(d["name"], d["dir"], d["entry"], d["port"])
                self._node_upsert_def(d)
                self.root.after(0, self._node_refresh_tree)
            except Exception as e:
                self.log(f"Node.js ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _node_stop_sel(self):
        sel = list(self._node_tree.selection())
        names = sel or ([self._node_name_var.get().strip()] if self._node_name_var.get().strip() else [])
        def w():
            for name in names:
                try:
                    self.svc.node_server_stop(name)
                except Exception as e:
                    self.log(f"Node.js ERROR: {e}")
            self.root.after(0, self._node_refresh_tree)
        threading.Thread(target=w, daemon=True).start()

    def _node_restart_sel(self):
        sel = list(self._node_tree.selection())
        if sel:
            d = next((s for s in self._node_defs if s.get("name") == sel[0]), None)
            if d:
                self._node_name_var.set(d["name"])
                self._node_dir_var.set(d.get("dir", ""))
                self._node_entry_var.set(d.get("entry", "server.js"))
                self._node_port_var.set(str(d.get("port", "3000")))
        d = self._node_current_def()
        def w():
            try:
                self.svc.node_server_stop(d["name"], quiet=True)
                self.svc.node_server_start(d["name"], d["dir"], d["entry"], d["port"])
                self._node_upsert_def(d)
                self.root.after(0, self._node_refresh_tree)
            except Exception as e:
                self.log(f"Node.js ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _node_remove_sel(self):
        sel = list(self._node_tree.selection())
        if not sel:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        if not DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"),
                                     f"{lang.t('confirm_delete')} {sel[0]}?"):
            return
        def w():
            try:
                self.svc.node_server_stop(sel[0], quiet=True)
            except Exception:
                pass
            self._node_defs = [s for s in self._node_defs if s.get("name") != sel[0]]
            self._node_save_defs()
            self.root.after(0, self._node_refresh_tree)
        threading.Thread(target=w, daemon=True).start()

    def _node_open_sel(self):
        sel = list(self._node_tree.selection())
        port = None
        if sel:
            d = next((s for s in self._node_defs if s.get("name") == sel[0]), None)
            if d:
                port = d.get("port")
            info = self.svc.node_servers.get(sel[0])
            if info:
                port = info["port"]
        port = port or self._node_port_var.get().strip() or "3000"
        url = f"http://127.0.0.1:{port}/"
        self.log(f"Opening Node.js app: {url}")
        webbrowser.open(url)

    def _build_py(self, parent):
        self._py_file = APP_ROOT / "config" / "python.json"
        try:
            self._py_defs = json.loads(self._py_file.read_text(encoding="utf-8")).get("servers", [])
        except Exception:
            self._py_defs = []
        title = tk.Label(parent, text="Python", bg=THEME["bg_elevated"], fg=THEME["accent"],
                         font=(THEME["font_family"], 10, "bold"), anchor="w")
        title.pack(fill="x", padx=12, pady=(8, 2))
        form = tk.Frame(parent, bg=THEME["bg_elevated"])
        form.pack(fill="x", padx=10, pady=2)
        self._py_name_var = tk.StringVar(value="pyapp")
        self._py_dir_var = tk.StringVar(value=str(WWW / "pyapp"))
        self._py_entry_var = tk.StringVar(value="app.py")
        self._py_port_var = tk.StringVar(value="5000")
        try:
            _py_vers = list(comps().get("python_versions", {}).keys()) or ["3.11", "3.12", "3.13"]
            _cur = self.svc.env_active()[2]
        except Exception:
            _py_vers, _cur = ["3.11", "3.12", "3.13"], ""
        self._py_ver_var = tk.StringVar(value=_cur if _cur in _py_vers else _py_vers[-1])
        r1 = tk.Frame(form, bg=THEME["bg_elevated"])
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text=lang.t("col_server"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        tk.Entry(r1, textvariable=self._py_name_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=16).pack(side="left", padx=4)
        tk.Label(r1, text=lang.t("node_project"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        tk.Entry(r1, textvariable=self._py_dir_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True, padx=4)
        IconButton(r1, "folder", self._py_browse_dir, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("first_run_browse") + " — " + lang.t("tip_browse")).pack(side="left", padx=2)
        r2 = tk.Frame(form, bg=THEME["bg_elevated"])
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text=lang.t("node_entry"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        tk.Entry(r2, textvariable=self._py_entry_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=24).pack(side="left", padx=4)
        tk.Label(r2, text=lang.t("node_port"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        tk.Entry(r2, textvariable=self._py_port_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=6).pack(side="left", padx=4)
        tk.Label(r2, text="Python:", bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        _pym = tk.OptionMenu(r2, self._py_ver_var, *_py_vers)
        _pym.configure(bg=THEME["entry_bg"], fg=THEME["entry_fg"], relief="flat",
                       activebackground=THEME["accent"], activeforeground=THEME["white"],
                       font=(THEME["font_family"], 9), highlightthickness=0)
        _pym["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
        _pym.pack(side="left", padx=4)
        btns = tk.Frame(parent, bg=THEME["bg_elevated"])
        btns.pack(fill="x", padx=10, pady=2)
        IconButton(btns, "play", self._py_start_sel, color=THEME["success"],
                     hover_color="#55e39a", active_color=THEME["success_dim"],
                     size=30, tip=lang.t("start") + " — " + lang.t("tip_run")).pack(side="left", padx=2)
        IconButton(btns, "stop", self._py_stop_sel, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("stop") + " — " + lang.t("tip_start")).pack(side="left", padx=2)
        IconButton(btns, "restart", self._py_restart_sel, color=THEME["warning_dim"],
                     hover_color=THEME["warning"], active_color="#ba5e17",
                     size=30, tip=lang.t("restart") + " — " + lang.t("tip_restart")).pack(side="left", padx=2)
        IconButton(btns, "globe", self._py_open_sel, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     size=30, tip=lang.t("btn_open_site") + " — " + lang.t("tip_open")).pack(side="left", padx=2)
        IconButton(btns, "cross", self._py_remove_sel, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        self._py_tree = ttk.Treeview(parent, columns=("server", "port", "pid", "started", "status"),
                                     show="headings", height=5, style="Big.Treeview")
        self._py_tree.heading("server", text=lang.t("col_server"))
        self._py_tree.heading("port", text=lang.t("col_port"))
        self._py_tree.heading("pid", text=lang.t("col_pid"))
        self._py_tree.heading("started", text=lang.t("col_started"))
        self._py_tree.heading("status", text=lang.t("col_status"))
        self._py_tree.column("server", width=140)
        self._py_tree.column("port", width=70)
        self._py_tree.column("pid", width=80)
        self._py_tree.column("started", width=130)
        self._py_tree.column("status", width=110)
        self._py_tree.pack(fill="x", padx=10, pady=(2, 6))
        self._py_refresh_tree()

    def _py_save_defs(self):
        try:
            (APP_ROOT / "config").mkdir(parents=True, exist_ok=True)
            self._py_file.write_text(json.dumps({"servers": self._py_defs}, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _py_current_def(self):
        return {"name": self._py_name_var.get().strip() or "pyapp",
                "dir": self._py_dir_var.get().strip(),
                "entry": self._py_entry_var.get().strip() or "app.py",
                "port": self._py_port_var.get().strip() or "5000",
                "pyver": self._py_ver_var.get().strip()}

    def _py_upsert_def(self, d):
        self._py_defs = [s for s in self._py_defs if s.get("name") != d["name"]]
        self._py_defs.append(d)
        self._py_save_defs()

    def _py_refresh_tree(self):
        if not hasattr(self, "_py_tree"):
            return
        for item in self._py_tree.get_children():
            self._py_tree.delete(item)
        live = {}
        for name, info in self.svc.py_servers.items():
            try:
                alive = info["proc"].poll() is None
            except Exception:
                alive = False
            live[name] = (info, alive)
        for d in self._py_defs:
            name = d.get("name", "")
            if name in live:
                info, alive = live[name]
                pid = info["proc"].pid if alive else "—"
                self._py_tree.insert("", "end", iid=name,
                                     values=(name, info["port"], pid, info["started"],
                                             lang.t("running") if alive else lang.t("stopped")))
        for name, (info, alive) in live.items():
            if name not in [d.get("name") for d in self._py_defs]:
                self._py_tree.insert("", "end", iid=name,
                                     values=(name, info["port"], info["proc"].pid, info["started"],
                                             lang.t("running")))

    def _py_browse_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(initialdir=self._py_dir_var.get() or str(WWW))
        if d:
            self._py_dir_var.set(d)

    def _py_fill_from_sel(self):
        sel = list(self._py_tree.selection())
        if not sel:
            return None
        d = next((s for s in self._py_defs if s.get("name") == sel[0]), None)
        if d:
            self._py_name_var.set(d["name"])
            self._py_dir_var.set(d.get("dir", ""))
            self._py_entry_var.set(d.get("entry", "app.py"))
            self._py_port_var.set(str(d.get("port", "5000")))
            if d.get("pyver"):
                self._py_ver_var.set(d["pyver"])
        return d

    def _py_start_sel(self):
        self._py_fill_from_sel()
        d = self._py_current_def()
        if not Path(d["dir"]).is_dir():
            messagebox.showerror(lang.t("error"), d["dir"])
            return
        def w():
            try:
                self.svc.py_server_start(d["name"], d["dir"], d["entry"], d["port"],
                                         d.get("pyver") or None)
                self._py_upsert_def(d)
                self.root.after(0, self._py_refresh_tree)
            except Exception as e:
                self.log(f"Python ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _py_stop_sel(self):
        sel = list(self._py_tree.selection())
        names = sel or ([self._py_name_var.get().strip()] if self._py_name_var.get().strip() else [])
        def w():
            for name in names:
                try:
                    self.svc.py_server_stop(name)
                except Exception as e:
                    self.log(f"Python ERROR: {e}")
            self.root.after(0, self._py_refresh_tree)
        threading.Thread(target=w, daemon=True).start()

    def _py_restart_sel(self):
        self._py_fill_from_sel()
        d = self._py_current_def()
        def w():
            try:
                self.svc.py_server_stop(d["name"], quiet=True)
                self.svc.py_server_start(d["name"], d["dir"], d["entry"], d["port"],
                                         d.get("pyver") or None)
                self._py_upsert_def(d)
                self.root.after(0, self._py_refresh_tree)
            except Exception as e:
                self.log(f"Python ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _py_remove_sel(self):
        sel = list(self._py_tree.selection())
        if not sel:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        if not DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"),
                                     f"{lang.t('confirm_delete')} {sel[0]}?"):
            return
        def w():
            try:
                self.svc.py_server_stop(sel[0], quiet=True)
            except Exception:
                pass
            self._py_defs = [s for s in self._py_defs if s.get("name") != sel[0]]
            self._py_save_defs()
            self.root.after(0, self._py_refresh_tree)
        threading.Thread(target=w, daemon=True).start()

    def _py_open_sel(self):
        sel = list(self._py_tree.selection())
        port = None
        if sel:
            d = next((s for s in self._py_defs if s.get("name") == sel[0]), None)
            if d:
                port = d.get("port")
            info = self.svc.py_servers.get(sel[0])
            if info:
                port = info["port"]
        port = port or self._py_port_var.get().strip() or "5000"
        url = f"http://127.0.0.1:{port}/"
        self.log(f"Opening Python app: {url}")
        webbrowser.open(url)

    def _std_entry(self, parent, var, width=14, show=None):
        e = tk.Entry(parent, textvariable=var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                     insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                     relief="flat", bd=0, width=width, highlightthickness=1,
                     highlightbackground=THEME["border"], highlightcolor=THEME["accent"])
        if show:
            e.configure(show=show)
        return e

    def _build_dbmanager(self, parent):
        conn = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        conn.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(conn, text=lang.t("dbm_conn"), bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=(THEME["font_family"], 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        cg = tk.Frame(conn, bg=THEME["bg_elevated"])
        cg.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(cg, text=lang.t("sql_engine"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).grid(row=0, column=0, sticky="w",
                                                      padx=(0, 4), pady=4)
        self._dbm_engine = tk.StringVar(value="MariaDB")
        eng = tk.OptionMenu(cg, self._dbm_engine, "MariaDB", "PostgreSQL")
        eng.configure(bg=THEME["entry_bg"], fg=THEME["entry_fg"], relief="flat",
                      activebackground=THEME["accent"], activeforeground=THEME["white"],
                      font=(THEME["font_family"], 9), highlightthickness=0)
        eng["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
        eng.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=4)
        tk.Label(cg, text=lang.t("db_user"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).grid(row=0, column=2, sticky="w",
                                                      padx=(0, 4), pady=4)
        self._dbm_user = tk.StringVar(value="root")
        self._std_entry(cg, self._dbm_user, width=10).grid(row=0, column=3, sticky="w",
                                                           padx=(0, 12), pady=4)
        tk.Label(cg, text=lang.t("db_pass"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).grid(row=1, column=0, sticky="w",
                                                      padx=(0, 4), pady=4)
        self._dbm_pass = tk.StringVar(value="")
        self._std_entry(cg, self._dbm_pass, width=10, show="*").grid(row=1, column=1, sticky="w",
                                                                     padx=(0, 12), pady=4)
        tk.Label(cg, text=lang.t("db_name"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).grid(row=1, column=2, sticky="w",
                                                      padx=(0, 4), pady=4)
        self._dbm_db = tk.StringVar(value="")
        self._std_entry(cg, self._dbm_db, width=14).grid(row=1, column=3, sticky="w",
                                                         padx=(0, 12), pady=4)

        acts = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        acts.pack(fill="x", padx=10, pady=4)
        tk.Label(acts, text=lang.t("dbm_actions"), bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=(THEME["font_family"], 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        ag = tk.Frame(acts, bg=THEME["bg_elevated"])
        ag.pack(fill="x", padx=10, pady=(0, 8))
        IconButton(ag, "cylinder", lambda: self._dbm_simple("list"), color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     size=30, tip=lang.t("db_list")).pack(side="left", padx=2)
        IconButton(ag, "plus", lambda: self._dbm_simple("create"), color=THEME["success"],
                     hover_color="#55e39a", active_color=THEME["success_dim"],
                     size=30, tip=lang.t("db_create")).pack(side="left", padx=2)
        IconButton(ag, "cross", lambda: self._dbm_simple("drop"), color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("db_drop")).pack(side="left", padx=2)
        IconButton(ag, "list", lambda: self._dbm_simple("users"), color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("db_users")).pack(side="left", padx=2)
        IconButton(ag, "person", self._dbm_mkuser, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("db_mkuser")).pack(side="left", padx=2)
        IconButton(ag, "down", self._dbm_backup, color=THEME["warning_dim"],
                     hover_color=THEME["warning"], active_color="#ba5e17",
                     size=30, tip=lang.t("db_backup")).pack(side="left", padx=2)
        IconButton(ag, "up", self._dbm_restore, color=THEME["warning_dim"],
                     hover_color=THEME["warning"], active_color="#ba5e17",
                     size=30, tip=lang.t("db_restore")).pack(side="left", padx=2)

        rbox = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        rbox.pack(fill="x", padx=10, pady=4)
        tk.Label(rbox, text="Redis", bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=(THEME["font_family"], 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        rrow = tk.Frame(rbox, bg=THEME["bg_elevated"])
        rrow.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(rrow, text=lang.t("db_pass"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        self._dbm_rpass = tk.StringVar(value="")
        self._std_entry(rrow, self._dbm_rpass, width=16, show="*").pack(side="left", padx=4)
        IconButton(rrow, "trash", self._dbm_flush, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=28, tip=lang.t("db_flush")).pack(side="left", padx=8)

        self._dbm_out = ScrolledText(parent, wrap="word", bg="#0d0f16", fg="#b8bdd0",
                                     insertbackground="white", font=("Cascadia Code", 9),
                                     relief="flat", bd=0, padx=10, pady=6, height=10,
                                     selectbackground=THEME["accent"],
                                     selectforeground=THEME["white"])
        self._dbm_out.pack(fill="both", expand=True, padx=10, pady=4)
        self._dbm_out.configure(state="disabled")
        self._dbm_status = tk.Label(parent, text="", bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                                    font=(THEME["font_family"], 8), anchor="w")
        self._dbm_status.pack(fill="x", padx=12, pady=(0, 6))

    def _dbm_show(self, text):
        def ui():
            self._dbm_out.configure(state="normal")
            self._dbm_out.delete("1.0", "end")
            self._dbm_out.insert("1.0", text)
            self._dbm_out.see("end")
            self._dbm_out.configure(state="disabled")
            self._dbm_status.configure(text="")
        self.root.after(0, ui)

    def _dbm_failed(self, e):
        self.log("DB Manager ERROR: " + str(e))
        self.root.after(0, lambda: self._dbm_status.configure(text=str(e)[:200]))

    def _dbm_creds(self):
        return (self._dbm_engine.get(), self._dbm_user.get().strip(),
                self._dbm_pass.get(), self._dbm_db.get().strip())

    def _dbm_simple(self, what):
        eng, user, pwd, db = self._dbm_creds()
        if what == "drop" and not DarkPrompt.ask_yes_no(
                self.root, lang.t("db_drop"), f"{lang.t('confirm_delete')} {db}?"):
            return
        def w():
            try:
                if what == "list":
                    rows = self.svc.db_list(eng, user, pwd)
                    self._dbm_show("\n".join(rows) or "—")
                elif what == "users":
                    rows = self.svc.db_users(eng, user, pwd)
                    self._dbm_show("\n".join(rows) or "—")
                elif what == "create":
                    self.svc.db_create(eng, user, pwd, db)
                    self._dbm_show(f"OK: {db}")
                elif what == "drop":
                    self.svc.db_drop(eng, user, pwd, db)
                    self._dbm_show(f"OK: {db}")
            except Exception as e:
                self._dbm_failed(e)
        threading.Thread(target=w, daemon=True).start()

    def _dbm_mkuser(self):
        eng, user, pwd, _db = self._dbm_creds()
        new_user = DarkPrompt.ask_string(self.root, lang.t("db_mkuser"), lang.t("db_user"))
        if not new_user:
            return
        new_pass = DarkPrompt.ask_string(self.root, lang.t("db_mkuser"), lang.t("db_pass"))
        if new_pass is None:
            return
        def w():
            try:
                self.svc.db_mkuser(eng, user, pwd, new_user.strip(), new_pass)
                self._dbm_show(f"OK: {new_user}")
            except Exception as e:
                self._dbm_failed(e)
        threading.Thread(target=w, daemon=True).start()

    def _dbm_backup(self):
        eng, user, pwd, db = self._dbm_creds()
        if not db:
            messagebox.showinfo(APP_NAME, lang.t("db_name"))
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".sql",
                                            filetypes=[("SQL dump", "*.sql")],
                                            initialfile=f"{db}.sql")
        if not path:
            return
        def w():
            try:
                self.svc.db_backup(eng, user, pwd, db, path)
                self._dbm_show(f"OK: {path}")
            except Exception as e:
                self._dbm_failed(e)
        threading.Thread(target=w, daemon=True).start()

    def _dbm_restore(self):
        eng, user, pwd, db = self._dbm_creds()
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("SQL dump", "*.sql"), ("All", "*.*")])
        if not path:
            return
        if not DarkPrompt.ask_yes_no(self.root, lang.t("db_restore"),
                                     f"{db or '*'} ← {Path(path).name}?"):
            return
        def w():
            try:
                self.svc.db_restore(eng, user, pwd, db, path)
                self._dbm_show(f"OK: {path}")
            except Exception as e:
                self._dbm_failed(e)
        threading.Thread(target=w, daemon=True).start()

    def _dbm_flush(self):
        if not DarkPrompt.ask_yes_no(self.root, lang.t("db_flush"), "Redis FLUSHALL?"):
            return
        pwd = self._dbm_rpass.get()
        def w():
            try:
                self.svc.redis_flush(pwd)
                self._dbm_show("OK: FLUSHALL")
            except Exception as e:
                self._dbm_failed(e)
        threading.Thread(target=w, daemon=True).start()

    def _build_perf(self, parent):
        self._perf_running = False
        self._perf_stop = threading.Event()
        self._perf_stats = None
        self._perf_summary = None
        cfg = tk.Frame(parent, bg=THEME["bg_elevated"])
        cfg.pack(fill="x", padx=10, pady=5)
        r1 = tk.Frame(cfg, bg=THEME["bg_elevated"])
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text=lang.t("perf_target"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        self._perf_target_var = tk.StringVar(value=f"http://127.0.0.1:{CONFIG['apache_port']}/")
        tk.Entry(r1, textvariable=self._perf_target_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=36).pack(side="left", padx=4)
        tk.Label(r1, text=lang.t("perf_profile"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        self._perf_profile_var = tk.StringVar(value="Normal")
        pm = tk.OptionMenu(r1, self._perf_profile_var, "Quick", "Normal", "Stress", "Spike", "Soak", "Endurance", "Custom",
                           command=self._perf_profile_changed)
        pm.configure(bg=THEME["entry_bg"], fg=THEME["entry_fg"], relief="flat",
                     activebackground=THEME["accent"], activeforeground=THEME["white"],
                     font=(THEME["font_family"], 9), highlightthickness=0)
        pm["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
        pm.pack(side="left", padx=4)
        r2 = tk.Frame(cfg, bg=THEME["bg_elevated"])
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text=lang.t("perf_users"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        self._perf_users_var = tk.StringVar(value="50")
        tk.Entry(r2, textvariable=self._perf_users_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=8).pack(side="left", padx=4)
        tk.Label(r2, text=lang.t("perf_duration"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        self._perf_dur_var = tk.StringVar(value="60")
        tk.Entry(r2, textvariable=self._perf_dur_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0, width=8).pack(side="left", padx=4)
        self._perf_toggle_btn = IconButton(r2, "play", self._perf_toggle,
                                            color=THEME["success"],
                                            hover_color="#55e39a", active_color=THEME["success_dim"],
                                            size=30, tip=lang.t("start") + " / " + lang.t("stop"))
        self._perf_toggle_btn.pack(side="left", padx=(16, 2))
        StyledButton(r2, "Auto", self._perf_auto, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     width=80, height=26, font_size=8).pack(side="left", padx=2)
        IconButton(r2, "bookmark", self._perf_set_base, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("perf_baseline")).pack(side="left", padx=2)
        IconButton(r2, "save", self._perf_save, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("perf_save")).pack(side="left", padx=2)
        tk.Label(cfg, text=lang.t("perf_paths"), bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                 font=(THEME["font_family"], 8), anchor="w").pack(fill="x", pady=(4, 0))
        self._perf_paths_txt = ScrolledText(cfg, wrap="word", bg="#0d0f16", fg="#b8bdd0",
                                            insertbackground="white", font=("Cascadia Code", 9),
                                            relief="flat", bd=0, padx=8, pady=4, height=3,
                                            selectbackground=THEME["accent"],
                                            selectforeground=THEME["white"])
        self._perf_paths_txt.pack(fill="x", pady=(0, 2))
        self._perf_paths_txt.insert("1.0", "GET /")

        res = tk.Frame(parent, bg=THEME["bg_elevated"])
        res.pack(fill="x", padx=10, pady=4)
        self._perf_vars = {}
        for i, key in enumerate(("RPS", "OK %", "ERR", "Avg ms", "P50", "P95", "P99", "CPU %",
                                 "RAM GB", "Users", "MB/s", "Peak")):
            cell = tk.Frame(res, bg=THEME["bg_card"], highlightbackground=THEME["border"],
                            highlightthickness=1)
            cell.grid(row=i // 4, column=i % 4, sticky="nsew", padx=4, pady=4)
            tk.Label(cell, text=key, bg=THEME["bg_card"], fg=THEME["text_muted"],
                     font=(THEME["font_family"], 8)).pack()
            var = tk.StringVar(value="—")
            tk.Label(cell, textvariable=var, bg=THEME["bg_card"], fg=THEME["accent"],
                     font=("Cascadia Code", 13, "bold")).pack()
            self._perf_vars[key] = var
        for c in range(4):
            res.grid_columnconfigure(c, weight=1)

        self._perf_canvas = tk.Canvas(parent, bg="#0d0f16", highlightthickness=0, height=150)
        self._perf_canvas.pack(fill="x", padx=10, pady=(0, 2))
        self._perf_base_label = tk.Label(parent, text="", bg=THEME["bg_elevated"], fg=THEME["warning"],
                                         font=("Cascadia Code", 9), anchor="w")
        self._perf_base_label.pack(fill="x", padx=12, pady=(0, 6))
        self._perf_base = None
        self._perf_on_done = None
        self._perf_auto_rows = []
        self._perf_rps_hist = []
        self._perf_p95_hist = []
        self._perf_cpu_hist = []
        self._perf_tick_n = 0

    def _perf_profile_changed(self, v):
        presets = {"Quick": ("10", "15"), "Normal": ("50", "60"), "Stress": ("200", "180"),
                   "Spike": ("300", "60"), "Soak": ("50", "1800"), "Endurance": ("100", "7200")}
        if v in presets:
            u, d = presets[v]
            self._perf_users_var.set(u)
            self._perf_dur_var.set(d)

    def _perf_toggle_visual(self, running):
        try:
            btn = self._perf_toggle_btn
            if running:
                btn.set_kind("stop")
                btn.set_colors(THEME["danger"], "#ff6b5a", THEME["danger_dim"])
            else:
                btn.set_kind("play")
                btn.set_colors(THEME["success"], "#55e39a", THEME["success_dim"])
        except Exception:
            pass

    def _perf_toggle(self):
        if getattr(self, "_perf_running", False):
            self._perf_on_done = None
            self._perf_auto_rows = []
            self._perf_stop.set()
            try:
                ch = getattr(self, "_perf_child", None)
                if ch is not None and ch.poll() is None:
                    kill_pid_tree(ch.pid)
            except Exception:
                pass
        else:
            self._perf_start()

    def _perf_start(self):
        if getattr(self, "_perf_running", False):
            return
        import random
        from concurrent.futures import ThreadPoolExecutor
        from urllib.parse import urlparse
        base = self._perf_target_var.get().strip().rstrip("/")
        if not base.startswith(("http://", "https://")):
            base = "http://" + base
        try:
            users = max(1, min(10000, int(self._perf_users_var.get())))
            dur = max(5, min(86400, int(self._perf_dur_var.get())))
        except ValueError:
            messagebox.showerror(lang.t("error"), "users/duration")
            return
        paths = []
        for line in self._perf_paths_txt.get("1.0", "end-1c").splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            m, p = parts[0].upper(), parts[1]
            try:
                w = max(1, int(parts[2])) if len(parts) > 2 else 1
            except ValueError:
                w = 1
            if m in ("GET", "POST", "PUT", "DELETE", "HEAD", "PATCH"):
                paths.append((m, p, w))
        if not paths:
            paths = [("GET", "/", 1)]
        try:
            host = (urlparse(base).hostname or "").lower()
        except Exception:
            host = ""
        allowed = {"127.0.0.1", "localhost", "::1"}
        try:
            allowed |= {str(s.get("domain", "")).lower() for s in (self._sites or []) if s.get("domain")}
        except Exception:
            pass
        if host not in allowed:
            if not DarkPrompt.ask_yes_no(self.root, lang.t("tab_perf"), f"{base} ?"):
                return
        weights = [x[2] for x in paths]
        stats = {"n": 0, "err": 0, "lat": [], "bytes": 0, "active": 0, "max_active": 0,
                 "lock": threading.Lock(), "t0": time.monotonic(),
                 "users": users, "dur": dur, "base": base,
                 "profile": self._perf_profile_var.get(), "threads": min(users, 2000)}
        self._perf_stats = stats
        self._perf_stop = threading.Event()
        self._perf_running = True
        self._perf_rps_hist = []
        self._perf_p95_hist = []
        self._perf_cpu_hist = []
        self._perf_tick_n = 0
        self._perf_last = (0, time.monotonic())
        self._perf_summary = None
        self._perf_timeline = []
        for v in self._perf_vars.values():
            v.set("—")
        stamp = time.strftime("%Y%m%d-%H%M%S")
        try:
            (APP_ROOT / "tmp").mkdir(parents=True, exist_ok=True)
            cfg_path = APP_ROOT / "tmp" / f"perftest-{stamp}.json"
            out_path = APP_ROOT / "tmp" / f"perftest-{stamp}.out"
            cfg_path.write_text(json.dumps({"base": base, "users": users, "dur": dur,
                                            "paths": paths, "out": str(out_path)}),
                                encoding="utf-8")
            out_path.write_text("", encoding="utf-8")
        except Exception as e:
            messagebox.showerror(lang.t("error"), str(e))
            return
        try:
            if getattr(sys, "frozen", False):
                cmd = [sys.executable, "--perf-child", str(cfg_path)]
            else:
                cmd = [sys.executable, str(Path(__file__).resolve()), "--perf-child", str(cfg_path)]
            child = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception as e:
            messagebox.showerror(lang.t("error"), str(e))
            return
        self._perf_child = child
        self._perf_out_path = str(out_path)

        def tail():
            pos, idle = 0, 0
            while True:
                try:
                    with open(str(out_path), "r", encoding="utf-8", errors="replace") as f:
                        f.seek(pos)
                        chunk = f.read()
                        pos = f.tell()
                except Exception:
                    chunk = ""
                if chunk:
                    idle = 0
                    for line in chunk.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            b = json.loads(line)
                        except Exception:
                            continue
                        if b.get("done"):
                            continue
                        with stats["lock"]:
                            stats["n"] = b.get("n", stats["n"])
                            stats["err"] = b.get("err", stats["err"])
                            stats["bytes"] = b.get("bytes", stats["bytes"])
                            stats["active"] = b.get("active", 0)
                            stats["max_active"] = max(stats["max_active"], b.get("active", 0))
                            for v in b.get("lat", []):
                                if len(stats["lat"]) < 500000:
                                    stats["lat"].append(v)
                    try:
                        self.root.after(0, self._perf_tick)
                    except Exception:
                        pass
                else:
                    idle += 1
                if child.poll() is not None and idle >= 2:
                    break
                time.sleep(0.5)
            for tmpf in (str(cfg_path), str(out_path)):
                try:
                    Path(tmpf).unlink(missing_ok=True)
                except Exception:
                    pass
            try:
                self.root.after(0, self._perf_finish)
            except Exception:
                pass

        self._perf_toggle_visual(True)
        threading.Thread(target=tail, daemon=True).start()
        self.log(f"Load test started in separate process (PID {child.pid}): "
                 f"{users} users, {dur}s -> {base} ({min(users, 2000)} OS threads)")

    def _perf_tick(self):
        st = getattr(self, "_perf_stats", None)
        if st is None:
            return
        with st["lock"]:
            n, err, lat = st["n"], st["err"], list(st["lat"])
        now = time.monotonic()
        ln0, t0 = getattr(self, "_perf_last", (0, now))
        rps = (n - ln0) / max(now - t0, 1e-6)
        self._perf_last = (n, now)
        if lat:
            s = sorted(lat)
            avg = sum(s) / len(s)
            p50 = s[min(len(s) - 1, int(0.50 * len(s)))]
            p95 = s[min(len(s) - 1, int(0.95 * len(s)))]
            p99 = s[min(len(s) - 1, int(0.99 * len(s)))]
        else:
            avg = p50 = p95 = p99 = 0.0
        ok_pct = (100.0 * (n - err) / n) if n else 100.0
        self._perf_rps_hist.append(rps)
        self._perf_p95_hist.append(p95)
        if len(self._perf_rps_hist) > 600:
            self._perf_rps_hist.pop(0)
            self._perf_p95_hist.pop(0)
        self._perf_vars["RPS"].set(f"{rps:.0f}")
        self._perf_vars["OK %"].set(f"{ok_pct:.2f}")
        self._perf_vars["ERR"].set(str(err))
        self._perf_vars["Avg ms"].set(f"{avg:.0f}")
        self._perf_vars["P50"].set(f"{p50:.0f}")
        self._perf_vars["P95"].set(f"{p95:.0f}")
        self._perf_vars["P99"].set(f"{p99:.0f}")
        with st["lock"]:
            active, max_active, total_bytes = st["active"], st["max_active"], st["bytes"]
        elapsed = max(now - st["t0"], 1e-6)
        mb_s = total_bytes / 1048576.0 / elapsed
        self._perf_vars["Users"].set(str(active))
        self._perf_vars["MB/s"].set(f"{mb_s:.2f}")
        self._perf_vars["Peak"].set(f"{max(self._perf_rps_hist) if self._perf_rps_hist else 0.0:.0f}")
        try:
            cpu_v = self._perf_vars["CPU %"].get()
            ram_v = self._perf_vars["RAM GB"].get()
        except Exception:
            cpu_v, ram_v = "—", "—"
        self._perf_summary = {"n": n, "err": err, "ok_pct": ok_pct, "avg": avg,
                              "p50": p50, "p95": p95, "p99": p99, "rps": rps,
                              "rps_peak": max(self._perf_rps_hist) if self._perf_rps_hist else 0.0,
                              "users": st["users"], "dur": st["dur"], "base": st["base"],
                              "profile": st.get("profile", "Custom"),
                              "threads": st.get("threads", st["users"]),
                              "mb": total_bytes / 1048576.0, "mb_s": mb_s,
                              "max_active": max_active}
        try:
            self._perf_timeline.append(
                (round(now - st["t0"]), round(rps, 1), round(ok_pct, 2), err,
                 round(avg, 1), round(p50, 1), round(p95, 1), round(p99, 1),
                 cpu_v, ram_v, active))
        except Exception:
            pass
        base_sm = getattr(self, "_perf_base", None)
        if base_sm:
            try:
                dr = sm_rps = self._perf_summary["rps"] - base_sm.get("rps_peak", 0)
                dp = self._perf_summary["p95"] - base_sm.get("p95", 0)
                self._perf_base_label.configure(
                    text=f"ΔRPS {dr:+.0f} | ΔP95 {dp:+.0f} ms  (vs baseline: "
                         f"{base_sm.get('users', '?')} users, {base_sm.get('base', '')})")
            except Exception:
                pass
        self._perf_tick_n = getattr(self, "_perf_tick_n", 0) + 1
        if self._perf_tick_n % 3 == 0:
            threading.Thread(target=self._perf_sysstat, daemon=True).start()
        if self._perf_tick_n % 10 == 0:
            self.log(f"[{int(now - st['t0'])}s] {rps:.0f} rps, OK {ok_pct:.2f}%, "
                     f"p95 {p95:.0f} ms, err {err}")
        self._perf_draw()

    def _perf_sysstat(self):
        try:
            ps = ("$c = Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average; "
                  "$o = Get-CimInstance Win32_OperatingSystem; "
                  "\"{0}|{1}|{2}\" -f $c, $o.FreePhysicalMemory, $o.TotalVisibleMemorySize")
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True,
                               text=True, timeout=15,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            cpu, free_kb, total_kb = [float(x) for x in r.stdout.strip().split("|")]
            used_gb = (total_kb - free_kb) / 1048576.0
            self._perf_cpu_hist.append(cpu)
            self.root.after(0, lambda: (self._perf_vars["CPU %"].set(f"{cpu:.0f}"),
                                        self._perf_vars["RAM GB"].set(f"{used_gb:.1f}")))
        except Exception:
            pass

    def _perf_draw(self):
        try:
            cv = self._perf_canvas
            cv.delete("all")
            W = cv.winfo_width() or 600
            H = 150
            rh, ph = self._perf_rps_hist, self._perf_p95_hist
            if not rh:
                return
            rmax = max(rh) or 1.0
            pmax = max(ph) or 1.0
            n = len(rh)
            step = W / max(n - 1, 1)
            for i in (1, 2, 3):
                y = H * i // 4
                cv.create_line(0, y, W, y, fill=THEME["border"])
            pts_r, pts_p = [], []
            for i, (r, p) in enumerate(zip(rh, ph)):
                x = i * step
                pts_r += [x, H - 4 - (r / rmax) * (H - 14)]
                pts_p += [x, H - 4 - (p / pmax) * (H - 14)]
            if len(pts_r) >= 4:
                cv.create_line(*pts_r, fill=THEME["success"], width=2)
            if len(pts_p) >= 4:
                cv.create_line(*pts_p, fill=THEME["warning"], width=2)
            cv.create_text(8, 8, anchor="w", text=f"max {rmax:.0f} rps",
                           fill=THEME["text_dim"], font=("Cascadia Code", 8))
            lx = W - 8
            cv.create_text(lx, 8, anchor="e", text="P95 ms", fill=THEME["warning"],
                           font=("Cascadia Code", 8, "bold"))
            cv.create_line(lx - 62, 8, lx - 46, 8, fill=THEME["warning"], width=3)
            cv.create_text(lx - 70, 8, anchor="e", text="RPS", fill=THEME["success"],
                           font=("Cascadia Code", 8, "bold"))
            cv.create_line(lx - 116, 8, lx - 100, 8, fill=THEME["success"], width=3)
        except Exception:
            pass

    def _perf_finish(self):
        self._perf_running = False
        self._perf_tick()
        sm = self._perf_summary or {}
        self.log(f"Load test finished: {sm.get('base', '')} "
                 f"[{sm.get('profile', 'Custom')}, {sm.get('users', 0)} users, "
                 f"{sm.get('dur', 0)}s, {sm.get('threads', 0)} OS threads]")
        self.log(f"  requests: {sm.get('n', 0)} | OK: {sm.get('ok_pct', 100.0):.2f}% | "
                 f"errors: {sm.get('err', 0)} | transferred: {sm.get('mb', 0):.2f} MB")
        self.log(f"  avg {sm.get('avg', 0):.1f} ms | p50 {sm.get('p50', 0):.1f} ms | "
                 f"p95 {sm.get('p95', 0):.1f} ms | p99 {sm.get('p99', 0):.1f} ms | "
                 f"peak {sm.get('rps_peak', 0):.0f} rps | max active {sm.get('max_active', 0)}")
        if self._perf_cpu_hist:
            self.log(f"  CPU max: {max(self._perf_cpu_hist):.0f}%")
        cb = getattr(self, "_perf_on_done", None)
        self._perf_on_done = None
        if cb:
            try:
                cb(dict(sm))
            except Exception as e:
                self.log(f"Auto benchmark ERROR: {e}")
        else:
            self._perf_toggle_visual(False)

    def _perf_set_base(self):
        sm = getattr(self, "_perf_summary", None)
        if not sm:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        self._perf_base = dict(sm)
        self.log(f"Baseline set: {sm.get('users')} users, peak {sm.get('rps_peak', 0):.0f} rps, "
                 f"p95 {sm.get('p95', 0):.0f} ms")

    def _perf_auto(self):
        if getattr(self, "_perf_running", False):
            return
        from urllib.parse import urlparse
        base = self._perf_target_var.get().strip().rstrip("/") or "http://127.0.0.1/"
        if not base.startswith(("http://", "https://")):
            base = "http://" + base
        try:
            host = (urlparse(base).hostname or "").lower()
        except Exception:
            host = ""
        allowed = {"127.0.0.1", "localhost", "::1"}
        try:
            allowed |= {str(s.get("domain", "")).lower() for s in (self._sites or []) if s.get("domain")}
        except Exception:
            pass
        if host not in allowed:
            if not DarkPrompt.ask_yes_no(self.root, lang.t("tab_perf"), f"{base} ?"):
                return
        stages = [(10, 15), (25, 20), (50, 30), (100, 30), (200, 30)]
        self._perf_auto_rows = []
        self.log(f"Auto benchmark started -> {base} ({len(stages)} stages)")

        def run_stage(i):
            if i >= len(stages):
                self._perf_auto_report(base)
                return
            u, d = stages[i]
            self._perf_users_var.set(str(u))
            self._perf_dur_var.set(str(d))
            self._perf_on_done = lambda sm, i=i: (
                self._perf_auto_rows.append((u, d, sm)),
                self.root.after(2000, lambda: run_stage(i + 1)))
            self._perf_start()

        run_stage(0)

    def _perf_auto_report(self):
        rows = getattr(self, "_perf_auto_rows", [])
        if not rows:
            return
        self.log("Auto benchmark results (users | RPS peak | P95 | errors):")
        table = []
        for u, d, sm in rows:
            line = (f"{u:>5} users | {sm.get('rps_peak', 0):>7.0f} rps | "
                    f"p95 {sm.get('p95', 0):>6.0f} ms | err {sm.get('err', 0)}")
            table.append(line)
            self.log("  " + line)
        stable = [r for r in rows if r[2].get("err", 1) == 0]
        if stable:
            best = max(stable, key=lambda r: r[2].get("rps_peak", 0))
            self.log(f"Stable max: {best[2].get('rps_peak', 0):.0f} rps @ {best[0]} users")
        self._perf_summary = dict(rows[-1][2])
        self._perf_tick()
        self._perf_toggle_visual(False)

    def _perf_save(self):
        sm = getattr(self, "_perf_summary", None)
        if not sm:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text", "*.txt")],
                                            initialfile="perftest.txt")
        if not path:
            return
        lines = [
            f"Faraja WebServer — load test report ({time.strftime('%Y-%m-%d %H:%M:%S')})",
            "",
            "== Test setup ==",
            f"Target: {sm['base']}",
            f"Profile: {sm.get('profile', 'Custom')} | virtual users: {sm['users']} | "
            f"duration: {sm['dur']}s | OS threads in generator process: {sm.get('threads', sm['users'])}",
            "Note: the generator runs in a separate process, so the app UI stays responsive",
            "and does not steal CPU from the tested server (except for the system-wide CPU/RAM readout).",
            "",
            "== Summary ==",
            f"Requests: {sm['n']} | OK: {sm['ok_pct']:.2f}% | errors: {sm['err']}",
            f"Avg: {sm['avg']:.1f} ms | P50: {sm['p50']:.1f} ms | "
            f"P95: {sm['p95']:.1f} ms | P99: {sm['p99']:.1f} ms",
            f"Peak RPS: {sm['rps_peak']:.0f} | transferred: {sm['mb']:.2f} MB "
            f"({sm.get('mb_s', 0):.2f} MB/s) | max active users: {sm.get('max_active', 0)}",
        ]
        if self._perf_cpu_hist:
            lines.append(f"CPU max (whole system): {max(self._perf_cpu_hist):.0f}%")
        for u, d, sm in getattr(self, "_perf_auto_rows", []):
            lines.append(f"auto {u}u/{d}s: peak {sm.get('rps_peak', 0):.0f} rps, "
                         f"p95 {sm.get('p95', 0):.0f} ms, err {sm.get('err', 0)}")
        lines += [
            "",
            "== Metrics glossary ==",
            "RPS — completed HTTP requests per second (green line on the chart).",
            "OK % — share of responses with HTTP status < 400.",
            "ERR — failed requests (HTTP 4xx/5xx, timeouts, connection errors).",
            "Avg — arithmetic mean response time over the whole test.",
            "P50/P95/P99 — latency percentiles: 50/95/99% of requests were faster than this.",
            "CPU % / RAM GB — whole-system load sampled every ~3s (includes the generator process).",
            "Users — currently active virtual users. MB/s — response throughput. Peak — best 1-second RPS.",
            "",
            "== How to read the chart ==",
            "Green line = RPS per second. Orange line = P95 latency per second (own scale).",
            "Both lines are jagged by design: every point is a real 1-second sample,",
            "and localhost latency naturally jitters (GC pauses, scheduler, TCP).",
            "An UP spike on green = burst of completions (e.g. recovery after a stall).",
            "A DOWN spike on green = requests stalled that second (server saturated, timeouts queueing).",
            "An UP spike on orange = momentary latency degradation — correlate it with the same",
            "second on green and with CPU: if both spike, the server (or the machine) hit a limit.",
            "A flat orange line near zero with falling green = mass timeouts (10s cap each).",
            "",
            "== Per-second timeline ==",
            "sec | RPS | OK% | ERR | Avg | P50 | P95 | P99 | CPU | RAM | Users",
        ]
        for row in getattr(self, "_perf_timeline", []):
            lines.append(" | ".join(str(x) for x in row))
        try:
            Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.log(f"Report saved: {path}")
        except Exception as e:
            messagebox.showerror(lang.t("error"), str(e))

    def _build_procs(self, parent):
        self._procs_rows = []
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        IconButton(top, "refresh", self._procs_refresh, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_refresh") + " — " + lang.t("tip_refresh")).pack(side="left", padx=2)
        IconButton(top, "cross", self._procs_kill, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("btn_delete") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        tk.Label(top, text=lang.t("log_find"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        self._procs_search_var = tk.StringVar(value="")
        se = tk.Entry(top, textvariable=self._procs_search_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                      insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                      relief="flat", bd=0, width=24)
        se.pack(side="left", padx=4)
        se.bind("<KeyRelease>", lambda e: self._procs_filter())
        cols = ("pid", "proc", "parent", "mem", "port")
        self._procs_tree = ttk.Treeview(parent, columns=cols, show="headings", height=14,
                                        style="Big.Treeview")
        self._procs_tree.heading("pid", text=lang.t("col_pid"))
        self._procs_tree.heading("proc", text=lang.t("col_proc"))
        self._procs_tree.heading("parent", text=lang.t("col_parent"))
        self._procs_tree.heading("mem", text=lang.t("col_mem"))
        self._procs_tree.heading("port", text=lang.t("col_port"))
        self._procs_tree.column("pid", width=80)
        self._procs_tree.column("proc", width=260)
        self._procs_tree.column("parent", width=100)
        self._procs_tree.column("mem", width=100)
        self._procs_tree.column("port", width=140)
        self._procs_tree.pack(fill="both", expand=True, padx=10, pady=4)
        self._procs_status = tk.Label(parent, text="", bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                                      font=(THEME["font_family"], 8), anchor="w")
        self._procs_status.pack(fill="x", padx=12, pady=(0, 6))
        self._procs_refresh()

    def _procs_filter(self):
        if not hasattr(self, "_procs_tree"):
            return
        q = self._procs_search_var.get().strip().lower()
        for item in self._procs_tree.get_children():
            self._procs_tree.delete(item)
        for pr in self._procs_rows:
            if q and q not in pr["name"].lower() and q not in str(pr["pid"]):
                continue
            self._procs_tree.insert("", "end", iid=pr["pid"],
                                    values=(pr["pid"], pr["name"], pr["ppid"],
                                            f"{pr['mem']} MB", pr["ports"]))

    def _procs_refresh(self):
        self._procs_status.configure(text="…")
        def w():
            try:
                rows = self.svc.proc_list()
                def ui():
                    self._procs_rows = rows
                    self._procs_filter()
                    self._procs_status.configure(text="")
                self.root.after(0, ui)
            except Exception as e:
                self.root.after(0, lambda: self._procs_status.configure(text=str(e)[:200]))
        threading.Thread(target=w, daemon=True).start()

    def _procs_kill(self):
        sel = self._procs_tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        try:
            pid = int(sel[0])
        except ValueError:
            return
        if not DarkPrompt.ask_yes_no(self.root, lang.t("btn_delete"),
                                     f"{lang.t('confirm_delete')} PID {pid}?"):
            return
        kill_pid_tree(pid)
        self.log(f"Killed PID {pid}")
        self.root.after(1500, self._procs_refresh)

    def _build_docker(self, parent):
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        IconButton(top, "refresh", self._dock_refresh, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_refresh") + " — " + lang.t("tip_refresh")).pack(side="left", padx=2)
        IconButton(top, "play", lambda: self._dock_ctl("start"), color=THEME["success"],
                     hover_color="#55e39a", active_color=THEME["success_dim"],
                     size=30, tip=lang.t("start") + " — " + lang.t("tip_run")).pack(side="left", padx=2)
        IconButton(top, "stop", lambda: self._dock_ctl("stop"), color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("stop") + " — " + lang.t("tip_start")).pack(side="left", padx=2)
        IconButton(top, "restart", lambda: self._dock_ctl("restart"), color=THEME["warning_dim"],
                     hover_color=THEME["warning"], active_color="#ba5e17",
                     size=30, tip=lang.t("restart") + " — " + lang.t("tip_restart")).pack(side="left", padx=2)
        IconButton(top, "cross", lambda: self._dock_ctl("rm"), color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        cols = ("name", "image", "status", "ports")
        self._dock_tree = ttk.Treeview(parent, columns=cols, show="headings", height=6,
                                       style="Big.Treeview")
        self._dock_tree.heading("name", text=lang.t("col_cont"))
        self._dock_tree.heading("image", text=lang.t("col_image"))
        self._dock_tree.heading("status", text=lang.t("col_dockstatus"))
        self._dock_tree.heading("ports", text=lang.t("col_ports"))
        self._dock_tree.column("name", width=160)
        self._dock_tree.column("image", width=200)
        self._dock_tree.column("status", width=180)
        self._dock_tree.column("ports", width=200)
        self._dock_tree.pack(fill="both", expand=True, padx=10, pady=4)
        self._dock_status = tk.Label(parent, text="", bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                                     font=(THEME["font_family"], 8), anchor="w")
        self._dock_status.pack(fill="x", padx=12, pady=(0, 2))

        comp = tk.Frame(parent, bg=THEME["bg_elevated"])
        comp.pack(fill="x", padx=10, pady=4)
        tk.Label(comp, text=lang.t("dock_file"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9, "bold")).pack(side="left")
        self._dock_compose_var = tk.StringVar(value=str(WWW / "docker-compose.yml"))
        tk.Entry(comp, textvariable=self._dock_compose_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True, padx=6)
        IconButton(comp, "folder", self._dock_browse_compose, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("tip_browse")).pack(side="left", padx=2)
        IconButton(comp, "up", lambda: self._dock_compose("up"), color=THEME["success"],
                     hover_color="#55e39a", active_color=THEME["success_dim"],
                     size=28, tip=lang.t("dock_up") + " — " + lang.t("tip_run")).pack(side="left", padx=2)
        IconButton(comp, "stop", lambda: self._dock_compose("down"), color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=28, tip=lang.t("dock_down")).pack(side="left", padx=2)
        IconButton(comp, "restart", lambda: self._dock_compose("restart"), color=THEME["warning_dim"],
                     hover_color=THEME["warning"], active_color="#ba5e17",
                     size=28, tip=lang.t("restart") + " — " + lang.t("tip_restart")).pack(side="left", padx=2)
        IconButton(comp, "down", lambda: self._dock_compose("pull"), color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("dock_pull")).pack(side="left", padx=2)
        IconButton(comp, "plus", lambda: self._dock_compose("build"), color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("dock_build")).pack(side="left", padx=2)
        IconButton(comp, "list", self._dock_compose_logs, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     size=28, tip=lang.t("dock_logs")).pack(side="left", padx=2)

        tk.Label(parent, text=lang.t("dock_images"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9, "bold"), anchor="w").pack(fill="x", padx=12, pady=(2, 0))
        imgrow = tk.Frame(parent, bg=THEME["bg_elevated"])
        imgrow.pack(fill="x", padx=10, pady=2)
        IconButton(imgrow, "refresh", self._dock_images_refresh, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("btn_refresh") + " — " + lang.t("tip_refresh")).pack(side="left", padx=2)
        IconButton(imgrow, "cross", self._dock_image_remove, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=28, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        self._dock_img_tree = ttk.Treeview(parent, columns=("image", "tag", "size"), show="headings",
                                           height=4, style="Big.Treeview")
        self._dock_img_tree.heading("image", text=lang.t("col_image"))
        self._dock_img_tree.heading("tag", text=lang.t("col_tag"))
        self._dock_img_tree.heading("size", text=lang.t("col_size"))
        self._dock_img_tree.column("image", width=280)
        self._dock_img_tree.column("tag", width=120)
        self._dock_img_tree.column("size", width=100)
        self._dock_img_tree.pack(fill="x", padx=10, pady=(0, 4))

        nv = tk.Frame(parent, bg=THEME["bg_elevated"])
        nv.pack(fill="x", padx=10, pady=(0, 6))
        left = tk.Frame(nv, bg=THEME["bg_elevated"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        tk.Label(left, text=lang.t("dock_networks"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9, "bold"), anchor="w").pack(fill="x")
        self._dock_net_tree = ttk.Treeview(left, columns=("name", "driver"), show="headings",
                                           height=3, style="Big.Treeview")
        self._dock_net_tree.heading("name", text=lang.t("col_cont"))
        self._dock_net_tree.heading("driver", text="Driver")
        self._dock_net_tree.column("name", width=160)
        self._dock_net_tree.column("driver", width=100)
        self._dock_net_tree.pack(fill="x")
        IconButton(left, "cross", self._dock_net_remove, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(anchor="w", pady=2)
        right = tk.Frame(nv, bg=THEME["bg_elevated"])
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))
        tk.Label(right, text=lang.t("dock_volumes"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9, "bold"), anchor="w").pack(fill="x")
        self._dock_vol_tree = ttk.Treeview(right, columns=("name", "driver"), show="headings",
                                           height=3, style="Big.Treeview")
        self._dock_vol_tree.heading("name", text=lang.t("col_cont"))
        self._dock_vol_tree.heading("driver", text="Driver")
        self._dock_vol_tree.column("name", width=160)
        self._dock_vol_tree.column("driver", width=100)
        self._dock_vol_tree.pack(fill="x")
        IconButton(right, "cross", self._dock_vol_remove, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(anchor="w", pady=2)
        self._dock_refresh()
        self._dock_images_refresh()
        self._dock_nets_vols_refresh()

    def _dock_fill(self, rows):
        for item in self._dock_tree.get_children():
            self._dock_tree.delete(item)
        for name, image, status, ports in rows:
            self._dock_tree.insert("", "end", iid=name, values=(name, image, status, ports))
        self._dock_status.configure(text="")

    def _dock_refresh(self):
        self._dock_status.configure(text="…")
        def w():
            try:
                rows = self.svc.docker_ps()
                self.root.after(0, lambda: self._dock_fill(rows))
            except Exception as e:
                self.root.after(0, lambda: self._dock_status.configure(text=str(e)[:200]))
        threading.Thread(target=w, daemon=True).start()

    def _dock_ctl(self, action):
        sel = list(self._dock_tree.selection())
        if not sel:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        if action == "rm":
            if not DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"),
                                         f"{lang.t('confirm_delete')} {sel[0]}?"):
                return
        def w():
            try:
                for name in sel:
                    self.svc.docker_ctl(action, name)
                self.root.after(0, self._dock_refresh)
            except Exception as e:
                self.log(f"docker {action} ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _dock_nets_vols_refresh(self):
        def w():
            try:
                nets = self.svc.docker_networks()
                vols = self.svc.docker_volumes()
                def ui():
                    for item in self._dock_net_tree.get_children():
                        self._dock_net_tree.delete(item)
                    for name, driver, _scope in nets:
                        self._dock_net_tree.insert("", "end", iid="n:" + name, values=(name, driver))
                    for item in self._dock_vol_tree.get_children():
                        self._dock_vol_tree.delete(item)
                    for name, driver in vols:
                        self._dock_vol_tree.insert("", "end", iid="v:" + name, values=(name, driver))
                self.root.after(0, ui)
            except Exception as e:
                self.root.after(0, lambda: self._dock_status.configure(text=str(e)[:200]))
        threading.Thread(target=w, daemon=True).start()

    def _dock_net_remove(self):
        sel = list(self._dock_net_tree.selection())
        if not sel:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        name = sel[0][2:]
        if not DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"),
                                     f"{lang.t('confirm_delete')} {name}?"):
            return
        def w():
            try:
                self.svc.docker_net_rm(name)
                self.root.after(0, self._dock_nets_vols_refresh)
            except Exception as e:
                self.log(f"docker network rm ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _dock_vol_remove(self):
        sel = list(self._dock_vol_tree.selection())
        if not sel:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        name = sel[0][2:]
        if not DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"),
                                     f"{lang.t('confirm_delete')} {name}?"):
            return
        def w():
            try:
                self.svc.docker_vol_rm(name)
                self.root.after(0, self._dock_nets_vols_refresh)
            except Exception as e:
                self.log(f"docker volume rm ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _dock_browse_compose(self):
        from tkinter import filedialog
        f = filedialog.askopenfilename(
            title="docker-compose.yml",
            filetypes=[("Compose", "*.yml;*.yaml"), ("All files", "*.*")],
            initialdir=str(WWW))
        if f:
            self._dock_compose_var.set(f)

    def _dock_compose(self, action):
        compose = self._dock_compose_var.get().strip()
        if not compose:
            return
        def w():
            try:
                out = self.svc.docker_compose(action, compose)
                self.log(f"compose {action} output:\n{out[-500:]}")
                self.root.after(0, self._dock_refresh)
            except Exception as e:
                self.log(f"compose {action} ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _dock_compose_logs(self):
        compose = self._dock_compose_var.get().strip()
        if not compose:
            return
        win = tk.Toplevel(self.root)
        win.title("docker compose logs")
        win.geometry("800x500")
        win.configure(bg=THEME["bg_elevated"])
        try:
            win.iconbitmap(str(ICON))
        except Exception:
            pass
        t = ScrolledText(win, wrap="word", bg="#0d0f16", fg="#b8bdd0",
                         insertbackground="white", font=("Cascadia Code", 9),
                         relief="flat", bd=0, padx=10, pady=6,
                         selectbackground=THEME["accent"], selectforeground=THEME["white"])
        t.pack(fill="both", expand=True, padx=10, pady=10)
        t.insert("1.0", "…")
        t.configure(state="disabled")
        def load():
            try:
                out = self.svc.docker_compose_logs(compose)
                def ui():
                    t.configure(state="normal")
                    t.delete("1.0", "end")
                    t.insert("1.0", out)
                    t.see("end")
                    t.configure(state="disabled")
                self.root.after(0, ui)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=load, daemon=True).start()

    def _dock_images_refresh(self):
        def w():
            try:
                rows = self.svc.docker_images()
                def ui():
                    for item in self._dock_img_tree.get_children():
                        self._dock_img_tree.delete(item)
                    for repo, tag, iid, size in rows:
                        self._dock_img_tree.insert("", "end", iid=iid,
                                                   values=(repo, tag, size))
                self.root.after(0, ui)
            except Exception as e:
                self.root.after(0, lambda: self._dock_status.configure(text=str(e)[:200]))
        threading.Thread(target=w, daemon=True).start()

    def _dock_image_remove(self):
        sel = list(self._dock_img_tree.selection())
        if not sel:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        if not DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"),
                                     f"{lang.t('confirm_delete')} {sel[0]}?"):
            return
        def w():
            try:
                for iid in sel:
                    self.svc.docker_rmi(iid)
                self.root.after(0, self._dock_images_refresh)
            except Exception as e:
                self.log(f"docker rmi ERROR: {e}")
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _db_entry(self, parent, row, col, text, var, width=14, show=None):
        tk.Label(parent, text=text, bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).grid(row=row, column=col, sticky="w",
                                                      padx=(0, 4), pady=4)
        e = tk.Entry(parent, textvariable=var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                     insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9),
                     relief="flat", bd=0, width=width, highlightthickness=1,
                     highlightbackground=THEME["border"], highlightcolor=THEME["accent"])
        if show:
            e.configure(show=show)
        e.grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4)
        return e

    def _db_static(self, parent, row, col, text, value):
        tk.Label(parent, text=text, bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).grid(row=row, column=col, sticky="w",
                                                      padx=(0, 4), pady=4)
        tk.Label(parent, text=value, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 font=("Cascadia Code", 9), padx=8, pady=3, anchor="w",
                 highlightthickness=1, highlightbackground=THEME["border"]).grid(
                     row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4)

    def _db_button(self, parent, row, col, kind, tip, cmd, color, hover, active):
        b = IconButton(parent, kind, cmd, color=color, hover_color=hover,
                       active_color=active, size=28, tip=tip)
        b.grid(row=row, column=col, sticky="w", padx=4, pady=4)
        return b

    def _build_db(self, parent):
        md = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                      highlightthickness=1)
        md.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(md, text="MariaDB", bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=(THEME["font_family"], 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        mg = tk.Frame(md, bg=THEME["bg_elevated"])
        mg.pack(fill="x", padx=10, pady=(0, 8))
        self._maria_port_var = tk.StringVar(value=str(CONFIG["mariadb_port"]))
        self._db_static(mg, 0, 0, lang.t("db_host"), "127.0.0.1")
        self._db_entry(mg, 0, 2, lang.t("node_port"), self._maria_port_var, width=6)
        self._db_button(mg, 0, 4, "check", lang.t("db_apply"), self._maria_apply,
                        THEME["success"], "#55e39a", THEME["success_dim"])
        self._maria_cur_var = tk.StringVar(value="")
        self._maria_new_var = tk.StringVar(value="")
        self._db_entry(mg, 1, 0, lang.t("db_curpass"), self._maria_cur_var, width=14, show="*")
        self._db_entry(mg, 1, 2, lang.t("db_rootpass"), self._maria_new_var, width=14, show="*")
        self._db_button(mg, 1, 4, "lock", lang.t("db_setpass"), self._maria_set_pass,
                        THEME["warning_dim"], THEME["warning"], "#ba5e17")

        pg = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                      highlightthickness=1)
        pg.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(pg, text="PostgreSQL", bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=(THEME["font_family"], 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        pgf = tk.Frame(pg, bg=THEME["bg_elevated"])
        pgf.pack(fill="x", padx=10, pady=(0, 8))
        self._pg_port_var = tk.StringVar(value=str(CONFIG["postgresql_port"]))
        self._pg_user_var = tk.StringVar(value="postgres")
        self._pg_pass_var = tk.StringVar(value="")
        self._pg_db_var = tk.StringVar(value="postgres")
        self._db_static(pgf, 0, 0, lang.t("db_host"), "127.0.0.1")
        self._db_entry(pgf, 0, 2, lang.t("node_port"), self._pg_port_var, width=6)
        self._db_entry(pgf, 0, 4, lang.t("db_user"), self._pg_user_var, width=14)
        self._db_entry(pgf, 0, 6, lang.t("db_pass"), self._pg_pass_var, width=14, show="*")
        self._db_entry(pgf, 1, 0, lang.t("db_name"), self._pg_db_var, width=16)
        _pgbtns = tk.Frame(pgf, bg=THEME["bg_elevated"])
        _pgbtns.grid(row=1, column=2, columnspan=7, sticky="w", padx=4, pady=4)
        self._db_button(_pgbtns, 0, 0, "check", lang.t("db_apply"), self._pg_apply,
                        THEME["success"], "#55e39a", THEME["success_dim"])
        self._db_button(_pgbtns, 0, 1, "plus", lang.t("db_createdb"), self._pg_create_db,
                        THEME["info"], "#2e9bf5", "#0769b5")
        self._db_button(_pgbtns, 0, 2, "lock", lang.t("db_setpass"), self._pg_set_pass,
                        THEME["warning_dim"], THEME["warning"], "#ba5e17")

        rd = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"],
                      highlightthickness=1)
        rd.pack(fill="x", padx=10, pady=4)
        tk.Label(rd, text="Redis", bg=THEME["bg_elevated"], fg=THEME["accent"],
                 font=(THEME["font_family"], 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        rg = tk.Frame(rd, bg=THEME["bg_elevated"])
        rg.pack(fill="x", padx=10, pady=(0, 8))
        try:
            _rc = self.svc.redis_conf()
        except Exception:
            _rc = {"bind": "127.0.0.1", "password": ""}
        self._redis_bind_var = tk.StringVar(value=_rc.get("bind") or "127.0.0.1")
        self._redis_pass_var = tk.StringVar(value=_rc.get("password") or "")
        self._db_entry(rg, 0, 0, lang.t("db_bind"), self._redis_bind_var, width=16)
        self._db_entry(rg, 0, 2, lang.t("db_pass"), self._redis_pass_var, width=20, show="*")
        self._db_button(rg, 0, 4, "check", lang.t("db_apply"), self._redis_apply,
                        THEME["success"], "#55e39a", THEME["success_dim"])

        self._db_status = tk.Label(parent, text="", bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                                   font=(THEME["font_family"], 8), anchor="w")
        self._db_status.pack(fill="x", padx=12, pady=4)

    def _db_ok(self, msg):
        self.log(msg)
        try:
            self.root.after(0, lambda: self._db_status.configure(text=msg[:160]))
        except Exception:
            pass

    def _db_err(self, e):
        self.log("DB ERROR: " + str(e))
        self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))

    def _maria_apply(self):
        port = self._maria_port_var.get().strip()
        def w():
            try:
                self.svc.maria_apply_port(port)
                self.root.after(0, self._refresh_port_label)
                self._db_ok(f"MariaDB port: {port}")
            except Exception as e:
                self._db_err(e)
        threading.Thread(target=w, daemon=True).start()

    def _maria_set_pass(self):
        cur, new = self._maria_cur_var.get(), self._maria_new_var.get()
        if not new:
            messagebox.showinfo(APP_NAME, lang.t("db_rootpass"))
            return
        def w():
            try:
                self.svc.maria_set_root_password(cur, new)
                self.root.after(0, lambda: self._maria_new_var.set(""))
                self._db_ok("MariaDB root password updated")
            except Exception as e:
                self._db_err(e)
        threading.Thread(target=w, daemon=True).start()

    def _pg_apply(self):
        port = self._pg_port_var.get().strip()
        def w():
            try:
                self.svc.pg_apply_port(port)
                self.root.after(0, self._refresh_port_label)
                self._db_ok(f"PostgreSQL port: {port}")
            except Exception as e:
                self._db_err(e)
        threading.Thread(target=w, daemon=True).start()

    def _refresh_port_label(self):
        try:
            for attr, (lbl, key, cfgkey) in self._port_labels.items():
                lbl.configure(text=f"{key} {CONFIG[cfgkey]}")
        except Exception:
            pass

    def _colorize_port_label(self, attr, running):
        try:
            lbl, _, _ = self._port_labels[attr]
            lbl.configure(fg=THEME["success"] if running else THEME["text_dim"],
                          font=("Cascadia Code", 8, "bold" if running else "normal"))
        except Exception:
            pass

    def _pg_create_db(self):
        user, pwd, db = self._pg_user_var.get().strip(), self._pg_pass_var.get(), self._pg_db_var.get().strip()
        def w():
            try:
                self.svc.pg_create_db(user or "postgres", pwd, db)
                self._db_ok(f"Database created: {db}")
            except Exception as e:
                self._db_err(e)
        threading.Thread(target=w, daemon=True).start()

    def _pg_set_pass(self):
        user, pwd = self._pg_user_var.get().strip() or "postgres", self._pg_pass_var.get()
        new_pass = DarkPrompt.ask_string(self.root, lang.t("db_setpass"),
                                         f"{user}: {lang.t('db_pass')}")
        if not new_pass:
            return
        def w():
            try:
                self.svc.pg_set_password(user, pwd, user, new_pass)
                self._db_ok(f"Password set: {user}")
            except Exception as e:
                self._db_err(e)
        threading.Thread(target=w, daemon=True).start()

    def _redis_apply(self):
        bind = self._redis_bind_var.get().strip() or "127.0.0.1"
        pwd = self._redis_pass_var.get()
        def w():
            try:
                (APP_ROOT / "config").mkdir(parents=True, exist_ok=True)
                (APP_ROOT / "config" / "redis.json").write_text(
                    json.dumps({"bind": bind, "password": pwd}, indent=2), encoding="utf-8")
                if self.svc.redisrun():
                    self.log("Restarting Redis to apply new settings...")
                    self.svc.stop_redis()
                    self.svc.start_redis()
                self._db_ok(f"Redis: bind {bind}, password {'set' if pwd else 'empty'}")
            except Exception as e:
                self._db_err(e)
        threading.Thread(target=w, daemon=True).start()

    def _status_bar(self, parent):
        bar = tk.Frame(parent, bg=THEME["bg_card"], height=30, highlightbackground=THEME["border"], highlightthickness=1)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)
        self.status = tk.StringVar(value=lang.t("status_ready"))
        tk.Label(bar, text="●", bg=THEME["bg_card"], fg=THEME["success"], font=(THEME["font_family"], 9)).pack(side="left", padx=(14,6))
        tk.Label(bar, textvariable=self.status, bg=THEME["bg_card"], fg=THEME["text_dim"],
                 anchor="w", font=(THEME["font_family"], 8)).pack(side="left")
        tk.Label(bar, text="LOCAL  •  READY", bg=THEME["bg_card"], fg=THEME["text_muted"],
                 font=("Cascadia Code", 7, "bold")).pack(side="right", padx=14)


    def _nav_button(self, parent, text, icon, command, active=False):
        bg = THEME["accent"] if active else THEME["bg_card"]
        fg = THEME["white"] if active else THEME["text_dim"]
        btn = tk.Frame(parent, bg=bg, height=38, cursor="hand2")
        btn.pack(fill="x", pady=2)
        btn.pack_propagate(False)
        rail = tk.Frame(btn, bg=THEME["accent"] if active else bg, width=3)
        rail.pack(side="left", fill="y")
        tk.Label(btn, text=icon, bg=bg, fg=THEME["white"] if active else THEME["accent"],
                 font=("Segoe UI Emoji", 13), width=3).pack(side="left", padx=(7, 1))
        tk.Label(btn, text=text, bg=bg, fg=fg,
                 font=(THEME["font_family"], 9, "bold" if active else "normal"),
                 anchor="w").pack(side="left", fill="x", expand=True)
        if active:
            tk.Label(btn, text="›", bg=bg, fg=THEME["white"],
                     font=(THEME["font_family"], 15, "bold")).pack(side="right", padx=10)
        for w in btn.winfo_children():
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>", lambda e, b=btn, a=active: b.configure(bg=THEME["bg_elevated"] if not a else THEME["accent_hover"]))
            w.bind("<Leave>", lambda e, b=btn, a=active, c=bg: b.configure(bg=c))
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e, b=btn, a=active: b.configure(bg=THEME["bg_elevated"] if not a else THEME["accent_hover"]))
        btn.bind("<Leave>", lambda e, b=btn, a=active, c=bg: b.configure(bg=c))
        return btn

    def _build_sidebar(self, parent, main_nb):
        side = tk.Frame(parent, bg=THEME["bg_card"], width=228,
                        highlightbackground=THEME["border"], highlightthickness=1)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        top = tk.Frame(side, bg=THEME["bg_card"])
        top.pack(fill="x", padx=14, pady=(16, 10))
        tk.Label(top, text="NAVIGATION", bg=THEME["bg_card"], fg=THEME["text_muted"],
                 font=("Cascadia Code", 8, "bold")).pack(anchor="w")

        nav = tk.Frame(side, bg=THEME["bg_card"])
        nav.pack(fill="x", padx=8)
        items = [
            (lang.t("tab_main"), "⌂", 0),
            (lang.t("tab_logs"), "▤", 1),
            (lang.t("tab_db"), "▦", 2),
            (lang.t("tab_projects"), "□", 3),
            (lang.t("tab_monitor"), "⌁", 4),
            (lang.t("tab_settings"), "⚙", 5),
        ]
        self._sidebar_buttons = []
        def select(idx):
            main_nb.select(idx)
            for i, b in enumerate(self._sidebar_buttons):
                self._style_nav_button(b, i == idx)
            self._sidebar_active = idx
        for label, icon, idx in items:
            b = self._nav_button(nav, label, icon, lambda i=idx: select(i), active=(idx == 0))
            self._sidebar_buttons.append(b)

        spacer = tk.Frame(side, bg=THEME["bg_card"])
        spacer.pack(fill="both", expand=True)
        server = tk.Frame(side, bg=THEME["bg_elevated"], highlightbackground=THEME["border"], highlightthickness=1)
        server.pack(fill="x", padx=14, pady=14)
        tk.Label(server, text="●", bg=THEME["bg_elevated"], fg=THEME["success"],
                 font=(THEME["font_family"], 14)).pack(side="left", padx=(10, 6), pady=10)
        sb = tk.Frame(server, bg=THEME["bg_elevated"]); sb.pack(side="left", pady=8)
        tk.Label(sb, text="FarajaWebServer", bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 8, "bold")).pack(anchor="w")
        tk.Label(sb, text="LOCAL • READY", bg=THEME["bg_elevated"], fg=THEME["text_muted"],
                 font=("Cascadia Code", 7)).pack(anchor="w", pady=(2,0))

    def _style_nav_button(self, btn, active):
        bg = THEME["accent"] if active else THEME["bg_card"]
        fg = THEME["white"] if active else THEME["text_dim"]
        btn.configure(bg=bg)
        for child in btn.winfo_children():
            try:
                child.configure(bg=bg)
                if isinstance(child, tk.Label):
                    if child.cget("text") in ("⌂", "▤", "▦", "□", "⌁", "⚙"):
                        child.configure(fg=THEME["white"] if active else THEME["accent"])
                    elif child.cget("text") == "›":
                        child.configure(fg=THEME["white"] if active else bg)
                    else:
                        child.configure(fg=fg)
            except Exception:
                pass
        try:
            btn.winfo_children()[0].configure(bg=THEME["accent"] if active else bg)
        except Exception:
            pass

    def _settings_header(self, parent):
        head = tk.Frame(parent, bg=THEME["bg"])
        head.pack(fill="x", padx=20, pady=(18, 12))
        icon = tk.Frame(head, bg=THEME["accent"], width=42, height=42)
        icon.pack(side="left"); icon.pack_propagate(False)
        tk.Label(icon, text="⚙", bg=THEME["accent"], fg=THEME["white"],
                 font=("Segoe UI Emoji", 19)).pack(expand=True)
        text = tk.Frame(head, bg=THEME["bg"]); text.pack(side="left", padx=12)
        tk.Label(text, text=lang.t("tab_settings"), bg=THEME["bg"], fg=THEME["text"],
                 font=(THEME["font_family"], 18, "bold")).pack(anchor="w")
        tk.Label(text, text="Управление сервером, окружением и конфигурацией", bg=THEME["bg"],
                 fg=THEME["text_dim"], font=(THEME["font_family"], 9)).pack(anchor="w", pady=(2,0))

    def _settings_card(self, parent, title, subtitle, icon="⚙"):
        card = tk.Frame(parent, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))
        top = tk.Frame(card, bg=THEME["bg_card"]); top.pack(fill="x", padx=14, pady=(12, 8))
        ic = tk.Frame(top, bg=THEME["bg_elevated"], width=34, height=34); ic.pack(side="left"); ic.pack_propagate(False)
        tk.Label(ic, text=icon, bg=THEME["bg_elevated"], fg=THEME["accent"], font=("Segoe UI Emoji", 14)).pack(expand=True)
        tb = tk.Frame(top, bg=THEME["bg_card"]); tb.pack(side="left", padx=10)
        tk.Label(tb, text=title, bg=THEME["bg_card"], fg=THEME["text"], font=(THEME["font_family"], 10, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(tb, text=subtitle, bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"], 8)).pack(anchor="w", pady=(2,0))
        body = tk.Frame(card, bg=THEME["bg_card"]); body.pack(fill="x", padx=14, pady=(0, 14))
        return card, body

    def _modern_settings_field(self, parent, label, variable, width=None, row=0, col=0, colspan=1):
        box = tk.Frame(parent, bg=THEME["bg_card"])
        box.grid(row=row, column=col, columnspan=colspan, sticky="ew", padx=5, pady=5)
        tk.Label(box, text=label, bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"], 8)).pack(anchor="w", pady=(0,4))
        e = tk.Entry(box, textvariable=variable, bg=THEME["bg_input"], fg=THEME["text"], insertbackground=THEME["text"],
                     font=("Cascadia Code", 9), relief="flat", bd=0, highlightthickness=1,
                     highlightbackground=THEME["border"], highlightcolor=THEME["accent"])
        if width: e.configure(width=width)
        e.pack(fill="x", ipady=7)
        return e

    def build(self):
        self._header(self.root)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TNotebook", background=THEME["bg"], borderwidth=0)
        style.configure("Modern.Horizontal.TProgressbar", troughcolor=THEME["bg_input"], background=THEME["accent"],
                        bordercolor=THEME["bg_input"], lightcolor=THEME["accent"], darkcolor=THEME["accent"], thickness=6)
        style.configure("Big.Treeview", background=THEME["bg_elevated"], fieldbackground=THEME["bg_elevated"],
                        foreground=THEME["text"], font=(THEME["font_family"], 10), rowheight=34, borderwidth=0)
        style.map("Big.Treeview", background=[("selected", THEME["accent"])], foreground=[("selected", THEME["white"])])
        style.configure("Big.Treeview.Heading", background=THEME["bg_card"], foreground=THEME["text_dim"],
                        font=(THEME["font_family"], 8, "bold"), relief="flat", padding=[8,8])
        style.configure("Vertical.TScrollbar", background=THEME["bg_input"], troughcolor=THEME["bg"],
                        arrowcolor=THEME["text_dim"], borderwidth=0, relief="flat")

        workspace = tk.Frame(self.root, bg=THEME["bg"])
        workspace.pack(fill="both", expand=True)
        main_nb = OfficeTabs(workspace, active_size=12, passive_size=9)
        main_nb.hide_header()

        tab1 = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab1, lang.t('tab_main'))
        self._page_header(tab1, lang.t("tab_main"),
                          PAGE_SUBTITLES["main"].get(lang.get(), PAGE_SUBTITLES["main"]["en"]), "⌂")
        main_shell = self._page_body(tab1)
        services_outer = tk.Frame(main_shell, bg=THEME["bg_card"])
        services_outer.pack(fill="both", expand=True, padx=6, pady=6)
        services_frame = self._scrollable(services_outer, bg=THEME["bg_card"])
        services_frame.grid_columnconfigure(0, weight=1); services_frame.grid_columnconfigure(1, weight=1)
        self._service_row, self._service_col = 0, 0
        self._service_card(services_frame, "apache", "🪶", "apache", self.start_a, self.stop_a, self.restart_a)
        self._service_card(services_frame, "mariadb", "🗄️", "db", self.start_d, self.stop_d, self.restart_d)
        self._service_card(services_frame, "php", "📜", "php", self.start_p, self.stop_p, self.restart_p)
        self._service_card(services_frame, "postgresql", "🐘", "pg", self.start_pg_ui, self.stop_pg_ui, self.restart_pg)
        self._service_card(services_frame, "redis", "⚡", "redis", self.start_redis_ui, self.stop_redis_ui, self.restart_redis)
        self._service_card(services_frame, "nginx", "🔀", "nginx", self.start_nginx_ui, self.stop_nginx_ui, self.restart_nginx)
        self._service_card(services_frame, "docker", "🐳", "docker", self.start_docker_ui, self.stop_docker_ui)
        self._service_card(services_frame, "nodejs", "🟢", "node", self.start_node_ui, self.stop_node_ui)
        self._action_bar(main_shell)

        tab_logs = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab_logs, lang.t('tab_logs')); self._log_tabs(tab_logs)
        tab_data = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab_data, lang.t('tab_db')); self._data_tabs(tab_data)
        tab_projects = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab_projects, lang.t('tab_projects')); self._projects_tabs(tab_projects)
        tab_monitor = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab_monitor, lang.t('tab_monitor')); self._monitor_tabs(tab_monitor)
        tab_settings = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab_settings, lang.t('tab_settings')); self._build_settings(self._scrollable(tab_settings, bg=THEME["bg"]))

        self._build_sidebar(workspace, main_nb)
        main_nb.body.pack_configure(side="right", fill="both", expand=True)
        # body was already packed by OfficeTabs; sidebar is added after it, so move it to the right explicitly.
        try:
            main_nb.body.lift()
        except Exception:
            pass
        self._status_bar(self.root)
        self.svc.ui_progress = self._install_progress
        self._sidebar_active = 0


    def context(self, t):
        menu = tk.Menu(t, tearoff=False, bg=THEME["bg_elevated"], fg=THEME["text"],
                       activebackground=THEME["accent"], activeforeground=THEME["white"],
                       font=(THEME["font_family"], 9), relief="flat", bd=1)
        menu.add_command(label="Copy selection", command=lambda: self.copy(t))
        menu.add_command(label="Copy all", command=lambda: self.copyall(t))
        t.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _build_file_manager(self, parent):
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        IconButton(top, "refresh", self._fm_refresh, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_refresh") + " — " + lang.t("tip_refresh")).pack(side="left", padx=2)
        IconButton(top, "folder_plus", self._fm_mkdir, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_new_folder") + " — " + lang.t("tip_add")).pack(side="left", padx=2)
        IconButton(top, "doc_plus", self._fm_newfile, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_new_file") + " — " + lang.t("tip_add")).pack(side="left", padx=2)
        IconButton(top, "pencil", self._fm_edit, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     size=30, tip=lang.t("btn_edit")).pack(side="left", padx=2)
        IconButton(top, "cross", self._fm_delete, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("btn_delete") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        IconButton(top, "copy", self._fm_copy, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("donate_copy")).pack(side="left", padx=2)
        IconButton(top, "paste", self._fm_paste, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_paste")).pack(side="left", padx=2)
        self._fm_path = tk.StringVar(value=str(WWW))
        self._fm_clip = {"op": None, "paths": []}
        path_entry = tk.Entry(top, textvariable=self._fm_path, bg=THEME["entry_bg"],
                              fg=THEME["entry_fg"], insertbackground=THEME["entry_fg"],
                              font=("Cascadia Code", 9), relief="flat", bd=0)
        path_entry.pack(side="left", fill="x", expand=True, padx=5)
        path_entry.bind("<Return>", lambda e: self._fm_navigate())

        tree_frame = tk.Frame(parent, bg=THEME["bg_elevated"])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        cols = ("type", "name", "size", "modified")
        self._fm_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14,
                                     style="Big.Treeview")
        self._fm_tree.heading("type", text="")
        self._fm_tree.heading("name", text="Name")
        self._fm_tree.heading("size", text="Size")
        self._fm_tree.heading("modified", text="Modified")
        self._fm_tree.column("type", width=48, stretch=False)
        self._fm_tree.column("name", width=320)
        self._fm_tree.column("size", width=90)
        self._fm_tree.column("modified", width=130)
        self._fm_tree.pack(fill="both", expand=True)
        self._fm_tree.bind("<Double-1>", self._fm_open)
        self._fm_tree.bind("<Button-3>", self._fm_menu)
        self._fm_tree.bind("<Control-c>", lambda e: (self._fm_copy(), "break"))
        self._fm_tree.bind("<Control-x>", lambda e: (self._fm_cut(), "break"))
        self._fm_tree.bind("<Control-v>", lambda e: (self._fm_paste(), "break"))
        self._fm_tree.bind("<Delete>", lambda e: (self._fm_delete(), "break"))
        self._fm_tree.bind("<F2>", lambda e: (self._fm_rename(), "break"))
        self._fm_tree.bind("<F5>", lambda e: (self._fm_refresh(), "break"))
        self._fm_refresh()

    def _fm_sel_path(self):
        sel = self._fm_tree.selection()
        if not sel:
            return None
        item = Path(sel[0])
        if item.name == "..":
            return None
        return item

    def _fm_menu(self, event):
        item = self._fm_tree.identify_row(event.y)
        if item:
            self._fm_tree.selection_set(item)
        menu = tk.Menu(self.root, tearoff=False, bg=THEME["bg_elevated"], fg=THEME["text"],
                       activebackground=THEME["accent"], activeforeground=THEME["white"],
                       font=(THEME["font_family"], 9), relief="flat", bd=1)
        menu.add_command(label=lang.t("btn_open"),
                         command=lambda: self._fm_open(None))
        menu.add_command(label=lang.t("btn_edit"), command=self._fm_edit)
        menu.add_command(label=lang.t("btn_rename"), command=self._fm_rename)
        menu.add_separator()
        menu.add_command(label=lang.t("donate_copy"), command=self._fm_copy)
        menu.add_command(label=lang.t("btn_cut"), command=self._fm_cut)
        menu.add_command(label=lang.t("btn_paste"), command=self._fm_paste)
        menu.add_separator()
        menu.add_command(label=lang.t("btn_delete"), command=self._fm_delete)
        menu.add_command(label=lang.t("btn_refresh"), command=self._fm_refresh)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _fm_copy(self):
        item = self._fm_sel_path()
        if not item:
            return
        self._fm_clip = {"op": "copy", "paths": [item]}
        self.log(f"Copy: {item.name}")

    def _fm_cut(self):
        item = self._fm_sel_path()
        if not item:
            return
        self._fm_clip = {"op": "cut", "paths": [item]}
        self.log(f"Cut: {item.name}")

    def _fm_unique(self, dest):
        if not dest.exists():
            return dest
        stem = dest.stem + " - copy"
        cand = dest.with_name(stem + dest.suffix)
        i = 2
        while cand.exists():
            cand = dest.with_name(f"{dest.stem} - copy ({i}){dest.suffix}")
            i += 1
        return cand

    def _fm_paste(self):
        op, paths = self._fm_clip.get("op"), self._fm_clip.get("paths", [])
        if not op or not paths:
            return
        dest_dir = Path(self._fm_path.get())
        if not dest_dir.is_dir():
            return
        for src in paths:
            try:
                if not src.exists():
                    continue
                if op == "cut" and src.resolve().parent == dest_dir.resolve():
                    continue
                target = self._fm_unique(dest_dir / src.name)
                if src.is_dir():
                    if op == "copy":
                        shutil.copytree(src, target)
                    else:
                        shutil.move(str(src), str(target))
                else:
                    if op == "copy":
                        shutil.copy2(src, target)
                    else:
                        shutil.move(str(src), str(target))
                self.log(f"Pasted: {target.name}")
            except Exception as e:
                self.log(f"Paste ERROR: {e}")
        if op == "cut":
            self._fm_clip = {"op": None, "paths": []}
        self._fm_refresh()

    def _fm_rename(self):
        item = self._fm_sel_path()
        if not item:
            return
        name = DarkPrompt.ask_string(self.root, lang.t("btn_rename"), item.name, initial=item.name)
        if not name or name == item.name:
            return
        try:
            item.rename(item.parent / name)
            self._fm_refresh()
        except Exception as e:
            messagebox.showerror(lang.t("error"), str(e))

    def _fm_refresh(self):
        for item in self._fm_tree.get_children():
            self._fm_tree.delete(item)
        path = Path(self._fm_path.get())
        if not path.exists():
            return
        try:
            parent_up = path.parent
            self._fm_tree.insert("", "end", values=("", "..", "<DIR>", ""),
                                 iid=str(parent_up))
        except Exception:
            pass
        for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            try:
                st = item.stat()
                is_dir = item.is_dir()
                icon = "\U0001F4C1" if is_dir else self._fm_file_icon(item.name)
                size = "<DIR>" if is_dir else f"{st.st_size / 1024:.1f} KB"
                mod = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
                self._fm_tree.insert("", "end", values=(icon, item.name, size, mod), iid=str(item))
            except Exception:
                pass

    def _fm_file_icon(self, name):
        ext = Path(name).suffix.lower()
        icons = {
            ".html": "\U0001F4DC", ".htm": "\U0001F4DC",
            ".css": "\U0001F3A8", ".js": "\u26A1", ".ts": "\u26A1",
            ".json": "{ }", ".xml": "\U0001F4C4",
            ".php": "\U0001F40D", ".py": "\U0001F40D",
            ".jpg": "\U0001F5BC", ".jpeg": "\U0001F5BC", ".png": "\U0001F5BC",
            ".gif": "\U0001F5BC", ".svg": "\U0001F5BC", ".ico": "\U0001F5BC",
            ".md": "\U0001F4DD", ".txt": "\U0001F4DD",
            ".sql": "\U0001F5C3", ".ini": "\u2699", ".conf": "\u2699",
            ".zip": "\U0001F4E6", ".log": "\U0001F4CB",
        }
        return icons.get(ext, "\U0001F4C4")

    def _fm_navigate(self):
        path = Path(self._fm_path.get())
        if path.is_dir():
            self._fm_refresh()

    def _fm_open(self, event):
        sel = self._fm_tree.selection()
        if not sel:
            return
        item = Path(sel[0])
        if item.is_dir():
            self._fm_path.set(str(item))
            self._fm_refresh()
        else:
            os.startfile(str(item))

    def _fm_mkdir(self):
        name = DarkPrompt.ask_string(self.root, lang.t("btn_new_folder"), lang.t("folder_name"))
        if name:
            Path(self._fm_path.get(), name).mkdir(exist_ok=True)
            self._fm_refresh()

    def _fm_delete(self):
        sel = self._fm_tree.selection()
        if not sel:
            return
        item = Path(sel[0])
        if item.name == "..":
            return
        if DarkPrompt.ask_yes_no(self.root, lang.t("btn_delete"), f"{lang.t('confirm_delete')} {item.name}?"):
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
            self._fm_refresh()

    def _fm_newfile(self):
        name = DarkPrompt.ask_string(self.root, lang.t("btn_new_file"), lang.t("file_name"))
        if not name:
            return
        path = Path(self._fm_path.get()) / name
        if path.exists():
            messagebox.showerror("Error", "File already exists")
            return
        template = ""
        ext = path.suffix.lower()
        if ext in (".html", ".htm"):
            template = f"<html>\n<head><title>{name}</title></head>\n<body>\n\n</body>\n</html>"
        elif ext == ".css":
            template = "body {\n    margin: 0;\n    padding: 0;\n}\n"
        elif ext in (".js", ".ts"):
            template = "console.log('Hello');\n"
        elif ext == ".php":
            template = "<?php\n\n?>\n"
        elif ext == ".json":
            template = "{}\n"
        path.write_text(template, encoding="utf-8")
        self._fm_refresh()
        self._fm_edit_file(path)

    def _fm_edit(self):
        sel = self._fm_tree.selection()
        if not sel:
            return
        item = Path(sel[0])
        if item.is_dir() or item.name == "..":
            return
        self._fm_edit_file(item)

    def _fm_edit_file(self, filepath):
        CodeEditor(self.root, filepath, save_callback=self._fm_refresh)

    def _fm_save(self, editor, filepath, text_widget):
        try:
            content = text_widget.get("1.0", "end-1c")
            filepath.write_text(content, encoding="utf-8")
            self.log(f"Saved: {filepath.name}")
            editor.title(f"Edit: {filepath.name} [Saved]")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _build_sql_editor(self, parent):
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        tk.Label(top, text=lang.t("sql_engine"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        self._sql_engine = tk.StringVar(value="MariaDB")
        engine_menu = tk.OptionMenu(top, self._sql_engine, "MariaDB", "PostgreSQL")
        engine_menu.configure(bg=THEME["entry_bg"], fg=THEME["entry_fg"], relief="flat",
                             activebackground=THEME["accent"], activeforeground=THEME["white"],
                             font=(THEME["font_family"], 9))
        engine_menu["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
        engine_menu.pack(side="left", padx=5)
        self._sql_user = tk.StringVar(value="root")
        self._sql_pass = tk.StringVar(value="")
        tk.Label(top, text=lang.t("sql_user"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(10, 2))
        tk.Entry(top, textvariable=self._sql_user, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9), width=10,
                 relief="flat", bd=0).pack(side="left", padx=2)
        tk.Label(top, text=lang.t("sql_pass"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(10, 2))
        tk.Entry(top, textvariable=self._sql_pass, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9), width=10,
                 relief="flat", bd=0, show="*").pack(side="left", padx=2)

        paned = tk.PanedWindow(parent, orient="horizontal", bg=THEME["bg"],
                               sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=10, pady=5)

        left = tk.Frame(paned, bg=THEME["bg"])
        right = tk.Frame(paned, bg=THEME["bg"])
        paned.add(left, minsize=300)
        paned.add(right, minsize=300)

        lbl_left = tk.Label(left, text=lang.t("sql_editor"), bg=THEME["bg"], fg=THEME["text_dim"],
                            font=(THEME["font_family"], 8, "bold"), anchor="w")
        lbl_left.pack(fill="x", padx=5, pady=(0, 2))

        self._sql_editor = ScrolledText(left, wrap="word", bg="#0d0f16", fg="#b8bdd0",
                                        insertbackground="white", font=("Cascadia Code", 10),
                                        relief="flat", bd=0, padx=10, pady=6,
                                        selectbackground=THEME["accent"], selectforeground=THEME["white"])
        self._sql_editor.pack(fill="both", expand=True)

        btn_frame = tk.Frame(left, bg=THEME["bg"], height=34)
        btn_frame.pack(fill="x", pady=(6, 4))
        btn_frame.pack_propagate(False)
        IconButton(btn_frame, "play", self._sql_execute, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     size=30, tip=lang.t("btn_execute") + " — " + lang.t("tip_run")).pack(side="left", padx=3)
        IconButton(btn_frame, "trash", lambda: self._sql_editor.delete("1.0", "end"),
                     color=THEME["bg_input"], hover_color=THEME["border_light"],
                     active_color=THEME["border"], size=30,
                     tip=lang.t("btn_clear") + " — " + lang.t("tip_clear")).pack(side="left", padx=3)

        lbl_right = tk.Label(right, text=lang.t("sql_results"), bg=THEME["bg"], fg=THEME["text_dim"],
                             font=(THEME["font_family"], 8, "bold"), anchor="w")
        lbl_right.pack(fill="x", padx=5, pady=(0, 2))

        result_container = tk.Frame(right, bg="white")
        result_container.pack(fill="both", expand=True)

        self._sql_result = ttk.Treeview(result_container, columns=("col1",), show="headings")
        style = ttk.Style()
        style.configure("White.Treeview", background="white", fieldbackground="white",
                        foreground="black", font=("Cascadia Code", 9))
        self._sql_result.configure(style="White.Treeview")
        self._sql_result.pack(fill="both", expand=True)

        self._sql_status = tk.Label(right, text="", bg=THEME["bg"], fg=THEME["text_muted"],
                                    font=(THEME["font_family"], 8), anchor="w")
        self._sql_status.pack(fill="x", padx=5, pady=(2, 0))

    def _sql_execute(self):
        query = self._sql_editor.get("1.0", "end-1c").strip()
        if not query:
            return
        engine = self._sql_engine.get()
        user = self._sql_user.get()
        passwd = self._sql_pass.get()
        def run():
            try:
                if engine == "MariaDB":
                    mysql = RUNTIME / "MariaDB" / "bin" / "mysql.exe"
                    if not mysql.exists():
                        raise RuntimeError("MariaDB mysql.exe not found")
                    cmd = [str(mysql), "-u", user, "--port", str(CONFIG["mariadb_port"])]
                    if passwd:
                        cmd.extend(["-p" + passwd])
                    cmd.extend(["-e", query])
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                elif engine == "PostgreSQL":
                    psql = RUNTIME / "PostgreSQL" / "bin" / "psql.exe"
                    if not psql.exists():
                        raise RuntimeError("PostgreSQL psql.exe not found")
                    env = os.environ.copy()
                    if passwd:
                        env["PGPASSWORD"] = passwd
                    cmd = [str(psql), "-U", user, "-p", str(CONFIG["postgresql_port"]),
                           "-d", "postgres", "-c", query]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                           env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0:
                    self.root.after(0, lambda: self._sql_status.configure(
                        text="ERROR: " + result.stderr.strip()[:200], fg=THEME["danger"]))
                    return
                output = result.stdout.strip()
                lines = output.split("\n")
                for item in self._sql_result.get_children():
                    self._sql_result.delete(item)
                self._sql_result["columns"] = ()
                if lines:
                    headers = lines[0].split("\t")
                    self._sql_result["columns"] = tuple(f"col{i}" for i in range(len(headers)))
                    for i, h in enumerate(headers):
                        self._sql_result.heading(f"col{i}", text=h)
                    for line in lines[1:]:
                        if line.strip():
                            cols = line.split("\t")
                            self._sql_result.insert("", "end", values=cols)
                self.root.after(0, lambda: self._sql_status.configure(
                    text=f"OK: {len(lines)-1} rows returned", fg=THEME["success"]))
            except Exception as e:
                self.root.after(0, lambda: self._sql_status.configure(
                    text="ERROR: " + str(e)[:200], fg=THEME["danger"]))
        threading.Thread(target=run, daemon=True).start()

    def _build_sites_manager(self, parent):
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        IconButton(top, "plus", self._site_add, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     size=30, tip=lang.t("btn_add_site") + " — " + lang.t("tip_add")).pack(side="left", padx=2)
        IconButton(top, "globe", self._site_launch, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     size=30, tip=lang.t("btn_open_site") + " — " + lang.t("tip_open")).pack(side="left", padx=2)
        IconButton(top, "cross", self._site_remove, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        IconButton(top, "folder", self._site_open, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=30, tip=lang.t("btn_open_folder") + " — " + lang.t("tip_open")).pack(side="left", padx=2)
        cols = ("name", "domain", "root", "port", "type", "https")
        self._site_tree = ttk.Treeview(parent, columns=cols, show="headings", height=10,
                                       style="Big.Treeview")
        self._site_tree.heading("name", text=lang.t("col_site"))
        self._site_tree.heading("domain", text=lang.t("col_domain"))
        self._site_tree.heading("root", text=lang.t("col_root"))
        self._site_tree.heading("port", text=lang.t("col_port"))
        self._site_tree.heading("type", text=lang.t("col_type"))
        self._site_tree.heading("https", text=lang.t("col_https"))
        self._site_tree.column("name", width=110)
        self._site_tree.column("domain", width=160)
        self._site_tree.column("root", width=180)
        self._site_tree.column("port", width=60)
        self._site_tree.column("type", width=70)
        self._site_tree.column("https", width=60)
        self._site_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self._sites_file = APP_ROOT / "config" / "sites.json"
        self._load_sites()

    def _load_sites(self):
        if self._sites_file.exists():
            try:
                self._sites = json.loads(self._sites_file.read_text(encoding="utf-8"))
            except Exception:
                self._sites = []
        else:
            self._sites = []
        for item in self._site_tree.get_children():
            self._site_tree.delete(item)
        for s in self._sites:
            self._site_tree.insert("", "end", values=(s.get("name",""), s.get("domain",""),
                                                       s.get("root",""), s.get("port",""),
                                                       s.get("type","php"),
                                                       "✓" if s.get("https") else "—"))
        self.svc.set_sites(self._sites)

    def _refresh_web_servers(self):
        def w():
            try:
                if self.svc.arun():
                    self.svc.stop_apache()
                    self.svc.start_apache()
                if self.svc.nginxrun():
                    self.svc.stop_nginx()
                    self.svc.start_nginx()
            except Exception as e:
                self.log("Web servers refresh ERROR: " + str(e))
        threading.Thread(target=w, daemon=True).start()

    def _site_add(self):
        name = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_name"))
        if not name:
            return
        domain = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_domain"),
                                       initial=f"{name}.localhost")
        if domain is None:
            return
        try:
            self.svc.check_domain(domain)
        except RuntimeError as e:
            messagebox.showerror(lang.t("error"), str(e))
            return
        typ = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_type"),
                                    initial="php")
        if typ is None:
            return
        typ = (typ.strip().lower() or "php")
        if typ not in ("php", "node", "python", "static"):
            typ = "php"
        pyver = ""
        if typ == "python":
            try:
                default_py = self.svc.env_active()[2] or "3.12"
            except Exception:
                default_py = "3.12"
            pyver = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_pyver"),
                                          initial=default_py)
            if pyver is None:
                return
            pyver = (pyver.strip() or default_py)
        phpver = ""
        if typ == "php":
            try:
                default_php = self.svc.default_php_ver()
            except Exception:
                default_php = "8.3"
            phpver = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_phpver"),
                                           initial="")
            if phpver is None:
                return
            phpver = phpver.strip()
            if phpver and phpver != default_php and phpver not in ("8.2", "8.3", "8.4"):
                messagebox.showerror(lang.t("error"), phpver)
                return
        https = DarkPrompt.ask_yes_no(self.root, lang.t("btn_add_site"), lang.t("site_https_q"))
        port = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_port"))
        if port is None:
            return
        site_root = WWW / name
        site_root.mkdir(parents=True, exist_ok=True)
        index = site_root / "index.html"
        if not index.exists():
            index.write_text(f"<html><body><h1>{name}</h1></body></html>", encoding="utf-8")
        self._sites.append({"name": name, "domain": domain, "root": str(site_root),
                            "port": port, "type": typ, "https": https, "pyver": pyver,
                            "phpver": phpver})
        self._sites_file.write_text(json.dumps(self._sites, indent=2), encoding="utf-8")
        self.svc.set_sites(self._sites)
        self._load_sites()
        self.log(f"Site added: {name} -> {domain} [{typ}{' +HTTPS' if https else ''}]")
        def w():
            try:
                if https:
                    try:
                        self.svc.mkcert_domain(domain)
                    except Exception as e:
                        self.log(f"SSL {domain} ERROR: {e} — HTTPS disabled for this site")
                        for s in self._sites:
                            if s.get("name") == name:
                                s["https"] = False
                        try:
                            self._sites_file.write_text(json.dumps(self._sites, indent=2), encoding="utf-8")
                            self.svc.set_sites(self._sites)
                            self.root.after(0, self._load_sites)
                        except Exception:
                            pass
                if typ == "php" and phpver:
                    try:
                        self.svc.ensure_site_php(phpver)
                    except Exception as e:
                        self.log(f"Site PHP {phpver} ERROR: {e}")
                self.svc.write_configs()
                self.svc._write_nginx_conf()
                try:
                    if hosts_add(domain):
                        self.log(f"hosts: 127.0.0.1 {domain}")
                except PermissionError:
                    self.log("hosts ERROR: " + lang.t("site_hosts_admin"))
                    self.root.after(0, lambda: messagebox.showerror(lang.t("error"), lang.t("site_hosts_admin")))
                except Exception as e:
                    self.log(f"hosts ERROR: {e}")
            except Exception as e:
                self.log("Site provision ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
                return
            self.root.after(0, self._refresh_web_servers)
        threading.Thread(target=w, daemon=True).start()

    def _site_remove(self):
        sel = self._site_tree.selection()
        if not sel:
            return
        vals = self._site_tree.item(sel[0], "values")
        name = vals[0]
        domain = vals[1] if len(vals) > 1 else ""
        if DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"), lang.t("confirm_delete_site", name=name)):
            self._sites = [s for s in self._sites if s.get("name") != name]
            self._sites_file.write_text(json.dumps(self._sites, indent=2), encoding="utf-8")
            self.svc.set_sites(self._sites)
            self._load_sites()
            def w():
                try:
                    self.svc.write_configs()
                    self.svc._write_nginx_conf()
                    try:
                        if domain and hosts_remove(domain):
                            self.log(f"hosts: removed {domain}")
                    except Exception as e:
                        self.log(f"hosts ERROR: {e}")
                except Exception as e:
                    self.log("Site remove ERROR: " + str(e))
                    return
                self.root.after(0, self._refresh_web_servers)
            threading.Thread(target=w, daemon=True).start()

    def _site_open(self):
        sel = self._site_tree.selection()
        if sel:
            vals = self._site_tree.item(sel[0], "values")
            root = vals[2]
            if Path(root).exists():
                os.startfile(root)

    def _site_launch(self):
        sel = self._site_tree.selection()
        if not sel:
            return
        vals = self._site_tree.item(sel[0], "values")
        name, domain, port = vals[0], vals[1], vals[3]
        typ = vals[4] if len(vals) > 4 else "php"
        https = len(vals) > 5 and vals[5] not in ("", "—")

        def _local(d):
            try:
                return socket.gethostbyname(d) in ("127.0.0.1", "::1")
            except Exception:
                return False

        use_domain = bool(domain and "." in domain and _local(domain))
        fallback = (f"http://127.0.0.1:{port}/" if port
                    else f"http://127.0.0.1:{CONFIG['apache_port']}/{name}/")
        if https and domain and "." in domain:
            if use_domain:
                url = f"https://{domain}/"
            else:
                self.log(lang.t("site_no_hosts", domain=domain))
                url = fallback
        elif use_domain and typ in ("node", "python") and self.svc.nginxrun():
            url = f"http://{domain}/"
        elif use_domain and typ in ("php", "static"):
            url = f"http://{domain}:{CONFIG['apache_port']}/"
        else:
            url = fallback
        self.log(f"Opening site: {url}")
        webbrowser.open(url)

    def _build_task_scheduler(self, parent):
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        IconButton(top, "plus", self._task_add, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     size=30, tip=lang.t("btn_add_task") + " — " + lang.t("tip_add")).pack(side="left", padx=2)
        IconButton(top, "cross", self._task_remove, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     size=30, tip=lang.t("btn_remove") + " — " + lang.t("tip_remove")).pack(side="left", padx=2)
        IconButton(top, "play", self._task_run, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     size=30, tip=lang.t("btn_run_now") + " — " + lang.t("tip_run")).pack(side="left", padx=2)
        cols = ("name", "schedule", "command", "status")
        self._task_tree = ttk.Treeview(parent, columns=cols, show="headings", height=10,
                                        style="Big.Treeview")
        self._task_tree.heading("name", text=lang.t("col_task"))
        self._task_tree.heading("schedule", text=lang.t("col_schedule"))
        self._task_tree.heading("command", text=lang.t("col_command"))
        self._task_tree.heading("status", text=lang.t("col_status"))
        self._task_tree.column("name", width=120)
        self._task_tree.column("schedule", width=120)
        self._task_tree.column("command", width=250)
        self._task_tree.column("status", width=80)
        self._task_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self._tasks_file = APP_ROOT / "config" / "tasks.json"
        self._load_tasks()

    def _load_tasks(self):
        if self._tasks_file.exists():
            try:
                self._tasks = json.loads(self._tasks_file.read_text(encoding="utf-8"))
            except Exception:
                self._tasks = []
        else:
            self._tasks = []
        for item in self._task_tree.get_children():
            self._task_tree.delete(item)
        for t in self._tasks:
            self._task_tree.insert("", "end", values=(t.get("name",""), t.get("schedule",""),
                                                       t.get("command",""), t.get("status","Idle")))

    def _task_add(self):
        name = DarkPrompt.ask_string(self.root, lang.t("btn_add_task"), lang.t("task_name"))
        if not name:
            return
        cmd = DarkPrompt.ask_string(self.root, lang.t("btn_add_task"), lang.t("task_command"))
        if not cmd:
            return
        schedule = DarkPrompt.ask_string(self.root, lang.t("btn_add_task"), lang.t("task_schedule"),
                                         initial="manual")
        if schedule is None:
            return
        self._tasks.append({"name": name, "schedule": schedule, "command": cmd, "status": "Idle"})
        self._tasks_file.write_text(json.dumps(self._tasks, indent=2), encoding="utf-8")
        self._load_tasks()
        self.log(f"Task added: {name}")

    def _task_remove(self):
        sel = self._task_tree.selection()
        if not sel:
            return
        vals = self._task_tree.item(sel[0], "values")
        name = vals[0]
        if DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"), lang.t("confirm_delete_task", name=name)):
            self._tasks = [t for t in self._tasks if t.get("name") != name]
            self._tasks_file.write_text(json.dumps(self._tasks, indent=2), encoding="utf-8")
            self._load_tasks()

    def _task_run(self):
        sel = self._task_tree.selection()
        if not sel:
            return
        vals = self._task_tree.item(sel[0], "values")
        name, cmd = vals[0], vals[2]
        def run():
            try:
                self.log(f"Running task: {name}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                output = result.stdout + result.stderr
                self.log(f"Task {name} completed: {output.strip()[:200]}")
            except Exception as e:
                self.log(f"Task {name} failed: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _save_settings(self):
        try:
            (APP_ROOT / "config").mkdir(parents=True, exist_ok=True)
            (APP_ROOT / "config" / "settings.json").write_text(
                json.dumps(getattr(self, "_settings", {}), indent=2), encoding="utf-8")
        except Exception:
            pass

    def _build_settings(self, parent):
        global DOWNLOADS
        self._settings = {}
        try:
            self._settings = json.loads((APP_ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
        except Exception:
            self._settings = {}
        try:
            p = Path(self._settings.get("downloads", str(DOWNLOADS)))
            if p.is_dir(): DOWNLOADS = p
        except Exception:
            pass

        self._settings_header(parent)
        content = tk.Frame(parent, bg=THEME["bg"])
        content.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)

        left = tk.Frame(content, bg=THEME["bg"]); left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right = tk.Frame(content, bg=THEME["bg"]); right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        _, body = self._settings_card(left, lang.t("set_modules"), "Рабочие каталоги и локальные архивы", "▣")
        body.grid_columnconfigure(0, weight=1)
        tk.Label(body, text=lang.t("set_dl_folder"), bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"], 8)).grid(row=0, column=0, sticky="w", padx=5, pady=(2,4))
        self._set_dl_var = tk.StringVar(value=str(DOWNLOADS))
        e = tk.Entry(body, textvariable=self._set_dl_var, bg=THEME["bg_input"], fg=THEME["text"], insertbackground=THEME["text"],
                     font=("Cascadia Code", 9), relief="flat", bd=0, highlightthickness=1,
                     highlightbackground=THEME["border"], highlightcolor=THEME["accent"])
        e.grid(row=1, column=0, sticky="ew", padx=5, pady=(0,5), ipady=7)
        actions = tk.Frame(body, bg=THEME["bg_card"]); actions.grid(row=1, column=1, padx=(5,0))
        IconButton(actions, "folder", self._set_browse_dl, color=THEME["accent"], hover_color=THEME["accent_hover"], active_color=THEME["accent_active"], size=30, tip=lang.t("first_run_browse")).pack(side="left", padx=2)
        IconButton(actions, "folder", self._set_open_dl, color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"], size=30, tip=lang.t("set_open_folder")).pack(side="left", padx=2)
        IconButton(actions, "refresh", self._set_refresh, color=THEME["info"], hover_color="#2e9bf5", active_color="#0769b5", size=30, tip=lang.t("set_rescan")).pack(side="left", padx=2)

        _, body = self._settings_card(left, lang.t("set_logs"), "Настройки отображения журнала", "≡")
        row = tk.Frame(body, bg=THEME["bg_card"]); row.pack(fill="x")
        log_fonts = ["Cascadia Code", "Consolas", "Courier New", "Source Code Pro", "Fira Code", "Segoe UI"]
        if self._settings.get("log_font") not in log_fonts and self._settings.get("log_font"): log_fonts.insert(0, self._settings["log_font"])
        self._log_font_var = tk.StringVar(value=self._settings.get("log_font", "Cascadia Code"))
        tk.Label(row, text=lang.t("set_font"), bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"],8)).pack(side="left", padx=5)
        fm = tk.OptionMenu(row, self._log_font_var, *log_fonts, command=lambda e: self._on_log_font_change())
        fm.configure(bg=THEME["bg_input"], fg=THEME["text"], relief="flat", highlightthickness=0, font=(THEME["font_family"],9)); fm["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"]); fm.pack(side="left", padx=5)
        tk.Label(row, text=lang.t("set_font_size"), bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"],8)).pack(side="left", padx=(14,5))
        self._log_size_var = tk.StringVar(value=str(self._settings.get("log_size", 9)))
        sm = tk.OptionMenu(row, self._log_size_var, *["8","9","10","11","12","13","14","16"], command=lambda e: self._on_log_font_change())
        sm.configure(bg=THEME["bg_input"], fg=THEME["text"], relief="flat", highlightthickness=0, font=(THEME["font_family"],9)); sm["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"]); sm.pack(side="left", padx=5)

        _, body = self._settings_card(left, lang.t("set_phpmode"), "PHP FastCGI и поведение локального сервера", "</>")
        row = tk.Frame(body, bg=THEME["bg_card"]); row.pack(fill="x")
        self._php_mode_map = {lang.t("php_dev"): "dev", lang.t("php_safe"): "safe"}
        _cur_mode = self._settings.get("php_mode", "dev")
        self._php_mode_var = tk.StringVar(value=lang.t("php_safe") if _cur_mode == "safe" else lang.t("php_dev"))
        tk.Label(row, text=lang.t("set_phpmode"), bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"],8)).pack(side="left", padx=5)
        pm = tk.OptionMenu(row, self._php_mode_var, *self._php_mode_map.keys(), command=lambda e: self._on_php_settings_change())
        pm.configure(bg=THEME["bg_input"], fg=THEME["text"], relief="flat", highlightthickness=0, font=(THEME["font_family"],9)); pm["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"]); pm.pack(side="left", padx=5)
        self._dir_list_var = tk.BooleanVar(value=bool(self._settings.get("dir_listing", False)))
        tk.Checkbutton(row, text=lang.t("set_dirlist"), variable=self._dir_list_var, command=self._on_php_settings_change,
                       bg=THEME["bg_card"], fg=THEME["text"], selectcolor=THEME["bg_input"], activebackground=THEME["bg_card"],
                       activeforeground=THEME["text"], font=(THEME["font_family"],8), highlightthickness=0, bd=0).pack(side="left", padx=(18,0))

        _, body = self._settings_card(left, lang.t("set_ports"), "Порты сервисов • применяются с перезапуском активных процессов", "▦")
        grid = tk.Frame(body, bg=THEME["bg_card"]); grid.pack(fill="x")
        self._port_vars = {}
        _pdefs = (("Apache", "apache_port"), ("MariaDB", "mariadb_port"), ("PHP", "php_cgi_port"), ("PostgreSQL", "postgresql_port"), ("Redis", "redis_port"), ("Nginx", "nginx_port"))
        for idx, (label, key) in enumerate(_pdefs):
            box = tk.Frame(grid, bg=THEME["bg_card"]); box.grid(row=idx//3, column=idx%3, sticky="ew", padx=5, pady=5); grid.grid_columnconfigure(idx%3, weight=1)
            tk.Label(box, text=label, bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"],8)).pack(anchor="w")
            var = tk.StringVar(value=str(CONFIG.get(key, ""))); self._port_vars[key] = var
            tk.Entry(box, textvariable=var, bg=THEME["bg_input"], fg=THEME["text"], insertbackground=THEME["text"], font=("Cascadia Code",9), relief="flat", bd=0, width=10, highlightthickness=1, highlightbackground=THEME["border"], highlightcolor=THEME["accent"]).pack(fill="x", ipady=6, pady=(3,0))
        foot = tk.Frame(body, bg=THEME["bg_card"]); foot.pack(fill="x", pady=(8,0))
        self._autostart_var = tk.BooleanVar(value=False)
        tk.Checkbutton(foot, text=lang.t("set_autostart"), variable=self._autostart_var, command=self._autostart_toggle,
                       bg=THEME["bg_card"], fg=THEME["text"], selectcolor=THEME["bg_input"], activebackground=THEME["bg_card"], activeforeground=THEME["text"], font=(THEME["font_family"],8), highlightthickness=0, bd=0).pack(side="left")
        IconButton(foot, "check", self._ports_apply, color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"], size=30, tip=lang.t("db_apply")).pack(side="right")
        threading.Thread(target=self._autostart_refresh, daemon=True).start()

        # Right column: environment and installed components.
        _, body = self._settings_card(right, lang.t("set_env"), "Версии PHP, Node.js, Python и инструментов", "◈")
        try:
            _php_vers = list(comps().get("php_versions", {}).keys()) or ["8.2","8.3","8.4"]
            _node_vers = list(comps().get("node_versions", {}).keys()) or ["20","22","24"]
            _py_vers = list(comps().get("python_versions", {}).keys()) or ["3.11","3.12","3.13"]
            _cur_php, _cur_node, _cur_py = self.svc.env_active()
        except Exception:
            _php_vers, _node_vers, _py_vers = ["8.2","8.3","8.4"], ["20","22","24"], ["3.11","3.12","3.13"]
            _cur_php, _cur_node, _cur_py = "", "", ""
        def envrow(label, versions, current, apply, attr):
            r = tk.Frame(body, bg=THEME["bg_card"]); r.pack(fill="x", pady=4)
            tk.Label(r, text=label, bg=THEME["bg_card"], fg=THEME["text"], font=(THEME["font_family"],8,"bold"), width=10, anchor="w").pack(side="left")
            var = tk.StringVar(value=current if current in versions else versions[-1]); setattr(self, attr+"_var", var)
            m = tk.OptionMenu(r, var, *versions); m.configure(bg=THEME["bg_input"], fg=THEME["text"], relief="flat", highlightthickness=0, font=(THEME["font_family"],9)); m["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"]); m.pack(side="left")
            cur = tk.Label(r, text="…", bg=THEME["bg_card"], fg=THEME["text_dim"], font=("Cascadia Code",8)); cur.pack(side="left", padx=8); setattr(self, attr+"_cur", cur)
            IconButton(r, "check", apply, color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"], size=28, tip=lang.t("db_apply")).pack(side="right")
        envrow(lang.t("env_php"), _php_vers, _cur_php, self._env_apply_php, "_env_php")
        envrow(lang.t("env_node"), _node_vers, _cur_node, self._env_apply_node, "_env_node")
        envrow("Python", _py_vers, _cur_py, self._env_apply_python, "_env_py")
        tk.Frame(body, bg=THEME["border"], height=1).pack(fill="x", pady=7)
        self._env_tools_var = tk.StringVar(value="…")
        tk.Label(body, text=lang.t("env_tools"), bg=THEME["bg_card"], fg=THEME["text_dim"], font=(THEME["font_family"],8)).pack(anchor="w")
        tk.Label(body, textvariable=self._env_tools_var, bg=THEME["bg_card"], fg=THEME["text_dim"], font=("Cascadia Code",8), justify="left", wraplength=390).pack(anchor="w", pady=(3,0))

        _, body = self._settings_card(right, lang.t("set_select"), "Выберите локальные компоненты для установки", "↓")
        self._set_component_vars = {}
        cb_grid = tk.Frame(body, bg=THEME["bg_card"]); cb_grid.pack(fill="x")
        try: manifest_names = [n for n,i in comps().items() if is_component(i)]
        except Exception: manifest_names = ["apache","php","mariadb","postgresql","redis","nginx","nodejs","phpmyadmin"]
        for idx, name in enumerate(manifest_names):
            var = tk.BooleanVar(value=False); self._set_component_vars[name] = var
            tk.Checkbutton(cb_grid, text=name.upper(), variable=var, bg=THEME["bg_card"], fg=THEME["text"], selectcolor=THEME["bg_input"], activebackground=THEME["bg_card"], activeforeground=THEME["text"], font=(THEME["font_family"],8), highlightthickness=0, bd=0).grid(row=idx//2, column=idx%2, sticky="w", padx=5, pady=3)
        ir = tk.Frame(body, bg=THEME["bg_card"]); ir.pack(fill="x", pady=(8,0))
        IconButton(ir, "down", self._set_install_selected, color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"], size=30, tip=lang.t("set_install_sel")).pack(side="left", padx=2)
        IconButton(ir, "down", self._set_install_missing, color=THEME["info"], hover_color="#2e9bf5", active_color="#0769b5", size=30, tip=lang.t("set_install_missing")).pack(side="left", padx=2)

        _, body = self._settings_card(right, "Резервная копия", "Сохранение и восстановление состояния Faraja", "↥")
        br = tk.Frame(body, bg=THEME["bg_card"]); br.pack(fill="x")
        IconButton(br, "save", self._snapshot_make, color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"], size=32, tip=lang.t("set_snapshot")).pack(side="left", padx=2)
        tk.Label(br, text=lang.t("set_snapshot"), bg=THEME["bg_card"], fg=THEME["text"], font=(THEME["font_family"],8)).pack(side="left", padx=5)
        IconButton(br, "up", self._snapshot_restore, color=THEME["warning_dim"], hover_color=THEME["warning"], active_color="#ba5e17", size=32, tip=lang.t("set_restore")).pack(side="left", padx=(16,2))
        tk.Label(br, text=lang.t("set_restore"), bg=THEME["bg_card"], fg=THEME["text"], font=(THEME["font_family"],8)).pack(side="left", padx=5)
        self._update_label = tk.Label(body, text="", bg=THEME["bg_card"], fg=THEME["warning"], font=(THEME["font_family"],8), wraplength=400, justify="left")
        self._update_label.pack(anchor="w", pady=(8,0))
        threading.Thread(target=self._update_check, daemon=True).start()

        cols = ("component", "state", "archive", "expected")
        self._set_tree = ttk.Treeview(parent, columns=cols, show="headings", height=7, style="Big.Treeview")
        for col, text in zip(cols, (lang.t("col_component"), lang.t("col_state"), lang.t("col_archive"), lang.t("col_expected"))): self._set_tree.heading(col, text=text)
        self._set_tree.column("component", width=110); self._set_tree.column("state", width=100); self._set_tree.column("archive", width=200); self._set_tree.column("expected", width=300)
        self._set_tree.pack(fill="x", padx=20, pady=(0,8))
        prog = tk.Frame(parent, bg=THEME["bg"]); prog.pack(fill="x", padx=20, pady=(0,10))
        self._set_progress = ttk.Progressbar(prog, mode="determinate", length=300, style="Modern.Horizontal.TProgressbar"); self._set_progress.pack(side="left")
        self._set_progress_label = tk.Label(prog, text="", bg=THEME["bg"], fg=THEME["text_dim"], font=(THEME["font_family"],8)); self._set_progress_label.pack(side="left", padx=8)
        self._set_refresh(); self._apply_log_font(); self._env_refresh_versions()

    def _env_refresh_versions(self):
        def w():
            try:
                php = self.svc.php_version_detect()
                node = self.svc.node_version_detect()
                py = self.svc.python_version_detect()
                tools = self.svc.tools_versions()
                ttxt = "  ·  ".join(f"{k}: {v}" for k, v in tools.items())
                def ui():
                    try:
                        self._env_php_cur.configure(text=php)
                        self._env_node_cur.configure(text=node)
                        self._env_py_cur.configure(text=py)
                        self._env_tools_var.set(ttxt)
                    except Exception:
                        pass
                self.root.after(0, ui)
            except Exception:
                pass
        threading.Thread(target=w, daemon=True).start()

    def _env_apply_php(self):
        ver = self._env_php_var.get()
        def w():
            try:
                self.svc.install_runtime_version(
                    "php", ver,
                    lambda g, t, s: self._install_progress(f"php {ver}", g, t, s))
                self._install_progress("", 0, 0)
                if self.svc.prun():
                    self.log("Restarting PHP to switch version...")
                    self.svc.stop_php()
                    self.svc.start_php()
                self.root.after(0, self._env_refresh_versions)
            except Exception as e:
                self.log("PHP version ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _env_apply_node(self):
        ver = self._env_node_var.get()
        def w():
            try:
                self.svc.install_runtime_version(
                    "node", ver,
                    lambda g, t, s: self._install_progress(f"node {ver}", g, t, s))
                self._install_progress("", 0, 0)
                if self.svc.node_servers:
                    self.log("Restart your Node.js servers to use the new version (Node.js tab)")
                self.root.after(0, self._env_refresh_versions)
            except Exception as e:
                self.log("Node.js version ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _env_apply_python(self):
        ver = self._env_py_var.get()
        def w():
            try:
                self.svc.install_runtime_version(
                    "python", ver,
                    lambda g, t, s: self._install_progress(f"python {ver}", g, t, s))
                self._install_progress("", 0, 0)
                if self.svc.py_servers:
                    self.log("Restart your Python servers to use the new version")
                self.root.after(0, self._env_refresh_versions)
            except Exception as e:
                self.log("Python version ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _ports_apply(self):
        try:
            new_ports = {}
            for key, var in self._port_vars.items():
                p = int(var.get().strip())
                if not 1 <= p <= 65535:
                    raise ValueError(key)
                new_ports[key] = p
        except ValueError:
            messagebox.showerror(lang.t("error"), "ports 1-65535")
            return
        def w():
            try:
                CONFIG.update(new_ports)
                try:
                    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                    CONFIG_FILE.write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
                except Exception as e:
                    self.log(f"server.json save warning: {e}")
                self.svc.write_configs()
                self.svc._write_nginx_conf()
                self.root.after(0, self._refresh_port_label)
                restarts = [("apache", self.svc.arun, self.svc.stop_apache, self.svc.start_apache),
                            ("db", self.svc.drun, self.svc.stop_db, self.svc.start_db),
                            ("php", self.svc.prun, self.svc.stop_php, self.svc.start_php),
                            ("pg", self.svc.pgrun, self.svc.stop_pg, self.svc.start_pg),
                            ("redis", self.svc.redisrun, self.svc.stop_redis, self.svc.start_redis),
                            ("nginx", self.svc.nginxrun, self.svc.stop_nginx, self.svc.start_nginx)]
                for _name, is_run, do_stop, do_start in restarts:
                    try:
                        if is_run():
                            do_stop()
                            do_start()
                    except Exception as e:
                        self.log(f"Restart ERROR: {e}")
                self.log("Ports applied: " + ", ".join(f"{k}={v}" for k, v in new_ports.items()))
            except Exception as e:
                self.log("Ports ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _autostart_target(self):
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        return f'"{sys.executable}" "{Path(__file__).resolve()}"'

    def _autostart_refresh(self):
        try:
            r = subprocess.run(["reg", "query",
                                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
                                "/v", "FarajaWebServer"],
                               capture_output=True, text=True, timeout=10,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            on = r.returncode == 0 and ".exe" in (r.stdout or "") or ".py" in (r.stdout or "")
            self.root.after(0, lambda: self._autostart_var.set(bool(on)))
        except Exception:
            pass

    def _autostart_toggle(self):
        on = bool(self._autostart_var.get())
        try:
            if on:
                r = subprocess.run(["reg", "add",
                                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
                                    "/v", "FarajaWebServer", "/t", "REG_SZ",
                                    "/d", self._autostart_target(), "/f"],
                                   capture_output=True, text=True, timeout=10,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if r.returncode != 0:
                    raise RuntimeError((r.stderr or r.stdout or "").strip()[:200])
                self.log("Autostart enabled")
            else:
                r = subprocess.run(["reg", "delete",
                                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
                                    "/v", "FarajaWebServer", "/f"],
                                   capture_output=True, text=True, timeout=10,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if r.returncode != 0:
                    raise RuntimeError((r.stderr or r.stdout or "").strip()[:200])
                self.log("Autostart disabled")
        except Exception as e:
            self.root.after(0, lambda: self._autostart_var.set(not on))
            messagebox.showerror(lang.t("error"), str(e))

    def _snapshot_make(self):
        def w():
            try:
                out = self.svc.snapshot_create()
                self.root.after(0, lambda: messagebox.showinfo(APP_NAME, str(out.name)))
            except Exception as e:
                self.log("Snapshot ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _snapshot_restore(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Faraja snapshot",
            filetypes=[("Faraja snapshot", "faraja-snap-*.zip"), ("ZIP", "*.zip")],
            initialdir=str(APP_ROOT / "backups"))
        if not path:
            return
        if not DarkPrompt.ask_yes_no(self.root, lang.t("set_restore"), Path(path).name + "?"):
            return
        def w():
            try:
                self.svc.snapshot_restore(path)
                self.root.after(0, self._set_refresh)
            except Exception as e:
                self.log("Restore ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _update_check(self):
        try:
            tag = self.svc.latest_release()
            if tag and self.svc._ver_tuple(tag) > self.svc._ver_tuple(APP_VERSION):
                msg = lang.t("update_avail", ver=tag, cur="v" + APP_VERSION)
                self.log(msg)
                self.root.after(0, lambda: self._update_label.configure(text=msg[:100]))
        except Exception as e:
            self.log(f"Update check skipped ({e})")

    def _on_log_font_change(self):
        self._settings["log_font"] = self._log_font_var.get()
        try:
            self._settings["log_size"] = int(self._log_size_var.get())
        except ValueError:
            self._settings["log_size"] = 9
        self._save_settings()
        self._apply_log_font()

    def _on_php_settings_change(self):
        mode = self._php_mode_map.get(self._php_mode_var.get(), "dev")
        self._settings["php_mode"] = mode
        self._settings["dir_listing"] = bool(self._dir_list_var.get())
        self._save_settings()
        def w():
            try:
                self.svc.write_configs()
                self.log(f"PHP mode: {mode}, directory listing: {'on' if self._settings['dir_listing'] else 'off'}")
                if self.svc.prun():
                    self.log("Restarting PHP to apply new settings...")
                    self.svc.stop_php()
                    self.svc.start_php()
            except Exception as e:
                self.log("PHP settings ERROR: " + str(e))
        threading.Thread(target=w, daemon=True).start()

    def _apply_log_font(self):
        try:
            font = (self._log_font_var.get(), int(self._log_size_var.get()))
        except Exception:
            return
        for vid, (t, _) in getattr(self, "views", {}).items():
            try:
                t.configure(font=font)
            except Exception:
                pass

    def _set_refresh(self):
        if not hasattr(self, "_set_tree"):
            return
        for item in self._set_tree.get_children():
            self._set_tree.delete(item)
        try:
            manifest = comps()
        except Exception:
            return
        for name, item in manifest.items():
            if not is_component(item):
                continue
            installed = (APP_ROOT / item["expected"]).exists()
            state = lang.t("state_installed") if installed else lang.t("state_missing")
            try:
                arc = find_local_archive(name)
                arc_name = arc.name if arc is not None else "—"
            except Exception:
                arc_name = "—"
            self._set_tree.insert("", "end", iid=name,
                                  values=(name, state, arc_name, item["expected"]))

    def _set_browse_dl(self):
        from tkinter import filedialog
        global DOWNLOADS
        d = filedialog.askdirectory(initialdir=self._set_dl_var.get())
        if not d:
            return
        DOWNLOADS = Path(d)
        DOWNLOADS.mkdir(parents=True, exist_ok=True)
        self._set_dl_var.set(str(DOWNLOADS))
        self._settings["downloads"] = str(DOWNLOADS)
        self._save_settings()
        self._set_refresh()

    def _set_open_dl(self):
        try:
            os.startfile(str(DOWNLOADS))
        except Exception as e:
            messagebox.showerror(lang.t("error"), str(e))

    def _set_install(self, names):
        def progress_cb(got, total, speed, name=""):
            self._install_progress(name, got, total)
        def w():
            try:
                for n in names:
                    install_component(n, self.log, lambda g, t, s, n=n: progress_cb(g, t, s, n))
                self._install_progress("", 0, 0)
                self.log(lang.t("set_inst_done"))
                self.root.after(0, self._set_refresh)
            except Exception as e:
                self.log("INSTALL ERROR: " + str(e))
                self.root.after(0, lambda: messagebox.showerror(lang.t("error"), str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _set_install_selected(self):
        names = [name for name, var in getattr(self, "_set_component_vars", {}).items() if var.get()]
        if not names:
            messagebox.showinfo(APP_NAME, lang.t("set_no_selection"))
            return
        self._set_install(names)

    def _set_install_missing(self):
        try:
            manifest = comps()
        except Exception as e:
            messagebox.showerror(lang.t("error"), str(e))
            return
        missing = [n for n, i in manifest.items() if is_component(i) and not (APP_ROOT / i["expected"]).exists()]
        if not missing:
            self.log(lang.t("all_installed"))
            return
        self._set_install(missing)

    def copy(self, t):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(t.get("sel.first", "sel.last"))
        except tk.TclError:
            pass

    def copyall(self, t):
        self.root.clipboard_clear()
        self.root.clipboard_append(t.get("1.0", "end-1c"))

    def copy_sel(self, e):
        self.copy(e.widget)
        return "break"

    def log(self, msg):
        self.lines.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        self.lines = self.lines[-3000:]
        self.root.after(0, lambda: self.status.set(msg))

    def status_color(self, w, running):
        if running:
            w.configure(text=lang.t("running"), bg=THEME["success"], fg=THEME["white"])
        else:
            w.configure(text=lang.t("stopped"), bg=THEME["danger"], fg=THEME["white"])

    def _toggle_svc(self, attr):
        mapping = {
            "apache": (self.svc.arun, self.start_a, self.stop_a),
            "db":     (self.svc.drun, self.start_d, self.stop_d),
            "php":    (self.svc.prun, self.start_p, self.stop_p),
            "pg":     (self.svc.pgrun, self.start_pg_ui, self.stop_pg_ui),
            "redis":  (self.svc.redisrun, self.start_redis_ui, self.stop_redis_ui),
            "nginx":  (self.svc.nginxrun, self.start_nginx_ui, self.stop_nginx_ui),
            "docker": (self.svc.dockerun, self.start_docker_ui, self.stop_docker_ui),
            "node":   (self.svc.noderun, self.start_node_ui, self.stop_node_ui),
        }
        is_running, start_fn, stop_fn = mapping[attr]
        if is_running():
            self.worker(stop_fn, lang.t("status_stopping", svc=attr))
        else:
            self.worker(start_fn, lang.t("status_starting", svc=attr))

    def _update_toggle_btn(self, attr, running):
        btn = getattr(self, attr + "_toggle")
        if running:
            btn.set_kind("stop")
            btn.set_colors(THEME["danger"], "#ff6b5a", THEME["danger_dim"])
        else:
            btn.set_kind("play")
            btn.set_colors(THEME["success"], "#55e39a", THEME["success_dim"])

    def _startup_site_php(self):
        try:
            self.svc.ensure_all_site_php()
        except Exception as e:
            self.log(f"Site PHP warmup: {e}")

    def _docker_poll(self):
        while not self.closing:
            try:
                self._docker_ok = self.svc.docker_check()
            except Exception:
                self._docker_ok = False
            for _ in range(150):
                if self.closing:
                    return
                time.sleep(0.1)

    def refresh(self):
        try:
            a = self.svc.arun()
            d = self.svc.drun()
            p = self.svc.prun()
            pg = self.svc.pgrun()
            rd = self.svc.redisrun()
            nx = self.svc.nginxrun()
            dk = getattr(self, "_docker_ok", False)
            no = self.svc.noderun()
            self.status_color(self.apache_status, a)
            self.status_color(self.db_status, d)
            self.status_color(self.php_status, p)
            self.status_color(self.pg_status, pg)
            self.status_color(self.redis_status, rd)
            self.status_color(self.nginx_status, nx)
            self.status_color(self.docker_status, dk)
            self.status_color(self.node_status, no)

            for prefix, running in [("apache", a), ("db", d), ("php", p), ("pg", pg), ("redis", rd), ("nginx", nx), ("docker", dk), ("node", no)]:
                self._update_toggle_btn(prefix, running)
                self._colorize_port_label(prefix, running)

        finally:
            if not self.closing:
                self.root.after(1000, self.refresh)

    def settext(self, vid, data):
        if vid not in self.views:
            return
        if self._view_cache.get(vid) == data:
            return
        self._view_cache[vid] = data
        t, _ = self.views[vid]
        t.delete("1.0", "end")
        t.insert("1.0", data)
        t.see("end")

    def _read_log_cached(self, key, path, limit):
        try:
            st = path.stat()
            sig = (st.st_mtime_ns, st.st_size)
        except OSError:
            return None
        if self._log_stat.get(key) == sig:
            return None
        try:
            data = path.read_text(encoding="mbcs", errors="replace")[-limit:]
        except Exception:
            return None
        self._log_stat[key] = sig
        return data

    def refresh_logs(self):
        try:
            lines = self.lines
            try:
                lvl = self._log_level_var.get()
                if lvl and lvl != "ALL":
                    lines = [l for l in lines if lvl in l]
                q = self._log_search_var.get().strip().lower()
                if q:
                    lines = [l for l in lines if q in l.lower()]
            except Exception:
                lines = self.lines
            self.settext("system", "\n".join(lines))
            for vid, (_, p) in self.views.items():
                if p is None:
                    continue
                data = self._read_log_cached(vid, p, 50000)
                if data is not None:
                    self.settext(vid, data)
            parts = []
            changed = False
            for name in ("apache-process.log", "php-process.log", "mariadb-process.log", "mariadb-init.log",
                          "postgresql-process.log", "postgresql-init.log", "redis-process.log", "nginx-process.log",
                          "node-process.log", "python-process.log"):
                p = LOGS / name
                if not p.exists():
                    continue
                try:
                    st = p.stat()
                    sig = (st.st_mtime_ns, st.st_size)
                except OSError:
                    continue
                cache_key = "proc:" + name
                if self._log_stat.get(cache_key) != sig:
                    changed = True
                self._log_stat[cache_key] = sig
                parts.append(name)
            if changed or self._view_cache.get("proc") is None:
                blocks = []
                for name in parts:
                    p = LOGS / name
                    try:
                        blocks.append(f"\n===== {name} =====\n" + p.read_text(encoding="mbcs", errors="replace")[-20000:])
                    except Exception:
                        pass
                self.settext("proc", "".join(blocks))
        finally:
            if not self.closing:
                self.root.after(2000, self.refresh_logs)

    def clear(self):
        self.lines.clear()
        for p in LOGS.glob("*.log"):
            try:
                p.write_text("", encoding="utf-8")
            except Exception:
                pass
        self.log("Logs cleared")

    def worker(self, fn, title):
        if not hasattr(self, "_operation_lock"):
            self._operation_lock = threading.RLock()
        def w():
            with self._operation_lock:
                try:
                    self.log(title + "...")
                    fn()
                except Exception as e:
                    self.log("ERROR: " + str(e))
                    self.root.after(0, lambda e=e: messagebox.showerror(title + " error", str(e)))
        threading.Thread(target=w, daemon=True).start()

    def _start_guarded(self, port, start_fn, title):
        victims = []
        if port_open(port):
            owners = port_owners(port)
            if owners:
                detail = ", ".join(f"{name or 'unknown'} (PID {pid})" for pid, name in owners)
                if not DarkPrompt.ask_yes_no(self.root, lang.t("kill_title"),
                                             lang.t("kill_text", port=port, detail=detail)):
                    return
                victims = [pid for pid, _ in owners]
        def run():
            for pid in victims:
                kill_pid_tree(pid)
            if victims:
                wait_port_closed(port, 8)
            start_fn()
        self.worker(run, title)
    def start_a(self): self._start_guarded(CONFIG["apache_port"], self.svc.start_apache, "Starting Apache")
    def stop_a(self): self.worker(self.svc.stop_apache, "Stopping Apache")
    def restart_a(self):
        def restart():
            self.svc.stop_apache()
            if not wait_port_closed(CONFIG["apache_port"], 12):
                owners = port_owners(CONFIG["apache_port"])
                detail = ", ".join(f"{name or 'unknown'} (PID {pid})" for pid, name in owners)
                raise RuntimeError(
                    f"Port {CONFIG['apache_port']} is still occupied after Apache stop: {detail}"
                )
            self.svc.start_apache()
        self.worker(restart, "Restarting Apache")

    def start_d(self): self._start_guarded(CONFIG["mariadb_port"], self.svc.start_db, "Starting MariaDB")
    def stop_d(self): self.worker(self.svc.stop_db, "Stopping MariaDB")
    def restart_d(self): self.worker(lambda: (self.svc.stop_db(), self.svc.start_db()), "Restarting MariaDB")
    def start_p(self): self._start_guarded(CONFIG["php_cgi_port"], self.svc.start_php, "Starting PHP")
    def stop_p(self): self.worker(self.svc.stop_php, "Stopping PHP")
    def restart_p(self): self.worker(lambda: (self.svc.stop_php(), self.svc.start_php()), "Restarting PHP")

    def start_pg_ui(self): self._start_guarded(CONFIG["postgresql_port"], self.svc.start_pg, "Starting PostgreSQL")
    def stop_pg_ui(self): self.worker(self.svc.stop_pg, "Stopping PostgreSQL")
    def restart_pg(self): self.worker(lambda: (self.svc.stop_pg(), self.svc.start_pg()), "Restarting PostgreSQL")

    def start_redis_ui(self): self._start_guarded(CONFIG["redis_port"], self.svc.start_redis, "Starting Redis")
    def stop_redis_ui(self): self.worker(self.svc.stop_redis, "Stopping Redis")
    def restart_redis(self): self.worker(lambda: (self.svc.stop_redis(), self.svc.start_redis()), "Restarting Redis")

    def start_nginx_ui(self): self._start_guarded(CONFIG["nginx_port"], self.svc.start_nginx, "Starting Nginx")
    def stop_nginx_ui(self): self.worker(self.svc.stop_nginx, "Stopping Nginx")
    def restart_nginx(self): self.worker(lambda: (self.svc.stop_nginx(), self.svc.start_nginx()), "Restarting Nginx")
    def setup_ssl_cmd(self): self.worker(self.svc.setup_ssl, "Setting up SSL")

    def start_node_ui(self): self.worker(self.svc.start_node, "Starting Node.js")
    def stop_node_ui(self): self.worker(self.svc.stop_node, "Stopping Node.js")
    def _install_progress(self, name, got, total, speed=0):
        def ui():
            bars = []
            if hasattr(self, "_progress_bar"):
                bars.append((self._progress_bar, getattr(self, "_progress_label", None)))
            if hasattr(self, "_set_progress"):
                try:
                    bars.append((self._set_progress, self._set_progress_label))
                except Exception:
                    pass
            if got == 0 and total == 0:
                for bar, lbl in bars:
                    try:
                        bar.stop()
                        bar.configure(mode="determinate", value=0)
                        if lbl is not None:
                            lbl.configure(text="")
                    except Exception:
                        pass
                self._prog_indet = False
                self.status.set(lang.t("status_ready"))
                return
            if got < 0 or total <= 0:
                txt = f"{name}: {lang.t('install_extract')}" if name else lang.t("install_extract")
                for bar, lbl in bars:
                    try:
                        bar.configure(mode="indeterminate")
                        if not getattr(self, "_prog_indet", False):
                            bar.start(60)
                        if lbl is not None:
                            lbl.configure(text=txt)
                    except Exception:
                        pass
                self._prog_indet = True
                self.status.set(txt)
                return
            self._prog_indet = False
            pct = got * 100 // total
            txt = f"{got/1048576:.1f}/{total/1048576:.1f} MB"
            if name:
                txt = f"{name}: " + txt
            if speed > 0:
                txt += f" | {speed/1048576:.2f} MB/s"
            for bar, lbl in bars:
                try:
                    bar.stop()
                    bar.configure(mode="determinate", value=pct)
                    if lbl is not None:
                        lbl.configure(text=txt)
                except Exception:
                    pass
            self.status.set(txt)
        try:
            self.root.after(0, ui)
        except Exception:
            pass
    def start_docker_ui(self):
        def run():
            self.svc.start_docker()
            self._docker_ok = True
        self.worker(run, "Starting Docker")
    def stop_docker_ui(self):
        def run():
            self.svc.stop_docker()
            self._docker_ok = self.svc.docker_check()
        self.worker(run, "Stopping Docker")

    def run_script_cmd(self):
        from tkinter import filedialog
        script = filedialog.askopenfilename(
            title="Select Script",
            filetypes=[("TypeScript", "*.ts"), ("JavaScript", "*.js"), ("All files", "*.*")],
            initialdir=str(WWW)
        )
        if script:
            self.worker(lambda: self.svc.run_script(script), f"Running {Path(script).name}")

    def start_all(self):
        def run():
            # Start independent services independently: a missing PHP package
            # must not prevent MariaDB/PostgreSQL/Redis from starting.
            for label, fn in [
                ("PHP", self.svc.start_php),
                ("MariaDB", self.svc.start_db),
                ("PostgreSQL", self.svc.start_pg),
                ("Redis", self.svc.start_redis),
            ]:
                try:
                    fn()
                except Exception as e:
                    self.log(f"{label} start skipped: {e}")

            apache_running=web_server_running("apache") or self.svc.arun()
            nginx_running=web_server_running("nginx") or self.svc.nginxrun()
            if apache_running and nginx_running:
                self.log("Both web servers detected; stopping Nginx. Apache is kept active.")
                try:
                    self.svc.stop_nginx()
                    nginx_running=False
                except Exception as e:
                    self.log("Nginx cleanup failed: " + str(e))
            if nginx_running:
                self.log("Nginx is active; Apache remains stopped.")
            elif not apache_running:
                try:
                    self.svc.start_apache()
                    self.log("Apache started; Nginx remains stopped.")
                except Exception as e:
                    self.log("Apache start skipped: " + str(e))
            else:
                self.log("Apache is active; Nginx remains stopped.")
        self.worker(run,"Starting All")

    def stop_all(self):
        def run():
            # Best-effort stop: one broken/foreign process must not prevent
            # other MiniServer services from being stopped.
            for label, fn in [
                ("Nginx", self.svc.stop_nginx),
                ("Apache", self.svc.stop_apache),
                ("PHP", self.svc.stop_php),
                ("MariaDB", self.svc.stop_db),
                ("PostgreSQL", self.svc.stop_pg),
                ("Redis", self.svc.stop_redis),
            ]:
                try:
                    fn()
                except Exception as e:
                    self.log(f"{label} stop warning: {e}")
        self.worker(run,"Stopping All")

    def restart_all(self):
        def run():
            was_nginx=web_server_running("nginx") or self.svc.nginxrun()
            was_apache=web_server_running("apache") or self.svc.arun()
            for label, fn in [
                ("Nginx", self.svc.stop_nginx), ("Apache", self.svc.stop_apache),
                ("PHP", self.svc.stop_php), ("MariaDB", self.svc.stop_db),
                ("PostgreSQL", self.svc.stop_pg), ("Redis", self.svc.stop_redis)]:
                try: fn()
                except Exception as e: self.log(f"{label} stop warning: {e}")
            for label, fn in [
                ("PHP", self.svc.start_php), ("MariaDB", self.svc.start_db),
                ("PostgreSQL", self.svc.start_pg), ("Redis", self.svc.start_redis)]:
                try: fn()
                except Exception as e: self.log(f"{label} start skipped: {e}")
            try:
                if was_nginx and not was_apache:
                    self.svc.start_nginx()
                else:
                    self.svc.start_apache()
                    self.log("Apache started; Nginx remains stopped.")
            except Exception as e:
                self.log("Web server restart skipped: " + str(e))
        self.worker(run,"Restarting All")

    def localhost(self): webbrowser.open(f'http://127.0.0.1:{CONFIG["apache_port"]}/')
    def pma(self): webbrowser.open(f'http://127.0.0.1:{CONFIG["apache_port"]}/phpmyadmin/')

    def check(self):
        missing = [n for n, i in comps().items() if is_component(i) and not (APP_ROOT / i["expected"]).exists()]
        if not missing:
            self.log(lang.t("all_installed"))
            return
        local_archives = []
        for n in missing:
            arc = find_local_archive(n)
            if arc is not None:
                local_archives.append(f"{n}: {arc.name}")
        if local_archives:
            self.log(lang.t("local_archive_found"))
            for line in local_archives:
                self.log("  " + line)
        if messagebox.askyesno(
            APP_NAME,
            lang.t("missing_components") + "\n\n" + "\n".join(missing) +
            ("\n\n" + lang.t("local_archive_found") if local_archives else "") +
            "\n\n" + lang.t("install_now")
        ):
            def w():
                try:
                    for n in missing:
                        local = find_local_archive(n)
                        label = "Installing from local archive" if local is not None else "Downloading"
                        install_component(
                            n,
                            self.log,
                            lambda g, t, s, n=n: self._install_progress(n, g, t, s)
                        )
                    self._install_progress("", 0, 0)
                    self.log("Installation completed")
                except Exception as e:
                    self.log("INSTALLATION ERROR: " + str(e))
                    self.root.after(0, lambda: messagebox.showerror("Installation error", str(e)))
            threading.Thread(target=w, daemon=True).start()

    def ensure_tray(self):
        if self.tray:
            return
        menu = pystray.Menu(
            pystray.MenuItem(f"Show {APP_NAME}", lambda i, x: self.show(), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lang.t("start_all"), lambda i, x: self.start_all()),
            pystray.MenuItem(lang.t("stop_all"), lambda i, x: self.stop_all()),
            pystray.MenuItem(lang.t("restart_all"), lambda i, x: self.restart_all()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Start Apache", lambda i, x: self.start_a()),
            pystray.MenuItem(f"Stop Apache", lambda i, x: self.stop_a()),
            pystray.MenuItem(f"Start MariaDB", lambda i, x: self.start_d()),
            pystray.MenuItem(f"Stop MariaDB", lambda i, x: self.stop_d()),
            pystray.MenuItem(f"Start PHP", lambda i, x: self.start_p()),
            pystray.MenuItem(f"Stop PHP", lambda i, x: self.stop_p()),
            pystray.MenuItem(f"Start PostgreSQL", lambda i, x: self.start_pg_ui()),
            pystray.MenuItem(f"Stop PostgreSQL", lambda i, x: self.stop_pg_ui()),
            pystray.MenuItem(f"Start Redis", lambda i, x: self.start_redis_ui()),
            pystray.MenuItem(f"Stop Redis", lambda i, x: self.stop_redis_ui()),
            pystray.MenuItem(f"Start Nginx", lambda i, x: self.start_nginx_ui()),
            pystray.MenuItem(f"Stop Nginx", lambda i, x: self.stop_nginx_ui()),
            pystray.MenuItem(f"Start Node.js", lambda i, x: self.start_node_ui()),
            pystray.MenuItem(f"Stop Node.js", lambda i, x: self.stop_node_ui()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", lambda i, x: self.exit())
        )
        self.tray = pystray.Icon(APP_NAME, Image.open(tray_image()), f"{APP_NAME} V16", menu)
        self.tray.on_activate = lambda i: self.show()
        threading.Thread(target=self.tray.run, daemon=True).start()

    def hide(self):
        self.ensure_tray()
        self.root.withdraw()
        self.log(lang.t("minimized_tray"))

    def show(self):
        self.root.after(0, lambda: (self.root.deiconify(), self.root.lift(), self.root.focus_force()))

    def unmap(self, e):
        if self.root.state() == "iconic":
            self.hide()

    def exit(self):
        if self.closing:
            return
        self.closing = True
        try:
            if self.tray:
                self.tray.stop()
        except Exception:
            pass

        def finalize():
            try:
                self.svc.shutdown()
            except Exception:
                pass
            # One final fast safety pass for anything that ignored its normal stop.
            try:
                emergency_kill()
            except Exception:
                pass
            self.root.after(0, self.root.destroy)

        threading.Thread(target=finalize, daemon=True).start()

    def _show_donate(self):
        win = tk.Toplevel(self.root)
        win.title(lang.t("donate_title"))
        win.geometry("520x640")
        win.configure(bg=THEME["bg_card"], highlightbackground=THEME["accent"],
                      highlightthickness=1)
        win.transient(self.root)
        try:
            win.iconbitmap(str(ICON))
        except Exception:
            pass
        tk.Label(win, text="❤  " + lang.t("donate_title"), bg=THEME["bg_card"],
                 fg=THEME["accent"], font=(THEME["font_family"], 14, "bold")).pack(pady=(14, 2))
        tk.Label(win, text=lang.t("donate_text"), bg=THEME["bg_card"], fg=THEME["text_dim"],
                 font=(THEME["font_family"], 9), wraplength=460, justify="center").pack(pady=(0, 8))
        hint = tk.Label(win, text="", bg=THEME["bg_card"], fg=THEME["success"],
                        font=(THEME["font_family"], 8))
        hint.pack()
        self._donate_imgs = {}
        self._donate_tab_btns = {}
        coins = (("BTC", "₿", "net_btc"), ("ETH", "Ξ", "net_eth"), ("TRX", "◈", "net_trx"))
        for coin, _sym, _net in coins:
            path, _addr = DONATE[coin]
            try:
                img = Image.open(str(path)).resize((220, 220), Image.LANCZOS)
                self._donate_imgs[coin] = ImageTk.PhotoImage(img)
            except Exception:
                pass
        tabbar = tk.Frame(win, bg=THEME["bg_card"])
        tabbar.pack(pady=4)
        for coin, sym, net in coins:
            b = StyledButton(tabbar, f"{sym} {coin}", lambda c=coin: self._donate_show(c),
                             color=THEME["bg_input"], hover_color=THEME["border_light"],
                             active_color=THEME["border"],
                             width=130, height=32, font_size=10)
            b.pack(side="left", padx=4)
            ToolTip(b, lang.t(net))
            self._donate_tab_btns[coin] = b
        self._donate_net = tk.Label(win, text="", bg=THEME["bg_card"], fg=THEME["text_dim"],
                                    font=(THEME["font_family"], 9))
        self._donate_net.pack(pady=(2, 4))
        self._donate_qr = tk.Label(win, bg="white", bd=0, relief="flat")
        self._donate_qr.pack(pady=4)
        self._donate_addr = tk.Label(win, text="", bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                     font=("Cascadia Code", 10), wraplength=420, justify="center",
                                     padx=12, pady=10)
        self._donate_addr.pack(fill="x", padx=24, pady=(4, 8))
        StyledButton(win, lang.t("donate_copy"), self._donate_copy_current,
                     color=THEME["accent"], hover_color=THEME["accent_hover"],
                     active_color=THEME["accent_active"],
                     width=170, height=30, font_size=9).pack(pady=(0, 14))
        self._donate_hint = hint
        self._donate_current = "BTC"
        self._donate_show("BTC")

    def _donate_show(self, coin):
        self._donate_current = coin
        nets = {"BTC": "net_btc", "ETH": "net_eth", "TRX": "net_trx"}
        _path, addr = DONATE[coin]
        for c, b in self._donate_tab_btns.items():
            on = (c == coin)
            b._color = THEME["accent"] if on else THEME["bg_input"]
            b._hover_color = THEME["accent_hover"] if on else THEME["border_light"]
            b._active_color = THEME["accent_active"] if on else THEME["border"]
            b._draw(b._color)
        self._donate_net.configure(text=lang.t(nets[coin]))
        photo = self._donate_imgs.get(coin)
        if photo is not None:
            self._donate_qr.configure(image=photo, text="")
        else:
            self._donate_qr.configure(image="", text=coin,
                                      bg=THEME["bg_elevated"], fg=THEME["accent"],
                                      font=(THEME["font_family"], 32, "bold"),
                                      width=18, height=8)
        self._donate_addr.configure(text=addr)
        self._donate_hint.configure(text="")

    def _donate_copy_current(self):
        try:
            _path, addr = DONATE.get(self._donate_current, (None, ""))
            self.root.clipboard_clear()
            self.root.clipboard_append(addr)
            self._donate_hint.configure(text=lang.t("donate_copied"))
        except Exception:
            pass

    def _show_help(self):
        win = tk.Toplevel(self.root)
        win.title(lang.t("doc_title"))
        try:
            app_w = max(1000, self.root.winfo_width())
        except Exception:
            app_w = 1000
        win.geometry(f"{app_w}x640")
        win.configure(bg=THEME["bg"])
        try:
            win.iconbitmap(str(ICON))
        except Exception:
            pass

        header = tk.Frame(win, bg=THEME["bg"])
        header.pack(fill="x", padx=20, pady=10)
        tk.Label(header, text=lang.t("doc_title"), bg=THEME["bg"], fg=THEME["accent"],
                 font=(THEME["font_family"], 16, "bold")).pack(side="left")

        nb = OfficeTabs(win, active_size=11, passive_size=9)

        docs = {
            "ru": {
                "overview": "LockSer — портативная локальная среда разработки для Windows.\n\n"
                    "ЧТО ВХОДИТ:\n"
                    "• Apache — веб-сервер (HTTP, порт 8080)\n"
                    "• MariaDB — база данных, совместимая с MySQL (порт 3306)\n"
                    "• PHP — серверный язык программирования (FastCGI, порт 9074)\n"
                    "• PostgreSQL — продвинутая СУБД (порт 5432)\n"
                    "• Redis — хранилище «ключ-значение» в памяти (порт 6379)\n"
                    "• Nginx — обратный прокси и балансировщик (порт 80)\n"
                    "• Node.js — выполнение JavaScript/TypeScript скриптов\n"
                    "• Docker — проверка наличия и статуса контейнеров\n"
                    "• phpMyAdmin — веб-панель управления базами MySQL/MariaDB\n\n"
                    "КАК УСТРОЕНО:\n"
                    "• Все компоненты живут в папке runtime/ рядом с программой — ничего не ставится в систему.\n"
                    "• Вкладка «Основное» — карточки сервисов: зелёный бейдж РАБОТАЕТ, красный ОСТАНОВЛЕН.\n"
                    "• Вкладка «Дополнительно» — логи, файлы, SQL-редактор, сайты, задачи, настройки.\n"
                    "• Язык интерфейса переключается флажками в шапке (RU/EN/ES/DE/FR/ZH) и запоминается.\n"
                    "• При закрытии окна программа сворачивается в трей (значок у часов). Полный выход — через меню трея.",
                "services": "УПРАВЛЕНИЕ СЕРВИСАМИ — ПОШАГОВО:\n\n"
                    "1. ЗАПУСК ОДНОГО СЕРВИСА: на карточке нажмите СТАРТ. Дождитесь зелёного бейджа РАБОТАЕТ\n"
                    "   и строки в логе «System», например «Apache started on port 8080».\n"
                    "2. ОСТАНОВКА: нажмите СТОП на карточке. Бейдж станет красным.\n"
                    "3. ПЕРЕЗАПУСК (оранжевая кнопка): останавливает и запускает сервис заново.\n"
                    "   Удобно после правок конфигов.\n"
                    "4. ЗАПУСТИТЬ ВСЕ / ОСТАНОВИТЬ ВСЕ — кнопки в шапке. Порядок запуска автоматический:\n"
                    "   PHP → MariaDB → PostgreSQL → Redis → Apache → Nginx.\n"
                    "5. Если порт занят чужой программой — появится ошибка с именем процесса и PID.\n"
                    "   Закройте чужую программу или смените порт в config/server.json и перезапустите.\n\n"
                    "ПОРТЫ ПО УМОЛЧАНИЮ:\n"
                    "• Apache 8080 — сайт: http://127.0.0.1:8080/\n"
                    "• MariaDB 3306 — логин root, пароль пустой (первый запуск)\n"
                    "• PHP FastCGI 9074 — внутренний, соединяет Apache и PHP\n"
                    "• PostgreSQL 5432 — пользователь postgres\n"
                    "• Redis 6379 — пароль не требуется\n"
                    "• Nginx 80 — требует прав администратора (порт ниже 1024)\n\n"
                    "СОВЕТ: наведите курсор на любую кнопку — появится всплывающая подсказка.",
                "quickstart": "БЫСТРЫЙ СТАРТ — ВАШ ПЕРВЫЙ САЙТ ЗА 5 ШАГОВ:\n\n"
                    "Шаг 1. При первом запуске откроется мастер: отметьте нужные компоненты галочками\n"
                    "и нажмите «Установить». Архивы качаются в папку downloads/ (видны в Настройках).\n"
                    "Шаг 2. Нажмите «ЗАПУСТИТЬ ВСЕ» в шапке. Все бейджи должны стать зелёными.\n"
                    "Шаг 3. Откройте в браузере http://127.0.0.1:8080/ — вы увидите стартовую страницу.\n"
                    "Шаг 4. Положите свой проект в папку www/ (например www/mysite/index.php) —\n"
                    "он сразу доступен по адресу http://127.0.0.1:8080/mysite/.\n"
                    "Шаг 5. Проверьте PHP: создайте www/info.php с текстом <?php phpinfo(); ?>\n"
                    "и откройте http://127.0.0.1:8080/info.php.\n\n"
                    "ТИПОВЫЕ ПРОБЛЕМЫ:\n"
                    "• «Порт занят» — закройте Skype/IIS/другой сервер или смените порт.\n"
                    "• Пустая страница PHP — убедитесь, что запущены и Apache, и PHP.\n"
                    "• Логи ошибок — вкладки «Ошибки Apache / PHP / MariaDB».",
                "sites": "САЙТЫ — КАК ДОБАВИТЬ И ОТКРЫТЬ:\n\n"
                    "Шаг 1. Вкладка «Дополнительно» → «Сайты» → кнопка «Добавить сайт».\n"
                    "Шаг 2. Введите имя (например mysite) — создастся папка www/mysite/ с index.html.\n"
                    "Шаг 3. Домен можно оставить mysite.localhost, порт — пустым.\n"
                    "Шаг 4. Выберите сайт в списке и нажмите «Открыть сайт» — он откроется в браузере\n"
                    "по адресу http://127.0.0.1:8080/mysite/.\n"
                    "Шаг 5. Кнопка «Открыть папку» показывает файлы сайта в проводнике.\n\n"
                    "ФАЙЛЫ:\n"
                    "• Вкладка «Файлы» — встроенный менеджер: двойной клик открывает папку/файл,\n"
                    "кнопка «Редактировать» открывает код с подсветкой синтаксиса (PHP, HTML, CSS, JS, TS, Python).\n"
                    "• Шрифт и тема редактора запоминаются (config/editor.json).\n"
                    "• «Новый файл» подставляет шаблон под расширение (index.html, style.css и т.д.).",
                "sql": "БАЗЫ ДАННЫХ — SQL-РЕДАКТОР:\n\n"
                    "Шаг 1. Запустите MariaDB (или PostgreSQL) на вкладке «Основное».\n"
                    "Шаг 2. Вкладка «Дополнительно» → «SQL». Слева выберите движок, введите логин/пароль\n"
                    "(MariaDB: root без пароля; PostgreSQL: postgres).\n"
                    "Шаг 3. Напишите запрос слева, нажмите «Выполнить» — результат появится в таблице справа.\n"
                    "Шаг 4. Примеры: SHOW DATABASES;  CREATE DATABASE mysite CHARACTER SET utf8mb4;\n"
                    "   CREATE USER 'mysite'@'localhost' IDENTIFIED BY 'secret';\n"
                    "   GRANT ALL ON mysite.* TO 'mysite'@'localhost';\n"
                    "Шаг 5. Для визуальной работы нажмите «phpMyAdmin» — откроется веб-панель\n"
                    "по адресу http://127.0.0.1:8080/phpmyadmin/ (root без пароля).",
                "ssl": "SSL (HTTPS) — ПОШАГОВО:\n\n"
                    "Шаг 1. Убедитесь, что интернет доступен (нужно скачать mkcert ~5 МБ).\n"
                    "Шаг 2. Нажмите «Настроить SSL» на панели действий.\n"
                    "Шаг 3. Программа скачает mkcert, установит локальный корневой сертификат (Windows спросит\n"
                    "разрешение один раз) и выпустит сертификат для localhost, 127.0.0.1 и ::1.\n"
                    "Шаг 4. Файлы появятся в папке ssl/: localhost.pem и localhost-key.pem.\n"
                    "Шаг 5. Перезапустите Nginx — сайт станет доступен по https://localhost/ (порт 443).\n"
                    "Браузер больше не будет ругаться на «ненадёжное соединение», т.к. корневой сертификат\n"
                    "mkcert добавлен в доверенные.",
                "docker": "DOCKER — ПОШАГОВО:\n\n"
                    "Шаг 1. Карточка Docker показывает, найден ли Docker в системе (проверка раз в 15 секунд\n"
                    "в фоне, чтобы не тормозить интерфейс).\n"
                    "Шаг 2. Если Docker Desktop не установлен — при нажатии СТАРТ появится предложение\n"
                    "установить его с официального сайта https://docker.com/products/docker-desktop.\n"
                    "Шаг 3. Установите Docker Desktop, перезапустите компьютер (требуется для WSL2),\n"
                    "запустите Docker Desktop и дождитесь статуса «Running».\n"
                    "Шаг 4. Карточка Docker в LockSer станет зелёной — Docker доступен.\n"
                    "Шаг 5. Контейнерами управляйте через терминал: docker ps (список), docker stop <имя>,\n"
                    "docker compose up -d (запуск проекта с docker-compose.yml).",
                "node": "NODE.JS — СЕРВЕРЫ, А НЕ ТОЛЬКО СКРИПТЫ:\n\n"
                    "Шаг 1. Вкладка «Проекты» → «Node.js». Укажите имя, каталог проекта, файл (server.js\n"
                    "или server.ts) и порт (например 3000). Каталог можно выбрать кнопкой «Обзор».\n"
                    "Шаг 2. Нажмите СТАРТ: приложение запустит сервер (для .ts — через tsx), дождётся порта\n"
                    "и пропишет роут /node/3000/ в конфиг Nginx. Статус, PID и время — в таблице.\n"
                    "Шаг 3. Откройте сайт: кнопка «Открыть сайт» ведёт на http://127.0.0.1:3000/,\n"
                    "а через Nginx он же доступен по http://127.0.0.1:80/node/3000/.\n"
                    "Шаг 4. СТОП/РЕСТАРТ управляют сервером; удаление стирает и определение, и процесс.\n"
                    "Определения хранятся в config/node.json.\n"
                    "Шаг 5. Переменная окружения PORT автоматически равна порту сервера — используйте\n"
                    "process.env.PORT в коде. Все Node-процессы убиваются при выходе из программы.",
                "perf": "НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ:\n\n"
                    "Шаг 1. Вкладка «Мониторинг» → «Нагрузка». Цель по умолчанию — ваш Apache.\n"
                    "Шаг 2. Выберите профиль: Quick (10/15с), Normal (50/60с), Stress (200/180с),\n"
                    "Spike (300/60с — резкий наплыв), Soak (50/1800с — поиск утечек) или Custom.\n"
                    "Шаг 3. Список запросов «МЕТОД путь [вес]», например «GET /catalog 20» — нагрузка\n"
                    "распределится по весам. POST шлёт тестовое тело.\n"
                    "Шаг 4. Одна кнопка СТАРТ/СТОП (перекрашивается). Во время теста: RPS, OK %, ошибки,\n"
                    "Avg/P50/P95/P99, CPU/RAM и живой график (зелёный — RPS, оранжевый — P95).\n"
                    "Шаг 5. Кнопка Auto сама прогоняет стадии 10→25→50→100→200 и печатает таблицу пределов\n"
                    "плюс «Stable max». Кнопка «В эталон» фиксирует результат для сравнения A/B:\n"
                    "поменяли конфиг — прогнали — видите ΔRPS/ΔP95. «Сохранить отчёт» пишет .txt.\n"
                    "Защита: нелокальные адреса требуют подтверждения.",
                "perf_chart": "ГРАФИК И МЕТРИКИ — КАК ЧИТАТЬ:\n\n"
                    "Зелёная линия — RPS (запросов в секунду, левая шкала).\n"
                    "Оранжевая линия — P95 задержек в мс (своя шкала).\n"
                    "Ломаная линия — это нормально: каждая точка = реальная 1-секундная выборка,\n"
                    "а локальные задержки естественно дрожат (GC, планировщик, TCP).\n"
                    "Зубец ВВЕРХ на зелёной — всплеск завершений (например, выход из просадки).\n"
                    "Зубец ВНИЗ на зелёной — просадка: запросы встали (сервер насыщен, таймауты в очереди).\n"
                    "Зубец ВВЕРХ на оранжевой — мгновенная деградация задержек; смотрите ту же секунду\n"
                    "на зелёной и CPU: если дёрнулись обе — упёрлись в предел сервера или машины.\n"
                    "Плоская оранжевая около нуля при падающей зелёной — массовые таймауты (лимит 10с).\n\n"
                    "MЕТРИКИ:\n"
                    "RPS — выполненных запросов в секунду. OK % — доля ответов со статусом < 400.\n"
                    "ERR — ошибки (4xx/5xx, таймауты, обрывы). Avg — средняя задержка за весь тест.\n"
                    "P50/P95/P99 — 50/95/99% запросов были быстрее этого значения.\n"
                    "CPU % / RAM GB — нагрузка ВСЕЙ системы (включая процесс генератора), опрос ~раз в 3с.\n"
                    "Users — активные виртуальные пользователи. MB/s — пропускная способность.\n"
                    "Peak — лучший секундный RPS за сессию.\n\n"
                    "ПРОФИЛИ: Quick 10/15с, Normal 50/60с, Stress 200/180с, Spike 300/60с (резкий наплыв),\n"
                    "Soak 50/1800с (утечки на дистанции), Endurance 100/7200с, Custom — свои значения.\n"
                    "Лимит — 10 000 пользователей, но ОС-потоков не более 2000 (предел указан в логе).\n"
                    "В лог каждые 10 секунд пишется строка прогресса, в конце — детальная сводка.\n"
                    "Кнопка «Сохранить отчёт» пишет .txt: конфиг, сводку, глоссарий, таблицу Auto-стадий\n"
                    "и ПОЛНЫЙ посекундный таймлайн теста с пояснениями.",
                "env": "ОКРУЖЕНИЕ И ВИРТУАЛЬНЫЕ ХОСТЫ:\n\n"
                    "Версии: в Настройках секция «Окружение» — PHP 8.2/8.3/8.4 и Node.js 20/22/24.\n"
                    "«Применить» скачивает сборку, ставит поверх runtime, запоминает выбор и рестартует PHP.\n"
                    "Рядом всегда видны реально установленные версии и инструменты (Composer/npm/Git).\n"
                    "Режим PHP (Development/Safe) и листинг каталогов — ряд выше: Safe гасит display_errors,\n"
                    "листинг по умолчанию выключен (Options -Indexes).\n"
                    "Apache слушает только 127.0.0.1 — наружу торчит лишь Nginx (:80/:443).\n"
                    "Сайты: тип php/node/static + HTTPS. Создание сайта само пишет Nginx-блок,\n"
                    "Apache VirtualHost, запись в hosts и выпускает сертификат на домен — получаете\n"
                    "https://мойпроект.local без ручных правок (hosts требует запуска от администратора).",
            },
            "en": {
                "overview": "LockSer — portable local development environment for Windows.\n\n"
                    "INCLUDED:\n"
                    "• Apache — web server (HTTP, port 8080)\n"
                    "• MariaDB — MySQL-compatible database (port 3306)\n"
                    "• PHP — server-side language (FastCGI, port 9074)\n"
                    "• PostgreSQL — advanced DBMS (port 5432)\n"
                    "• Redis — in-memory key-value store (port 6379)\n"
                    "• Nginx — reverse proxy and load balancer (port 80)\n"
                    "• Node.js — runs JavaScript/TypeScript scripts\n"
                    "• Docker — availability and status check\n"
                    "• phpMyAdmin — web panel for MySQL/MariaDB\n\n"
                    "HOW IT WORKS:\n"
                    "• Everything lives in runtime/ next to the program — nothing is installed into the system.\n"
                    "• The 'Main' tab holds service cards: green badge RUNNING, red STOPPED.\n"
                    "• The 'Advanced' tab holds logs, files, SQL editor, sites, tasks and settings.\n"
                    "• Switch UI language with the flags in the header (RU/EN/ES/DE/FR/ZH); the choice is saved.\n"
                    "• Closing the window minimizes to tray. Full exit is via the tray menu.",
                "services": "MANAGING SERVICES — STEP BY STEP:\n\n"
                    "1. START ONE SERVICE: press START on its card. Wait for the green RUNNING badge\n"
                    "   and a log line such as 'Apache started on port 8080'.\n"
                    "2. STOP: press STOP on the card. The badge turns red.\n"
                    "3. RESTART (orange button): stops and starts the service again.\n"
                    "   Handy after editing configs.\n"
                    "4. START ALL / STOP ALL in the header start everything in order:\n"
                    "   PHP → MariaDB → PostgreSQL → Redis → Apache → Nginx.\n"
                    "5. If a port is busy, you get an error naming the process and PID.\n"
                    "   Close that program or change the port in config/server.json and restart.\n\n"
                    "DEFAULT PORTS:\n"
                    "• Apache 8080 — site: http://127.0.0.1:8080/\n"
                    "• MariaDB 3306 — login root, empty password (first run)\n"
                    "• PHP FastCGI 9074 — internal bridge between Apache and PHP\n"
                    "• PostgreSQL 5432 — user postgres\n"
                    "• Redis 6379 — no password required\n"
                    "• Nginx 80 — needs administrator rights (port below 1024)\n\n"
                    "TIP: hover any button to see a tooltip.",
                "quickstart": "QUICK START — YOUR FIRST SITE IN 5 STEPS:\n\n"
                    "Step 1. On first launch a wizard opens: tick the components you need\n"
                    "and press 'Install'. Archives are downloaded into downloads/ (see Settings).\n"
                    "Step 2. Press 'START ALL' in the header. All badges should turn green.\n"
                    "Step 3. Open http://127.0.0.1:8080/ in your browser — the welcome page appears.\n"
                    "Step 4. Drop your project into www/ (e.g. www/mysite/index.php) —\n"
                    "it is instantly served at http://127.0.0.1:8080/mysite/.\n"
                    "Step 5. Test PHP: create www/info.php containing <?php phpinfo(); ?>\n"
                    "and open http://127.0.0.1:8080/info.php.\n\n"
                    "COMMON ISSUES:\n"
                    "• 'Port busy' — close Skype/IIS/another server or change the port.\n"
                    "• Blank PHP page — make sure both Apache and PHP are running.\n"
                    "• Error details live in the 'Apache/PHP/MariaDB Error' log tabs.",
                "sites": "SITES — ADD AND OPEN:\n\n"
                    "Step 1. 'Advanced' tab → 'Sites' → 'Add Site' button.\n"
                    "Step 2. Enter a name (e.g. mysite) — folder www/mysite/ with index.html is created.\n"
                    "Step 3. Keep the domain mysite.localhost and leave the port empty.\n"
                    "Step 4. Select the site and press 'Open Site' — it opens in the browser\n"
                    "at http://127.0.0.1:8080/mysite/.\n"
                    "Step 5. 'Open Folder' shows the site files in Explorer.\n\n"
                    "FILES:\n"
                    "• The 'Files' tab is a built-in manager: double-click opens folders/files,\n"
                    "'Edit' opens code with syntax highlighting (PHP, HTML, CSS, JS, TS, Python).\n"
                    "• Editor font and theme are remembered (config/editor.json).\n"
                    "• 'New File' inserts a template matching the extension.",
                "sql": "DATABASES — SQL EDITOR:\n\n"
                    "Step 1. Start MariaDB (or PostgreSQL) on the 'Main' tab.\n"
                    "Step 2. 'Advanced' tab → 'SQL'. Pick the engine, enter login/password\n"
                    "(MariaDB: root with empty password; PostgreSQL: postgres).\n"
                    "Step 3. Type a query on the left, press 'Execute' — results appear in the table.\n"
                    "Step 4. Examples: SHOW DATABASES;  CREATE DATABASE mysite CHARACTER SET utf8mb4;\n"
                    "   CREATE USER 'mysite'@'localhost' IDENTIFIED BY 'secret';\n"
                    "   GRANT ALL ON mysite.* TO 'mysite'@'localhost';\n"
                    "Step 5. For visual work press 'phpMyAdmin' — the panel opens at\n"
                    "http://127.0.0.1:8080/phpmyadmin/ (root, no password).",
                "ssl": "SSL (HTTPS) — STEP BY STEP:\n\n"
                    "Step 1. Make sure you are online (mkcert download, ~5 MB).\n"
                    "Step 2. Press 'Setup SSL' in the action bar.\n"
                    "Step 3. The app downloads mkcert, installs the local root certificate (Windows asks\n"
                    "permission once) and issues a certificate for localhost, 127.0.0.1 and ::1.\n"
                    "Step 4. Files appear in ssl/: localhost.pem and localhost-key.pem.\n"
                    "Step 5. Restart Nginx — the site becomes available at https://localhost/ (port 443)\n"
                    "with no browser warnings, because the mkcert root is trusted.",
                "docker": "DOCKER — STEP BY STEP:\n\n"
                    "Step 1. The Docker card shows whether Docker is present (checked in background\n"
                    "every 15 seconds so the UI never freezes).\n"
                    "Step 2. If Docker Desktop is missing, pressing START offers to install it from\n"
                    "https://docker.com/products/docker-desktop.\n"
                    "Step 3. Install Docker Desktop, reboot (required for WSL2),\n"
                    "start Docker Desktop and wait for 'Running'.\n"
                    "Step 4. The Docker card in LockSer turns green — Docker is available.\n"
                    "Step 5. Manage containers in a terminal: docker ps (list), docker stop <name>,\n"
                    "docker compose up -d (start a docker-compose.yml project).",
                "node": "NODE.JS — SERVERS, NOT JUST SCRIPTS:\n\n"
                    "Step 1. 'Projects' tab → 'Node.js'. Set name, project folder, entry file (server.js\n"
                    "or server.ts) and port (e.g. 3000).\n"
                    "Step 2. Press START: the app launches the server (.ts via tsx), waits for the port\n"
                    "and adds a /node/3000/ route to the Nginx config. Status, PID and time are in the table.\n"
                    "Step 3. Open it: 'Open Site' goes to http://127.0.0.1:3000/, also reachable via\n"
                    "http://127.0.0.1:80/node/3000/ through Nginx.\n"
                    "Step 4. STOP/RESTART control the server; Remove deletes the definition and the process.\n"
                    "Definitions live in config/node.json.\n"
                    "Step 5. The PORT env variable always equals the server port — use process.env.PORT.\n"
                    "All Node processes are killed on application exit.",
                "perf": "LOAD TESTING:\n\n"
                    "Step 1. 'Monitor' tab → 'Load Test'. The default target is your Apache.\n"
                    "Step 2. Pick a profile: Quick (10/15s), Normal (50/60s), Stress (200/180s),\n"
                    "Spike (300/60s), Soak (50/1800s) or Custom.\n"
                    "Step 3. Request list 'METHOD path [weight]', e.g. 'GET /catalog 20'. POST sends a body.\n"
                    "Step 4. One START/STOP toggle button. Live: RPS, OK %, errors, Avg/P50/P95/P99,\n"
                    "CPU/RAM and a live chart (green — RPS, orange — P95).\n"
                    "Step 5. 'Auto' runs stages 10→25→50→100→200 and prints the limits table plus\n"
                    "'Stable max'. 'Set baseline' pins a result for A/B comparison: change config,\n"
                    "re-run, see ΔRPS/ΔP95. 'Save report' writes a .txt. Non-local targets need confirmation.",
                "perf_chart": "CHART AND METRICS — HOW TO READ:\n\n"
                    "Green line — RPS (requests per second). Orange line — P95 latency in ms (own scale).\n"
                    "A jagged line is normal: every point is a real 1-second sample, and localhost\n"
                    "latency naturally jitters (GC, scheduler, TCP).\n"
                    "UP spike on green — burst of completions (e.g. recovery after a stall).\n"
                    "DOWN spike on green — stall: requests queued (server saturated, timeouts piling up).\n"
                    "UP spike on orange — momentary latency degradation; check the same second on green\n"
                    "and CPU: if both spiked, the server (or the machine) hit a limit.\n"
                    "Flat orange near zero with falling green — mass timeouts (10s cap each).\n\n"
                    "METRICS:\n"
                    "RPS — completed requests per second. OK % — share of responses with status < 400.\n"
                    "ERR — failures (4xx/5xx, timeouts, broken connections). Avg — mean latency.\n"
                    "P50/P95/P99 — 50/95/99% of requests were faster than this.\n"
                    "CPU % / RAM GB — WHOLE system load incl. the generator process, sampled ~every 3s.\n"
                    "Users — active virtual users. MB/s — throughput. Peak — best 1-second RPS.\n\n"
                    "PROFILES: Quick 10/15s, Normal 50/60s, Stress 200/180s, Spike 300/60s,\n"
                    "Soak 50/1800s, Endurance 100/7200s, Custom — your values.\n"
                    "Limit — 10,000 users, max 2,000 OS threads (stated in the log).\n"
                    "A progress line is logged every 10 seconds, plus a detailed summary at the end.\n"
                    "'Save report' writes a .txt: setup, summary, glossary, Auto stages table\n"
                    "and the FULL per-second timeline with explanations.",
                "env": "ENVIRONMENT AND VIRTUAL HOSTS:\n\n"
                    "Versions: Settings → 'Environment' — PHP 8.2/8.3/8.4 and Node.js 20/22/24.\n"
                    "'Apply' downloads the build, installs over runtime/, remembers the choice and restarts PHP.\n"
                    "Detected versions and tools (Composer/npm/Git) are always visible.\n"
                    "PHP mode (Development/Safe) and directory listing are one row above: Safe turns\n"
                    "display_errors off, listing defaults to off (Options -Indexes).\n"
                    "Apache listens on 127.0.0.1 only — only Nginx (:80/:443) faces outward.\n"
                    "Sites: php/node/static type + HTTPS. Creating a site writes the Nginx block,\n"
                    "the Apache VirtualHost, the hosts entry and issues the domain certificate — you get\n"
                    "https://myproject.local with no manual edits (hosts needs administrator run).",
            },
            "es": {
                "overview": "LockSer — entorno de desarrollo local portátil para Windows.\n\n"
                    "INCLUYE: Apache (8080), MariaDB (3306), PHP FastCGI (9074), PostgreSQL (5432),\n"
                    "Redis (6379), Nginx (80), Node.js, Docker, SSL y phpMyAdmin.\n\n"
                    "Todo vive en runtime/ junto al programa, sin instalación en el sistema.\n"
                    "Pestaña «Principal»: tarjetas de servicios (verde = en ejecución).\n"
                    "Pestaña «Adicional»: registros, archivos, editor SQL, sitios, tareas y ajustes.\n"
                    "El idioma se cambia con las banderas del encabezado y se guarda.",
                "services": "GESTIÓN DE SERVICIOS:\n\n"
                    "1. INICIAR en la tarjeta → espere el distintivo verde EN EJECUCIÓN.\n"
                    "2. DETENER detiene el servicio. REINICIAR (naranja) lo reinicia.\n"
                    "3. INICIAR TODO / DETENER TODO: orden automático\n"
                    "   PHP → MariaDB → PostgreSQL → Redis → Apache → Nginx.\n"
                    "4. Si un puerto está ocupado, el error indica el proceso y el PID.\n"
                    "   Cierre ese programa o cambie el puerto en config/server.json.\n"
                    "Puertos: Apache 8080, MariaDB 3306 (root sin contraseña),\n"
                    "PostgreSQL 5432, Redis 6379, Nginx 80 (requiere administrador).",
                "quickstart": "INICIO RÁPIDO EN 5 PASOS:\n\n"
                    "Paso 1. En el primer inicio marque los componentes y pulse «Instalar».\n"
                    "Paso 2. Pulse «INICIAR TODO». Todos los distintivos en verde.\n"
                    "Paso 3. Abra http://127.0.0.1:8080/ en el navegador.\n"
                    "Paso 4. Copie su proyecto a www/ (p. ej. www/mysite/index.php) —\n"
                    "estará en http://127.0.0.1:8080/mysite/.\n"
                    "Paso 5. Pruebe PHP con www/info.php que contenga <?php phpinfo(); ?>.",
                "sites": "SITIOS Y ARCHIVOS:\n\n"
                    "1. «Adicional» → «Sitios» → «Agregar sitio», escriba el nombre.\n"
                    "2. «Abrir sitio» lo abre en el navegador (http://127.0.0.1:8080/nombre/).\n"
                    "3. «Abrir carpeta» muestra los archivos en el Explorador.\n"
                    "4. Pestaña «Archivos»: doble clic abre, «Editar» abre código con resaltado\n"
                    "(PHP, HTML, CSS, JS, TS, Python). La fuente y el tema se recuerdan.",
                "sql": "BASES DE DATOS:\n\n"
                    "1. Inicie MariaDB (o PostgreSQL) en «Principal».\n"
                    "2. «Adicional» → «SQL»: elija el motor e indique usuario/clave\n"
                    "(MariaDB: root sin clave; PostgreSQL: postgres).\n"
                    "3. Escriba la consulta y pulse «Ejecutar»; el resultado sale a la derecha.\n"
                    "4. O pulse «phpMyAdmin»: http://127.0.0.1:8080/phpmyadmin/.",
                "ssl": "SSL (HTTPS):\n\n"
                    "1. Pulse «Configurar SSL» (requiere internet, ~5 MB).\n"
                    "2. Se descarga mkcert, se instala el certificado raíz local\n"
                    "(Windows pide permiso una vez) y se emite el certificado.\n"
                    "3. Archivos en ssl/: localhost.pem y localhost-key.pem.\n"
                    "4. Reinicie Nginx — https://localhost/ funcionará sin avisos.",
                "docker": "DOCKER:\n\n"
                    "1. La tarjeta muestra si Docker está presente (verificación en fondo cada 15 s).\n"
                    "2. Si falta, al pulsar INICIAR se ofrece instalar Docker Desktop.\n"
                    "3. Instale Docker Desktop, reinicie el PC (WSL2), inicie Docker Desktop.\n"
                    "4. Comandos: docker ps, docker stop <nombre>, docker compose up -d.",
            },
            "de": {
                "overview": "LockSer — portable lokale Entwicklungsumgebung für Windows.\n\n"
                    "ENTHALTEN: Apache (8080), MariaDB (3306), PHP FastCGI (9074), PostgreSQL (5432),\n"
                    "Redis (6379), Nginx (80), Node.js, Docker, SSL und phpMyAdmin.\n\n"
                    "Alles liegt in runtime/ neben dem Programm — keine Systeminstallation.\n"
                    "Reiter «Haupt»: Dienst-Karten (grün = läuft).\n"
                    "Reiter «Erweitert»: Logs, Dateien, SQL-Editor, Sites, Aufgaben, Einstellungen.\n"
                    "Die Sprache wird über die Flaggen in der Kopfzeile umgeschaltet und gespeichert.",
                "services": "DIENSTE VERWALTEN:\n\n"
                    "1. STARTEN auf der Karte → grüne Anzeige LÄUFT abwarten.\n"
                    "2. STOPPEN hält den Dienst an. NEUSTART (orange) startet neu.\n"
                    "3. ALLE STARTEN / ALLE STOPPEN: automatische Reihenfolge\n"
                    "   PHP → MariaDB → PostgreSQL → Redis → Apache → Nginx.\n"
                    "4. Ist ein Port belegt, nennt der Fehler Prozess und PID.\n"
                    "   Fremdes Programm schließen oder Port in config/server.json ändern.\n"
                    "Ports: Apache 8080, MariaDB 3306 (root ohne Passwort),\n"
                    "PostgreSQL 5432, Redis 6379, Nginx 80 (braucht Admin-Rechte).",
                "quickstart": "SCHNELLSTART IN 5 SCHRITTEN:\n\n"
                    "Schritt 1. Beim ersten Start Komponenten ankreuzen und «Installieren».\n"
                    "Schritt 2. «ALLE STARTEN» — alle Anzeigen werden grün.\n"
                    "Schritt 3. http://127.0.0.1:8080/ im Browser öffnen.\n"
                    "Schritt 4. Projekt nach www/ kopieren (z. B. www/mysite/index.php) —\n"
                    "erreichbar unter http://127.0.0.1:8080/mysite/.\n"
                    "Schritt 5. PHP testen: www/info.php mit <?php phpinfo(); ?> anlegen.",
                "sites": "SITES UND DATEIEN:\n\n"
                    "1. «Erweitert» → «Sites» → «Site hinzufügen», Namen eingeben.\n"
                    "2. «Seite öffnen» öffnet sie im Browser (http://127.0.0.1:8080/name/).\n"
                    "3. «Ordner öffnen» zeigt die Dateien im Explorer.\n"
                    "4. Reiter «Dateien»: Doppelklick öffnet, «Bearbeiten» öffnet Code\n"
                    "mit Highlighting (PHP, HTML, CSS, JS, TS, Python). Schrift und Theme\n"
                    "werden gespeichert.",
                "sql": "DATENBANKEN:\n\n"
                    "1. MariaDB (oder PostgreSQL) unter «Haupt» starten.\n"
                    "2. «Erweitert» → «SQL»: Engine wählen, Benutzer/Passwort eingeben\n"
                    "(MariaDB: root ohne Passwort; PostgreSQL: postgres).\n"
                    "3. Abfrage schreiben, «Ausführen» — Ergebnis erscheint rechts.\n"
                    "4. Oder «phpMyAdmin»: http://127.0.0.1:8080/phpmyadmin/.",
                "ssl": "SSL (HTTPS):\n\n"
                    "1. «SSL einrichten» klicken (Internet nötig, ~5 MB).\n"
                    "2. mkcert wird geladen, Root-Zertifikat installiert\n"
                    "(Windows fragt einmal um Erlaubnis), Zertifikat ausgestellt.\n"
                    "3. Dateien in ssl/: localhost.pem und localhost-key.pem.\n"
                    "4. Nginx neu starten — https://localhost/ läuft ohne Warnungen.",
                "docker": "DOCKER:\n\n"
                    "1. Die Karte zeigt, ob Docker vorhanden ist (Prüfung alle 15 s im Hintergrund).\n"
                    "2. Fehlt Docker, bietet STARTEN die Installation von Docker Desktop an.\n"
                    "3. Docker Desktop installieren, PC neu starten (WSL2), Docker Desktop starten.\n"
                    "4. Befehle: docker ps, docker stop <name>, docker compose up -d.",
            },
            "fr": {
                "overview": "LockSer — environnement de développement local portable pour Windows.\n\n"
                    "INCLUS : Apache (8080), MariaDB (3306), PHP FastCGI (9074), PostgreSQL (5432),\n"
                    "Redis (6379), Nginx (80), Node.js, Docker, SSL et phpMyAdmin.\n\n"
                    "Tout vit dans runtime/ à côté du programme, sans installation système.\n"
                    "Onglet « Principal » : cartes des services (vert = en exécution).\n"
                    "Onglet « Avancé » : logs, fichiers, éditeur SQL, sites, tâches, paramètres.\n"
                    "La langue se change avec les drapeaux de l'en-tête et est mémorisée.",
                "services": "GÉRER LES SERVICES :\n\n"
                    "1. DÉMARRER sur la carte → attendre le badge vert EN EXÉCUTION.\n"
                    "2. ARRÊTER stoppe le service. REDÉMARRER (orange) le relance.\n"
                    "3. TOUT DÉMARRER / TOUT ARRÊTER : ordre automatique\n"
                    "   PHP → MariaDB → PostgreSQL → Redis → Apache → Nginx.\n"
                    "4. Si un port est occupé, l'erreur nomme le processus et le PID.\n"
                    "   Fermez ce programme ou changez le port dans config/server.json.\n"
                    "Ports : Apache 8080, MariaDB 3306 (root sans mot de passe),\n"
                    "PostgreSQL 5432, Redis 6379, Nginx 80 (droits admin requis).",
                "quickstart": "DÉMARRAGE RAPIDE EN 5 ÉTAPES :\n\n"
                    "Étape 1. Au premier lancement, cochez les composants puis « Installer ».\n"
                    "Étape 2. Cliquez « TOUT DÉMARRER ». Tous les badges passent au vert.\n"
                    "Étape 3. Ouvrez http://127.0.0.1:8080/ dans le navigateur.\n"
                    "Étape 4. Copiez votre projet dans www/ (ex. www/monsite/index.php) —\n"
                    "disponible sur http://127.0.0.1:8080/monsite/.\n"
                    "Étape 5. Testez PHP avec www/info.php contenant <?php phpinfo(); ?>.",
                "sites": "SITES ET FICHIERS :\n\n"
                    "1. « Avancé » → « Sites » → « Ajouter un site », saisissez le nom.\n"
                    "2. « Ouvrir le site » l'ouvre dans le navigateur (http://127.0.0.1:8080/nom/).\n"
                    "3. « Ouvrir le dossier » montre les fichiers dans l'Explorateur.\n"
                    "4. Onglet « Fichiers » : double-clic pour ouvrir, « Modifier » pour le code\n"
                    "avec coloration (PHP, HTML, CSS, JS, TS, Python). Police et thème mémorisés.",
                "sql": "BASES DE DONNÉES :\n\n"
                    "1. Démarrez MariaDB (ou PostgreSQL) dans « Principal ».\n"
                    "2. « Avancé » → « SQL » : choisissez le moteur, saisissez login/mot de passe\n"
                    "(MariaDB : root sans mot de passe ; PostgreSQL : postgres).\n"
                    "3. Écrivez la requête, « Exécuter » — le résultat s'affiche à droite.\n"
                    "4. Ou « phpMyAdmin » : http://127.0.0.1:8080/phpmyadmin/.",
                "ssl": "SSL (HTTPS) :\n\n"
                    "1. Cliquez « Configurer SSL » (internet requis, ~5 Mo).\n"
                    "2. mkcert est téléchargé, le certificat racine local est installé\n"
                    "(Windows demande une fois), le certificat est émis.\n"
                    "3. Fichiers dans ssl/ : localhost.pem et localhost-key.pem.\n"
                    "4. Redémarrez Nginx — https://localhost/ fonctionne sans alertes.",
                "docker": "DOCKER :\n\n"
                    "1. La carte indique si Docker est présent (vérification en fond toutes les 15 s).\n"
                    "2. S'il manque, DÉMARRER propose d'installer Docker Desktop.\n"
                    "3. Installez Docker Desktop, redémarrez le PC (WSL2), lancez Docker Desktop.\n"
                    "4. Commandes : docker ps, docker stop <nom>, docker compose up -d.",
            },
            "zh": {
                "overview": "LockSer — Windows 便携式本地开发环境。\n\n"
                    "包含：Apache（8080）、MariaDB（3306）、PHP FastCGI（9074）、PostgreSQL（5432）、\n"
                    "Redis（6379）、Nginx（80）、Node.js、Docker、SSL 和 phpMyAdmin。\n\n"
                    "所有组件位于程序旁的 runtime/ 文件夹中，无需系统安装。\n"
                    "「主要」选项卡：服务卡片（绿色 = 运行中）。\n"
                    "「高级」选项卡：日志、文件、SQL 编辑器、站点、任务和设置。\n"
                    "点击标题栏旗帜切换语言，设置会被记住。",
                "services": "服务管理：\n\n"
                    "1. 点击卡片上的「启动」，等待绿色「运行中」徽章。\n"
                    "2. 「停止」停止服务。橙色「重启」重新启动。\n"
                    "3. 「全部启动 / 全部停止」：自动顺序\n"
                    "   PHP → MariaDB → PostgreSQL → Redis → Apache → Nginx。\n"
                    "4. 端口被占用时，错误会显示进程名和 PID。\n"
                    "   关闭该程序或修改 config/server.json 中的端口。\n"
                    "端口：Apache 8080、MariaDB 3306（root，无密码）、\n"
                    "PostgreSQL 5432、Redis 6379、Nginx 80（需要管理员权限）。",
                "quickstart": "五步快速入门：\n\n"
                    "第 1 步：首次启动时勾选所需组件，点击「安装」。\n"
                    "第 2 步：点击「全部启动」，所有徽章变绿。\n"
                    "第 3 步：在浏览器中打开 http://127.0.0.1:8080/。\n"
                    "第 4 步：将项目复制到 www/（如 www/mysite/index.php）——\n"
                    "即可通过 http://127.0.0.1:8080/mysite/ 访问。\n"
                    "第 5 步：创建 www/info.php（内容 <?php phpinfo(); ?>）测试 PHP。",
                "sites": "站点与文件：\n\n"
                    "1. 「高级」→「站点」→「添加站点」，输入名称。\n"
                    "2. 「打开站点」在浏览器中打开（http://127.0.0.1:8080/名称/）。\n"
                    "3. 「打开文件夹」在资源管理器中显示文件。\n"
                    "4. 「文件」选项卡：双击打开，「编辑」打开代码高亮编辑器\n"
                    "（PHP、HTML、CSS、JS、TS、Python）。字体和主题会被记住。",
                "sql": "数据库：\n\n"
                    "1. 在「主要」选项卡中启动 MariaDB（或 PostgreSQL）。\n"
                    "2. 「高级」→「SQL」：选择引擎，输入用户名/密码\n"
                    "（MariaDB：root 无密码；PostgreSQL：postgres）。\n"
                    "3. 在左侧输入查询，点击「执行」，结果显示在右侧。\n"
                    "4. 或点击「phpMyAdmin」：http://127.0.0.1:8080/phpmyadmin/。",
                "ssl": "SSL（HTTPS）：\n\n"
                    "1. 点击「设置 SSL」（需要联网，约 5 MB）。\n"
                    "2. 下载 mkcert，安装本地根证书（Windows 会请求一次授权），颁发证书。\n"
                    "3. 证书位于 ssl/：localhost.pem 和 localhost-key.pem。\n"
                    "4. 重启 Nginx —— https://localhost/ 不再有警告。",
                "docker": "Docker：\n\n"
                    "1. 卡片显示是否检测到 Docker（后台每 15 秒检查一次）。\n"
                    "2. 未安装时，点击启动会提示安装 Docker Desktop。\n"
                    "3. 安装 Docker Desktop，重启电脑（WSL2），启动 Docker Desktop。\n"
                    "4. 命令：docker ps、docker stop <名称>、docker compose up -d。",
            },
        }

        current_lang = lang.get()
        lang_docs = {**docs.get("en", {}), **docs.get(current_lang, {})}

        sections = [
            (lang.t("tab_system"), "overview"),
            (lang.t("help_btn"), "quickstart"),
            (lang.t("tab_main"), "services"),
            (lang.t("tab_sites"), "sites"),
            (lang.t("tab_sql"), "sql"),
            (lang.t("tab_node"), "node"),
            (lang.t("tab_perf"), "perf"),
            (lang.t("perf_chart_tab"), "perf_chart"),
            (lang.t("tab_settings"), "env"),
            (lang.t("setup_ssl"), "ssl"),
            (lang.t("docker"), "docker"),
        ]

        for section_title, key in sections:
            frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
            nb.add(frame, section_title)
            t = ScrolledText(frame, wrap="word", bg="#0d0f16", fg="#b8bdd0",
                             insertbackground="white", font=("Cascadia Code", 10),
                             relief="flat", bd=0, padx=14, pady=10,
                             selectbackground=THEME["accent"], selectforeground=THEME["white"])
            t.pack(fill="both", expand=True, padx=0, pady=0)
            text = lang_docs.get(key, "").replace("MiniServer", APP_NAME).replace("LockSer", APP_NAME)
            if key == "overview":
                text = lang.t("faraja_meaning") + "\n\n" + text
            t.insert("1.0", text)
            t.configure(state="disabled")

    def _first_run_wizard(self):
        first_run_marker = APP_ROOT / "config" / ".first_run_done"
        if first_run_marker.exists():
            return
        win = tk.Toplevel(self.root)
        win.title(lang.t("first_run_title"))
        win.geometry("600x500")
        win.configure(bg=THEME["bg"])
        win.transient(self.root)
        win.grab_set()
        try:
            win.iconbitmap(str(ICON))
        except Exception:
            pass

        header = tk.Frame(win, bg=THEME["bg"])
        header.pack(fill="x", padx=20, pady=10)
        tk.Label(header, text=lang.t("first_run_title"), bg=THEME["bg"], fg=THEME["accent"],
                 font=(THEME["font_family"], 16, "bold")).pack(side="left")

        tk.Label(win, text=lang.t("first_run_welcome"), bg=THEME["bg"], fg=THEME["text"],
                 font=(THEME["font_family"], 10), wraplength=550, justify="left").pack(
                     fill="x", padx=20, pady=(0, 10))

        components_frame = tk.Frame(win, bg=THEME["bg_elevated"], bd=1, relief="flat",
                                     highlightbackground=THEME["border"], highlightthickness=1)
        components_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(components_frame, text=lang.t("first_run_components"), bg=THEME["bg_elevated"],
                 fg=THEME["text"], font=(THEME["font_family"], 10, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

        comp_vars = {}
        comp_names = ["apache", "php", "mariadb", "postgresql", "redis", "nginx", "nodejs", "phpmyadmin"]
        for name in comp_names:
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(components_frame, text=name.upper(), variable=var,
                               bg=THEME["bg_elevated"], fg=THEME["text"],
                               selectcolor=THEME["bg_input"], activebackground=THEME["bg_elevated"],
                               activeforeground=THEME["text"], font=(THEME["font_family"], 10))
            cb.pack(anchor="w", padx=20, pady=2)
            comp_vars[name] = var

        dir_frame = tk.Frame(win, bg=THEME["bg"])
        dir_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(dir_frame, text=lang.t("first_run_download_dir"), bg=THEME["bg"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(anchor="w")
        dir_inner = tk.Frame(dir_frame, bg=THEME["bg"])
        dir_inner.pack(fill="x", pady=(4, 0))
        download_dir_var = tk.StringVar(value=str(DOWNLOADS))
        tk.Entry(dir_inner, textvariable=download_dir_var, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                 insertbackground=THEME["entry_fg"], font=("Cascadia Code", 9), relief="flat", bd=0).pack(
                     side="left", fill="x", expand=True)
        def browse_dir():
            from tkinter import filedialog
            d = filedialog.askdirectory(initialdir=download_dir_var.get())
            if d:
                download_dir_var.set(d)
        IconButton(dir_inner, "folder", browse_dir, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     size=28, tip=lang.t("first_run_browse") + " — " + lang.t("tip_browse")).pack(side="right", padx=(8, 0))

        btn_frame = tk.Frame(win, bg=THEME["bg"])
        btn_frame.pack(fill="x", padx=20, pady=10)
        def finish():
            selected = [n for n, v in comp_vars.items() if v.get()]
            config_file = APP_ROOT / "config" / "wizard.json"
            config_file.write_text(json.dumps({
                "selected_components": selected,
                "download_dir": download_dir_var.get()
            }, indent=2), encoding="utf-8")
            first_run_marker.parent.mkdir(parents=True, exist_ok=True)
            first_run_marker.write_text("done", encoding="utf-8")
            win.destroy()
            if selected:
                self.log(f"Selected components: {', '.join(selected)}")
                self._install_selected(selected, download_dir_var.get())
        def skip():
            first_run_marker.parent.mkdir(parents=True, exist_ok=True)
            first_run_marker.write_text("done", encoding="utf-8")
            win.destroy()

        StyledButton(btn_frame, lang.t("first_run_install"), finish, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     width=100, height=30, font_size=9).pack(side="left", padx=4)
        StyledButton(btn_frame, lang.t("first_run_skip"), skip, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=100, height=30, font_size=9).pack(side="left", padx=4)

    def _install_selected(self, components, download_dir):
        def w():
            try:
                for n in components:
                    install_component(
                        n, self.log,
                        lambda g, t, s, n=n: self._install_progress(n, g, t, s)
                    )
                self._install_progress("", 0, 0)
                self.log(lang.t("install_complete"))
            except Exception as e:
                self.log("INSTALL ERROR: " + str(e))
        threading.Thread(target=w, daemon=True).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    if "--perf-child" in sys.argv:
        _idx = sys.argv.index("--perf-child")
        run_perf_child(sys.argv[_idx + 1] if _idx + 1 < len(sys.argv) else "")
    else:
        App().run()
