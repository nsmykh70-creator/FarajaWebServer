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
RUNTIME=APP_ROOT/"runtime"; DOWNLOADS=APP_ROOT/"downloads"; LOGS=APP_ROOT/"logs"; PMA=WWW/"phpmyadmin"
for x in (RUNTIME,DOWNLOADS,LOGS,WWW,APP_ROOT/"tmp"): x.mkdir(parents=True,exist_ok=True)

DEFAULT={"apache_port":8080,"mariadb_port":3306,"php_cgi_port":9074,"postgresql_port":5432,"redis_port":6379,"nginx_port":80}
try: CONFIG={**DEFAULT,**json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
except Exception:
    CONFIG=DEFAULT.copy(); CONFIG_FILE.parent.mkdir(parents=True,exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(CONFIG,indent=2),encoding="utf-8")

THEME = {
    "bg": "#0a0f16",
    "bg_card": "#111923",
    "bg_elevated": "#151f2c",
    "bg_input": "#1b2735",
    "border": "#263548",
    "border_light": "#34465d",
    "accent": "#4f8cff",
    "accent_hover": "#6aa2ff",
    "accent_active": "#3975e8",
    "success": "#35d07f",
    "success_dim": "#24965c",
    "danger": "#ff5d6c",
    "danger_dim": "#c83f50",
    "warning": "#f39c12",
    "warning_dim": "#e67e22",
    "info": "#42c6ff",
    "text": "#edf4ff",
    "text_dim": "#9aabc0",
    "text_muted": "#687b91",
    "white": "#ffffff",
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
    "tip_restart_all": {"ru": "Перезапустить все сервисы", "en": "Restart all services", "es": "Reiniciar todos los servicios", "de": "Alle Dienste neu starten", "fr": "Redémarrer tous les services", "zh": "重启所有服务"},
    "tip_start": {"ru": "Запустить / остановить сервис", "en": "Start / stop the service", "es": "Iniciar / detener el servicio", "de": "Dienst starten / stoppen", "fr": "Démarrer / arrêter le service", "zh": "启动 / 停止服务"},
    "tip_restart": {"ru": "Перезапустить сервис", "en": "Restart the service", "es": "Reiniciar el servicio", "de": "Dienst neu starten", "fr": "Redémarrer le service", "zh": "重启服务"},
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
for _entry in LOCALES.values():
    for _code, _text in _entry.items():
        if "MiniServer" in _text:
            _entry[_code] = _text.replace("MiniServer", APP_NAME)
del _entry, _code, _text

def comps(): return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
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


def install_component(name,log,progress):
    item = comps()[name]
    tmp = DOWNLOADS/(name+"_extract")
    shutil.rmtree(tmp,ignore_errors=True)
    tmp.mkdir(parents=True)
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
    def __init__(self,log):self.log=log;self.apache=None;self.db=None;self.php=None;self.pg=None;self.redis_proc=None;self.nginx=None;self.handles=[];self.ui_progress=None
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
    def write_configs(self):
        a=self.ad.resolve().as_posix(); w=WWW.resolve().as_posix(); p=PMA.resolve().as_posix()
        ph=self.pd.resolve().as_posix(); m=self.md.resolve().as_posix(); l=LOGS.resolve().as_posix()
        apache_modules = self._apache_modules()
        apache=f'''ServerRoot "{a}"
Listen {CONFIG["apache_port"]}
ServerName 127.0.0.1:{CONFIG["apache_port"]}

{apache_modules}

TypesConfig conf/mime.types
DocumentRoot "{w}"

<Directory "{w}">
    Require all granted
    AllowOverride All
    Options Indexes FollowSymLinks
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

ErrorLog "{l}/apache-error.log"
CustomLog "{l}/apache-access.log" combined
LogLevel warn
'''
        (self.ad/"conf").mkdir(parents=True,exist_ok=True)
        (self.ad/"conf/httpd.conf").write_text(apache,encoding="utf-8")
        php=f'''[PHP]
extension_dir="{ph}/ext"
extension=mysqli
extension=pdo_mysql
extension=mbstring
extension=curl
display_errors=On
display_startup_errors=On
log_errors=On
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
    def arun(self):return port_open(CONFIG["apache_port"])
    def drun(self):return port_open(CONFIG["mariadb_port"])
    def prun(self):return port_open(CONFIG["php_cgi_port"])
    def start_php(self):
        if self.prun():self.log("PHP CGI is already running");return
        self.write_configs();exe=self.pd/"php-cgi.exe"
        if not exe.exists():raise RuntimeError("PHP is not installed")
        f=self.logfile("php-process.log")
        self.php=subprocess.Popen([str(exe),"-b",f'127.0.0.1:{CONFIG["php_cgi_port"]}',"-c",str(self.pd/"php.ini")],cwd=self.pd,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["php_cgi_port"],15):raise RuntimeError("PHP CGI did not start; see PHP Error / Process logs")
        self.log("PHP CGI started")
    def stop_php(self):
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
        # Apache and Nginx are mutually exclusive in MiniServer.
        if web_server_running("nginx") or self.nginxrun():
            raise RuntimeError("Apache cannot be started while Nginx is running. Stop Nginx first.")
        if self.arun():
            owners = port_owners(CONFIG["apache_port"])
            apache_names = {"httpd.exe", "apache.exe"}
            foreign = [(pid, name) for pid, name in owners if name.lower() not in apache_names]
            if foreign:
                detail = ", ".join(f"{name or 'unknown'} (PID {pid})" for pid, name in foreign)
                raise RuntimeError(
                    f"Port {CONFIG['apache_port']} is occupied by another program: {detail}. "
                    "MiniServer will not terminate another web server automatically. "
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
        self.log("Apache started")
    def stop_apache(self):
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
        self.log("MariaDB started")
        try: self._setup_pma_storage()
        except Exception: pass
    def stop_db(self):
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
    def pgrun(self):return port_open(CONFIG["postgresql_port"])
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
        self.log("PostgreSQL started")
    def stop_pg(self):
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
    def redisrun(self):return port_open(CONFIG["redis_port"])
    def start_redis(self):
        if self.redisrun():self.log("Redis is already running");return
        self._ensure_component("redis")
        exe=self.rdd/"redis-server.exe"
        f=self.logfile("redis-process.log")
        self.redis_proc=subprocess.Popen([str(exe),"--port",str(CONFIG["redis_port"]),"--bind","127.0.0.1","--loglevel","warning"],
            cwd=self.rdd,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["redis_port"],10):raise RuntimeError("Redis did not start; see Process / Init log")
        self.log("Redis started on port %s" % CONFIG["redis_port"])
    def stop_redis(self):
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
    def nginxrun(self):return port_open(CONFIG["nginx_port"])
    def start_nginx(self):
        # Apache and Nginx are mutually exclusive in MiniServer.
        if web_server_running("apache") or self.arun():
            raise RuntimeError("Nginx cannot be started while Apache is running. Stop Apache first.")
        if self.nginxrun():self.log("Nginx is already running");return
        self._ensure_component("nginx")
        exe=self.nd/"nginx.exe"
        self._write_nginx_conf()
        f=self.logfile("nginx-process.log")
        self.nginx=subprocess.Popen([str(exe),"-c",str((self.nd/"conf/nginx.conf").resolve())],
            cwd=self.nd,stdout=f,stderr=f,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if not wait_port(CONFIG["nginx_port"],10):raise RuntimeError("Nginx did not start; see Process / Init log")
        self.log("Nginx started on port %s" % CONFIG["nginx_port"])
    def stop_nginx(self):
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
    def _write_nginx_conf(self):
        www_path = WWW.resolve().as_posix()
        a_port = CONFIG["apache_port"]
        n_port = CONFIG["nginx_port"]
        ssl_dir = APP_ROOT / "ssl"
        ssl_cert = ssl_dir / "localhost.pem"
        ssl_key = ssl_dir / "localhost-key.pem"
        ssl_block = ""
        if ssl_cert.exists() and ssl_key.exists():
            ssl_block = f'''
    server {{
        listen 443 ssl;
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
        conf = f'''worker_processes 1;
events {{ worker_connections 1024; }}
http {{
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    server {{
        listen {n_port};
        server_name localhost;
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
    }}{ssl_block}
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
        return proc
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


class OfficeTabs:
    def __init__(self, parent, active_size=11, passive_size=9):
        self.header = tk.Frame(parent, bg=THEME["bg"])
        self.header.pack(fill="x", padx=12, pady=(8, 0))
        sep = tk.Frame(parent, bg=THEME["border"], height=1)
        sep.pack(fill="x", padx=12, pady=0)
        self.body = tk.Frame(parent, bg=THEME["bg"])
        self.body.pack(fill="both", expand=True)
        self._tabs = []
        self._selected = -1
        self._active_size = active_size
        self._passive_size = passive_size

    def add(self, frame, text):
        idx = len(self._tabs)
        cv = tk.Canvas(self.header, bg=THEME["bg"], highlightthickness=0,
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
        entry = tk.Entry(win, textvariable=var, bg=THEME["bg_input"], fg=THEME["text"],
                         insertbackground=THEME["text"], font=("Cascadia Code", 10),
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

        body = tk.Frame(self.win, bg=self.scheme["bg"])
        body.pack(fill="both", expand=True)

        self._line_numbers = tk.Text(body, width=5, padx=6, pady=8,
                                     bg="#1e1e1e", fg="#858585",
                                     font=(self.font_family, self.font_size),
                                     state="disabled", relief="flat", bd=0,
                                     selectbackground="#1e1e1e", cursor="arrow",
                                     takefocus=0)
        self._line_numbers.pack(side="left", fill="y")

        self._minimap = tk.Text(body, width=16, padx=2, pady=8,
                                bg=self.scheme["bg"], fg=self.scheme["fg"],
                                font=(self.font_family, 2),
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
        self._text.bind("<MouseWheel>", self._on_scroll)
        self._text.bind("<Button-4>", self._on_scroll)
        self._text.bind("<Button-5>", self._on_scroll)
        self._text.bind("<Control-s>", lambda e: self._save())
        self._text.bind("<Tab>", self._handle_tab)

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
        self._text.insert("insert", "    ")
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
        font = (self.font_family, self.font_size)
        self._text.configure(font=font)
        self._line_numbers.configure(font=font)
        try:
            self._minimap.configure(font=(self.font_family, 2))
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


class App:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title(f"{APP_NAME} V14")
        self.root.geometry("1280x860")
        self.root.minsize(1120,750)
        self.root.configure(bg=THEME["bg"])
        try:self.root.iconbitmap(str(ICON))
        except Exception:pass
        self.lines=[];self.svc=Services(self.log);self.tray=None;self.closing=False
        self._pulse = 0
        self._docker_ok = False
        self.build()
        threading.Thread(target=self._docker_poll, daemon=True).start()
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
            mark = tk.Canvas(brand, width=38, height=38, bg=THEME["bg"], highlightthickness=0)
            mark.pack(side="left", padx=(0, 12))
            mark.create_oval(2, 2, 36, 36, fill=THEME["accent"], outline="")
            mark.create_text(19, 19, text="F", fill=THEME["white"], font=(THEME["font_family"], 16, "bold"))
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

        self._toggle_all_btn = StyledButton(controls, lang.t("start_all"), self._toggle_all,
            color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"],
            width=122, height=34, font_size=8)
        self._toggle_all_btn.pack(side="right", padx=(10,0))
        ToolTip(self._toggle_all_btn, lang.t("tip_toggle_all"))
        _restart_all_btn = StyledButton(controls, lang.t("restart_all"), self.restart_all, color=THEME["warning_dim"],
            hover_color=THEME["warning"], active_color="#ba5e17", width=140, height=34, font_size=8)
        _restart_all_btn.pack(side="right", padx=4)
        ToolTip(_restart_all_btn, lang.t("tip_restart_all"))
        _help_btn = StyledButton(controls, lang.t("help_btn"), self._show_help, color=THEME["bg_card"],
            hover_color=THEME["bg_elevated"], active_color=THEME["bg_input"], width=70, height=34, font_size=8)
        _help_btn.pack(side="right", padx=4)
        ToolTip(_help_btn, lang.t("tip_help"))
        self._all_running = False

        self._port_label = tk.Label(parent, text="", bg=THEME["bg_card"], fg=THEME["text_dim"],
                                    font=("Cascadia Code", 8), anchor="w", padx=24, pady=7)
        self._port_label.pack(fill="x")
        self._port_label.configure(text=f"LOCAL SERVICES   •   Apache {CONFIG['apache_port']}   ·   MariaDB {CONFIG['mariadb_port']}   ·   PHP {CONFIG['php_cgi_port']}   ·   PostgreSQL {CONFIG['postgresql_port']}   ·   Redis {CONFIG['redis_port']}   ·   Nginx {CONFIG['nginx_port']}")


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
        icon = tk.Label(top, text=icon_text, bg=THEME["bg_elevated"], fg=THEME["accent"],
                        width=3, height=1, font=("Segoe UI Emoji", 14))
        icon.pack(side="left", padx=(0,10))
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
        toggle_btn = StyledButton(actions, lang.t("start"), lambda a=attr: self._toggle_svc(a),
            color=THEME["success"], hover_color="#55e39a", active_color=THEME["success_dim"],
            width=78, height=27, font_size=7)
        toggle_btn.pack(side="left")
        setattr(self, attr + "_toggle", toggle_btn)
        ToolTip(toggle_btn, lang.t("tip_start"))
        if restart_cmd:
            restart_btn = StyledButton(actions, lang.t("restart"), restart_cmd, color=THEME["warning_dim"],
                hover_color=THEME["warning"], active_color="#ba5e17", width=86, height=27, font_size=7)
            restart_btn.pack(side="left", padx=5); setattr(self, attr + "_restart", restart_btn)
            ToolTip(restart_btn, lang.t("tip_restart"))


    def _action_bar(self, parent):
        shell = tk.Frame(parent, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        shell.pack(fill="x", padx=12, pady=(10,14))
        left = tk.Frame(shell, bg=THEME["bg_card"]); left.pack(side="left", padx=10, pady=9)
        for text, cmd, color, width, tip in [
            (lang.t("open_localhost"), self.localhost, THEME["accent"], 116, lang.t("tip_localhost")),
            (lang.t("phpmyadmin"), self.pma, THEME["info"], 104, lang.t("tip_pma")),
            (lang.t("open_www"), lambda: os.startfile(str(WWW)), THEME["bg_input"], 94, lang.t("tip_www")),
            (lang.t("setup_ssl"), self.setup_ssl_cmd, THEME["warning_dim"], 94, lang.t("tip_ssl")),
            (lang.t("run_script"), self.run_script_cmd, THEME["bg_input"], 96, lang.t("tip_script"))]:
            _ab = StyledButton(left, text, cmd, color=color, hover_color=THEME["border_light"],
                               active_color=THEME["border"], width=width, height=30, font_size=7)
            _ab.pack(side="left", padx=2)
            ToolTip(_ab, tip)
        right = tk.Frame(shell, bg=THEME["bg_card"]); right.pack(side="right", padx=10, pady=9)
        self._progress_label = tk.Label(right, text="", bg=THEME["bg_card"], fg=THEME["text_dim"],
                                         font=("Cascadia Code", 7)); self._progress_label.pack(side="right", padx=5)
        self._progress_bar = ttk.Progressbar(right, mode="determinate", length=130, style="Modern.Horizontal.TProgressbar")
        self._progress_bar.pack(side="right", padx=5)
        _clear_btn = StyledButton(right, lang.t("clear_logs"), self.clear, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"], width=88, height=30, font_size=7)
        _clear_btn.pack(side="right", padx=2)
        ToolTip(_clear_btn, lang.t("tip_clear"))


    def _log_tabs(self, parent):
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

        nb = OfficeTabs(parent, active_size=11, passive_size=9)
        self._extra_nb = nb
        self.views = {}
        self._view_cache = {}
        self._log_stat = {}

        tabs = [
            ("system", lang.t("tab_system"), None),
            ("apache_err", lang.t("tab_apache_err"), LOGS / "apache-error.log"),
            ("php_err", lang.t("tab_php_err"), LOGS / "php-error.log"),
            ("mariadb_err", lang.t("tab_mariadb_err"), LOGS / "mariadb-error.log"),
            ("proc", lang.t("tab_process"), None),
        ]

        for vid, title, path in tabs:
            frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
            nb.add(frame, title)

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

        files_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(files_frame, lang.t('tab_files'))
        self._build_file_manager(files_frame)

        sql_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(sql_frame, lang.t('tab_sql'))
        self._build_sql_editor(sql_frame)

        sites_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(sites_frame, lang.t('tab_sites'))
        self._build_sites_manager(sites_frame)

        tasks_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(tasks_frame, lang.t('tab_tasks'))
        self._build_task_scheduler(tasks_frame)

        settings_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(settings_frame, lang.t('tab_settings'))
        self._build_settings(settings_frame)

        docker_frame = tk.Frame(nb.body, bg=THEME["bg_elevated"])
        nb.add(docker_frame, lang.t('tab_docker'))
        self._build_docker(docker_frame)

    def _build_docker(self, parent):
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        StyledButton(top, lang.t("btn_refresh"), self._dock_refresh, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=100, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("start"), lambda: self._dock_ctl("start"), color=THEME["success"],
                     hover_color="#55e39a", active_color=THEME["success_dim"],
                     width=90, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("stop"), lambda: self._dock_ctl("stop"), color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     width=90, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("restart"), lambda: self._dock_ctl("restart"), color=THEME["warning_dim"],
                     hover_color=THEME["warning"], active_color="#ba5e17",
                     width=100, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_remove"), lambda: self._dock_ctl("rm"), color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=100, height=28, font_size=9).pack(side="left", padx=2)
        cols = ("name", "image", "status", "ports")
        self._dock_tree = ttk.Treeview(parent, columns=cols, show="headings", height=12,
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
        self._dock_status.pack(fill="x", padx=12, pady=(0, 6))
        self._dock_refresh()

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

    def _status_bar(self, parent):
        bar = tk.Frame(parent, bg=THEME["bg_card"], height=30, highlightbackground=THEME["border"], highlightthickness=1)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)
        self.status = tk.StringVar(value=lang.t("status_ready"))
        tk.Label(bar, text="●", bg=THEME["bg_card"], fg=THEME["success"], font=(THEME["font_family"], 9)).pack(side="left", padx=(14,6))
        tk.Label(bar, textvariable=self.status, bg=THEME["bg_card"], fg=THEME["text_dim"],
                 anchor="w", font=(THEME["font_family"], 8)).pack(side="left")
        tk.Label(bar, text="LOCAL  •  READY", bg=THEME["bg_card"], fg=THEME["text_muted"],
                 font=("Cascadia Code", 7, "bold")).pack(side="right", padx=14)


    def build(self):
        self._header(self.root)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TNotebook", background=THEME["bg"], borderwidth=0, tabmargins=[14, 10, 14, 0])
        style.configure("Main.TNotebook.Tab", background=THEME["bg"], foreground=THEME["text_dim"],
                        padding=[20, 11], font=(THEME["font_family"], 9, "bold"), borderwidth=0, focuscolor=THEME["bg"])
        style.map("Main.TNotebook.Tab", background=[("selected", THEME["bg_elevated"]), ("active", THEME["bg_card"])],
                  foreground=[("selected", THEME["accent"]), ("active", THEME["text"])])
        style.configure("Modern.Horizontal.TProgressbar", troughcolor=THEME["bg_input"], background=THEME["accent"],
                        bordercolor=THEME["bg_input"], lightcolor=THEME["accent"], darkcolor=THEME["accent"], thickness=6)
        style.configure("Big.Treeview", background=THEME["bg_elevated"], fieldbackground=THEME["bg_elevated"],
                        foreground=THEME["text"], font=(THEME["font_family"], 10), rowheight=34, borderwidth=0)
        style.map("Big.Treeview", background=[("selected", THEME["accent"])], foreground=[("selected", THEME["white"])])
        style.configure("Big.Treeview.Heading", background=THEME["bg_card"], foreground=THEME["text_dim"],
                        font=(THEME["font_family"], 8, "bold"), relief="flat", padding=[8,8])
        style.map("Big.Treeview.Heading", background=[("active", THEME["bg_input"])])

        main_nb = OfficeTabs(self.root, active_size=12, passive_size=9)
        tab1 = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab1, lang.t('tab_main'))

        services_frame = tk.Frame(tab1, bg=THEME["bg"])
        services_frame.pack(fill="both", expand=True, padx=8, pady=4)
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
        self._action_bar(tab1)

        tab2 = tk.Frame(main_nb.body, bg=THEME["bg"]); main_nb.add(tab2, lang.t('tab_extra'))
        self._log_tabs(tab2)
        self._status_bar(self.root)
        self.svc.ui_progress = self._install_progress


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
        StyledButton(top, lang.t("btn_refresh"), self._fm_refresh, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=100, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_new_folder"), self._fm_mkdir, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=110, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_new_file"), self._fm_newfile, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=100, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_edit"), self._fm_edit, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     width=110, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_delete"), self._fm_delete, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     width=100, height=28, font_size=9).pack(side="left", padx=2)
        self._fm_path = tk.StringVar(value=str(WWW))
        path_entry = tk.Entry(top, textvariable=self._fm_path, bg=THEME["bg_input"],
                              fg=THEME["text"], insertbackground=THEME["text"],
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
        self._fm_refresh()

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
        engine_menu.configure(bg=THEME["bg_input"], fg=THEME["text"], relief="flat",
                             activebackground=THEME["accent"], activeforeground=THEME["white"],
                             font=(THEME["font_family"], 9))
        engine_menu["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
        engine_menu.pack(side="left", padx=5)
        self._sql_user = tk.StringVar(value="root")
        self._sql_pass = tk.StringVar(value="")
        tk.Label(top, text=lang.t("sql_user"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(10, 2))
        tk.Entry(top, textvariable=self._sql_user, bg=THEME["bg_input"], fg=THEME["text"],
                 insertbackground=THEME["text"], font=("Cascadia Code", 9), width=10,
                 relief="flat", bd=0).pack(side="left", padx=2)
        tk.Label(top, text=lang.t("sql_pass"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(10, 2))
        tk.Entry(top, textvariable=self._sql_pass, bg=THEME["bg_input"], fg=THEME["text"],
                 insertbackground=THEME["text"], font=("Cascadia Code", 9), width=10,
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
        StyledButton(btn_frame, lang.t("btn_execute"), self._sql_execute, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     width=96, height=28, font_size=9).pack(side="left", padx=3)
        StyledButton(btn_frame, lang.t("btn_clear"), lambda: self._sql_editor.delete("1.0", "end"),
                     color=THEME["bg_input"], hover_color=THEME["border_light"],
                     active_color=THEME["border"], width=78, height=28, font_size=9).pack(side="left", padx=3)

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
        StyledButton(top, lang.t("btn_add_site"), self._site_add, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     width=120, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_open_site"), self._site_launch, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     width=120, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_remove"), self._site_remove, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     width=100, height=28, font_size=9).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_open_folder"), self._site_open, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=120, height=28, font_size=9).pack(side="left", padx=2)
        cols = ("name", "domain", "root", "port")
        self._site_tree = ttk.Treeview(parent, columns=cols, show="headings", height=10,
                                       style="Big.Treeview")
        self._site_tree.heading("name", text=lang.t("col_site"))
        self._site_tree.heading("domain", text=lang.t("col_domain"))
        self._site_tree.heading("root", text=lang.t("col_root"))
        self._site_tree.heading("port", text=lang.t("col_port"))
        self._site_tree.column("name", width=140)
        self._site_tree.column("domain", width=180)
        self._site_tree.column("root", width=220)
        self._site_tree.column("port", width=70)
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
                                                       s.get("root",""), s.get("port","")))

    def _site_add(self):
        name = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_name"))
        if not name:
            return
        domain = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_domain"),
                                       initial=f"{name}.localhost")
        if domain is None:
            return
        port = DarkPrompt.ask_string(self.root, lang.t("btn_add_site"), lang.t("site_port"))
        if port is None:
            return
        site_root = WWW / name
        site_root.mkdir(parents=True, exist_ok=True)
        index = site_root / "index.html"
        if not index.exists():
            index.write_text(f"<html><body><h1>{name}</h1></body></html>", encoding="utf-8")
        self._sites.append({"name": name, "domain": domain, "root": str(site_root), "port": port})
        self._sites_file.write_text(json.dumps(self._sites, indent=2), encoding="utf-8")
        self._load_sites()
        self.log(f"Site added: {name} -> {domain}")

    def _site_remove(self):
        sel = self._site_tree.selection()
        if not sel:
            return
        vals = self._site_tree.item(sel[0], "values")
        name = vals[0]
        if DarkPrompt.ask_yes_no(self.root, lang.t("btn_remove"), lang.t("confirm_delete_site", name=name)):
            self._sites = [s for s in self._sites if s.get("name") != name]
            self._sites_file.write_text(json.dumps(self._sites, indent=2), encoding="utf-8")
            self._load_sites()

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
        if port:
            url = f"http://127.0.0.1:{port}/"
        else:
            url = f"http://127.0.0.1:{CONFIG['apache_port']}/{name}/"
        self.log(f"Opening site: {url}")
        webbrowser.open(url)

    def _build_task_scheduler(self, parent):
        top = tk.Frame(parent, bg=THEME["bg_elevated"])
        top.pack(fill="x", padx=10, pady=5)
        StyledButton(top, lang.t("btn_add_task"), self._task_add, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     width=80, height=24, font_size=8).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_remove"), self._task_remove, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     width=80, height=24, font_size=8).pack(side="left", padx=2)
        StyledButton(top, lang.t("btn_run_now"), self._task_run, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     width=80, height=24, font_size=8).pack(side="left", padx=2)
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
            if p.is_dir():
                DOWNLOADS = p
        except Exception:
            pass

        title = tk.Label(parent, text=lang.t("set_modules"), bg=THEME["bg_elevated"], fg=THEME["text"],
                         font=(THEME["font_family"], 10, "bold"), anchor="w")
        title.pack(fill="x", padx=12, pady=(8, 2))

        dl = tk.Frame(parent, bg=THEME["bg_elevated"])
        dl.pack(fill="x", padx=10, pady=4)
        tk.Label(dl, text=lang.t("set_dl_folder"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left")
        self._set_dl_var = tk.StringVar(value=str(DOWNLOADS))
        tk.Entry(dl, textvariable=self._set_dl_var, bg=THEME["bg_input"], fg=THEME["text"],
                 insertbackground=THEME["text"], font=("Cascadia Code", 9),
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True, padx=6)
        StyledButton(dl, lang.t("first_run_browse"), self._set_browse_dl, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=80, height=24, font_size=8).pack(side="left", padx=2)
        StyledButton(dl, lang.t("set_open_folder"), self._set_open_dl, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=90, height=24, font_size=8).pack(side="left", padx=2)
        StyledButton(dl, lang.t("set_rescan"), self._set_refresh, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=100, height=24, font_size=8).pack(side="left", padx=2)

        logf = tk.Frame(parent, bg=THEME["bg_elevated"])
        logf.pack(fill="x", padx=10, pady=4)
        tk.Label(logf, text=lang.t("set_logs"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 10, "bold")).pack(side="left")
        tk.Label(logf, text=lang.t("set_font"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(16, 2))
        log_fonts = ["Cascadia Code", "Consolas", "Courier New", "Source Code Pro", "Fira Code", "Segoe UI"]
        if self._settings.get("log_font") not in log_fonts and self._settings.get("log_font"):
            log_fonts.insert(0, self._settings["log_font"])
        self._log_font_var = tk.StringVar(value=self._settings.get("log_font", "Cascadia Code"))
        log_font_menu = tk.OptionMenu(logf, self._log_font_var, *log_fonts,
                                      command=lambda e: self._on_log_font_change())
        log_font_menu.configure(bg=THEME["bg_input"], fg=THEME["text"], relief="flat",
                                activebackground=THEME["accent"], activeforeground=THEME["white"],
                                font=(THEME["font_family"], 9), highlightthickness=0)
        log_font_menu["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
        log_font_menu.pack(side="left", padx=4)
        tk.Label(logf, text=lang.t("set_font_size"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9)).pack(side="left", padx=(12, 2))
        self._log_size_var = tk.StringVar(value=str(self._settings.get("log_size", 9)))
        log_size_menu = tk.OptionMenu(logf, self._log_size_var,
                                      "8", "9", "10", "11", "12", "13", "14", "16",
                                      command=lambda e: self._on_log_font_change())
        log_size_menu.configure(bg=THEME["bg_input"], fg=THEME["text"], relief="flat",
                                activebackground=THEME["accent"], activeforeground=THEME["white"],
                                font=(THEME["font_family"], 9), highlightthickness=0)
        log_size_menu["menu"].configure(bg=THEME["bg_elevated"], fg=THEME["text"])
        log_size_menu.pack(side="left", padx=4)

        # Components are explicitly selected here; installation is never triggered at startup.
        select_box = tk.Frame(parent, bg=THEME["bg_elevated"], highlightbackground=THEME["border"], highlightthickness=1)
        select_box.pack(fill="x", padx=10, pady=(5, 3))
        tk.Label(select_box, text=lang.t("set_select"), bg=THEME["bg_elevated"], fg=THEME["text"],
                 font=(THEME["font_family"], 9, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
        self._set_component_vars = {}
        cb_grid = tk.Frame(select_box, bg=THEME["bg_elevated"])
        cb_grid.pack(fill="x", padx=6, pady=(0, 6))
        try:
            manifest_names = list(comps().keys())
        except Exception:
            manifest_names = ["apache", "php", "mariadb", "postgresql", "redis", "nginx", "nodejs", "phpmyadmin"]
        for idx, name in enumerate(manifest_names):
            var = tk.BooleanVar(value=False)
            self._set_component_vars[name] = var
            cb = tk.Checkbutton(cb_grid, text=name.upper(), variable=var,
                                bg=THEME["bg_elevated"], fg=THEME["text"],
                                selectcolor=THEME["bg_input"], activebackground=THEME["bg_elevated"],
                                activeforeground=THEME["text"], font=(THEME["font_family"], 9),
                                highlightthickness=0, bd=0)
            cb.grid(row=idx // 4, column=idx % 4, sticky="w", padx=8, pady=2)

        cols = ("component", "state", "archive", "expected")
        self._set_tree = ttk.Treeview(parent, columns=cols, show="headings", height=5,
                                       style="Big.Treeview")
        self._set_tree.heading("component", text=lang.t("col_component"))
        self._set_tree.heading("state", text=lang.t("col_state"))
        self._set_tree.heading("archive", text=lang.t("col_archive"))
        self._set_tree.heading("expected", text=lang.t("col_expected"))
        self._set_tree.column("component", width=110)
        self._set_tree.column("state", width=100)
        self._set_tree.column("archive", width=200)
        self._set_tree.column("expected", width=260)
        self._set_tree.pack(fill="x", padx=10, pady=4)

        btns = tk.Frame(parent, bg=THEME["bg_elevated"])
        btns.pack(fill="x", padx=10, pady=4)
        StyledButton(btns, lang.t("set_install_sel"), self._set_install_selected, color=THEME["success"],
                     hover_color="#10d8a0", active_color=THEME["success_dim"],
                     width=140, height=26, font_size=8).pack(side="left", padx=2)
        StyledButton(btns, lang.t("set_install_missing"), self._set_install_missing, color=THEME["info"],
                     hover_color="#2e9bf5", active_color="#0769b5",
                     width=160, height=26, font_size=8).pack(side="left", padx=2)

        prog = tk.Frame(parent, bg=THEME["bg_elevated"])
        prog.pack(fill="x", padx=10, pady=(0, 8))
        self._set_progress = ttk.Progressbar(prog, mode="determinate", length=300,
                                             style="Modern.Horizontal.TProgressbar")
        self._set_progress.pack(side="left", padx=2)
        self._set_progress_label = tk.Label(prog, text="", bg=THEME["bg_elevated"], fg=THEME["text_dim"],
                                            font=(THEME["font_family"], 8))
        self._set_progress_label.pack(side="left", padx=6)
        self._set_refresh()
        self._apply_log_font()

    def _on_log_font_change(self):
        self._settings["log_font"] = self._log_font_var.get()
        try:
            self._settings["log_size"] = int(self._log_size_var.get())
        except ValueError:
            self._settings["log_size"] = 9
        self._save_settings()
        self._apply_log_font()

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
        missing = [n for n, i in manifest.items() if not (APP_ROOT / i["expected"]).exists()]
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

    def _toggle_all(self):
        if self._all_running:
            self.stop_all()
        else:
            self.start_all()

    def _update_toggle_btn(self, attr, running):
        btn = getattr(self, attr + "_toggle")
        if running:
            btn._text = lang.t("stop")
            btn._color = THEME["danger"]
            btn._hover_color = "#ff6b5a"
            btn._active_color = THEME["danger_dim"]
        else:
            btn._text = lang.t("start")
            btn._color = THEME["success"]
            btn._hover_color = "#10d8a0"
            btn._active_color = THEME["success_dim"]
        btn._draw(btn._color)

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

            self._all_running = any([a, d, p, pg, rd, nx])
            if self._all_running:
                self._toggle_all_btn._text = lang.t("stop_all")
                self._toggle_all_btn._color = THEME["danger"]
                self._toggle_all_btn._hover_color = "#ff6b5a"
                self._toggle_all_btn._active_color = THEME["danger_dim"]
            else:
                self._toggle_all_btn._text = lang.t("start_all")
                self._toggle_all_btn._color = THEME["success"]
                self._toggle_all_btn._hover_color = "#10d8a0"
                self._toggle_all_btn._active_color = THEME["success_dim"]
            self._toggle_all_btn._draw(self._toggle_all_btn._color)
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
            self.settext("system", "\n".join(self.lines))
            for vid, (_, p) in self.views.items():
                if p is None:
                    continue
                data = self._read_log_cached(vid, p, 50000)
                if data is not None:
                    self.settext(vid, data)
            parts = []
            changed = False
            for name in ("apache-process.log", "php-process.log", "mariadb-process.log", "mariadb-init.log",
                          "postgresql-process.log", "postgresql-init.log", "redis-process.log", "nginx-process.log"):
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

    def start_a(self): self.worker(self.svc.start_apache, "Starting Apache")
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

    def start_d(self): self.worker(self.svc.start_db, "Starting MariaDB")
    def stop_d(self): self.worker(self.svc.stop_db, "Stopping MariaDB")
    def restart_d(self): self.worker(lambda: (self.svc.stop_db(), self.svc.start_db()), "Restarting MariaDB")
    def start_p(self): self.worker(self.svc.start_php, "Starting PHP")
    def stop_p(self): self.worker(self.svc.stop_php, "Stopping PHP")
    def restart_p(self): self.worker(lambda: (self.svc.stop_php(), self.svc.start_php()), "Restarting PHP")

    def start_pg_ui(self): self.worker(self.svc.start_pg, "Starting PostgreSQL")
    def stop_pg_ui(self): self.worker(self.svc.stop_pg, "Stopping PostgreSQL")
    def restart_pg(self): self.worker(lambda: (self.svc.stop_pg(), self.svc.start_pg()), "Restarting PostgreSQL")

    def start_redis_ui(self): self.worker(self.svc.start_redis, "Starting Redis")
    def stop_redis_ui(self): self.worker(self.svc.stop_redis, "Stopping Redis")
    def restart_redis(self): self.worker(lambda: (self.svc.stop_redis(), self.svc.start_redis()), "Restarting Redis")

    def start_nginx_ui(self): self.worker(self.svc.start_nginx, "Starting Nginx")
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
        missing = [n for n, i in comps().items() if not (APP_ROOT / i["expected"]).exists()]
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
        self.tray = pystray.Icon(APP_NAME, Image.open(tray_image()), f"{APP_NAME} V14", menu)
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

    def _show_help(self):
        win = tk.Toplevel(self.root)
        win.title(lang.t("doc_title"))
        win.geometry("750x600")
        win.configure(bg=THEME["bg"])
        try:
            win.iconbitmap(str(ICON))
        except Exception:
            pass

        header = tk.Frame(win, bg=THEME["bg"])
        header.pack(fill="x", padx=20, pady=10)
        tk.Label(header, text=lang.t("doc_title"), bg=THEME["bg"], fg=THEME["accent"],
                 font=(THEME["font_family"], 16, "bold")).pack(side="left")
        StyledButton(header, "X", win.destroy, color=THEME["danger"],
                     hover_color="#ff6b5a", active_color=THEME["danger_dim"],
                     width=30, height=28, font_size=9).pack(side="right")

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
        lang_docs = docs.get(current_lang, docs["en"])

        sections = [
            (lang.t("tab_system"), "overview"),
            (lang.t("help_btn"), "quickstart"),
            (lang.t("tab_main"), "services"),
            (lang.t("tab_sites"), "sites"),
            (lang.t("tab_sql"), "sql"),
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
            t.insert("1.0", lang_docs.get(key, "").replace("MiniServer", APP_NAME).replace("LockSer", APP_NAME))
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
        tk.Entry(dir_inner, textvariable=download_dir_var, bg=THEME["bg_input"], fg=THEME["text"],
                 insertbackground=THEME["text"], font=("Cascadia Code", 9), relief="flat", bd=0).pack(
                     side="left", fill="x", expand=True)
        def browse_dir():
            from tkinter import filedialog
            d = filedialog.askdirectory(initialdir=download_dir_var.get())
            if d:
                download_dir_var.set(d)
        StyledButton(dir_inner, lang.t("first_run_browse"), browse_dir, color=THEME["bg_input"],
                     hover_color=THEME["border_light"], active_color=THEME["border"],
                     width=80, height=26, font_size=8).pack(side="right", padx=(8, 0))

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
    App().run()
