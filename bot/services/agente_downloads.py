import os
import shutil
import time
import sys
from datetime import datetime, timedelta

# Caminho da pasta Downloads (ajustado automaticamente para o usuário atual)
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

# Destinos para cada tipo de arquivo
DESTINOS = {
    ".pdf": os.path.join(os.path.expanduser("~"), "Documents", "PDFs"),
    ".docx": os.path.join(os.path.expanduser("~"), "Documents", "Documentos"),
    ".doc": os.path.join(os.path.expanduser("~"), "Documents", "Documentos"),
    ".txt": os.path.join(os.path.expanduser("~"), "Documents", "Documentos"),
    ".xlsx": os.path.join(os.path.expanduser("~"), "Documents", "Planilhas"),
    ".csv": os.path.join(os.path.expanduser("~"), "Documents", "Planilhas"),
    ".pptx": os.path.join(os.path.expanduser("~"), "Documents", "Apresentacoes"),
    ".jpg": os.path.join(os.path.expanduser("~"), "Pictures"),
    ".jpeg": os.path.join(os.path.expanduser("~"), "Pictures"),
    ".png": os.path.join(os.path.expanduser("~"), "Pictures"),
    ".gif": os.path.join(os.path.expanduser("~"), "Pictures"),
    ".svg": os.path.join(os.path.expanduser("~"), "Pictures"),
    ".webp": os.path.join(os.path.expanduser("~"), "Pictures"),
    ".mp3": os.path.join(os.path.expanduser("~"), "Music"),
    ".wav": os.path.join(os.path.expanduser("~"), "Music"),
    ".flac": os.path.join(os.path.expanduser("~"), "Music"),
    ".mp4": os.path.join(os.path.expanduser("~"), "Videos"),
    ".mkv": os.path.join(os.path.expanduser("~"), "Videos"),
    ".avi": os.path.join(os.path.expanduser("~"), "Videos"),
    ".mov": os.path.join(os.path.expanduser("~"), "Videos"),
    ".exe": os.path.join(os.path.expanduser("~"), "Downloads", "Programas"),
    ".msi": os.path.join(os.path.expanduser("~"), "Downloads", "Programas"),
    ".zip": os.path.join(os.path.expanduser("~"), "Downloads", "Compactados"),
    ".rar": os.path.join(os.path.expanduser("~"), "Downloads", "Compactados"),
    ".7z": os.path.join(os.path.expanduser("~"), "Downloads", "Compactados"),
    ".torrent": os.path.join(os.path.expanduser("~"), "Downloads", "Torrents"),
    ".apk": os.path.join(os.path.expanduser("~"), "Downloads", "Programas"),
    ".iso": os.path.join(os.path.expanduser("~"), "Downloads", "Imagens_Disk"),
    ".dwg": os.path.join(os.path.expanduser("~"), "Documents", "DWG"),
    ".skp": os.path.join(os.path.expanduser("~"), "Documents", "SketchUp_Archicad"),
    ".skb": os.path.join(os.path.expanduser("~"), "Documents", "SketchUp_Archicad"),
    ".rbz": os.path.join(os.path.expanduser("~"), "Documents", "SketchUp_Archicad"),
    ".gsm": os.path.join(os.path.expanduser("~"), "Documents", "SketchUp_Archicad"),
    ".gsml": os.path.join(os.path.expanduser("~"), "Documents", "SketchUp_Archicad"),
    ".lcf": os.path.join(os.path.expanduser("~"), "Documents", "SketchUp_Archicad"),
    ".html": os.path.join(os.path.expanduser("~"), "Documents", "Codigo"),
    ".css": os.path.join(os.path.expanduser("~"), "Documents", "Codigo"),
    ".js": os.path.join(os.path.expanduser("~"), "Documents", "Codigo"),
    ".py": os.path.join(os.path.expanduser("~"), "Documents", "Codigo"),
    ".json": os.path.join(os.path.expanduser("~"), "Documents", "Codigo"),
    ".sqlite": os.path.join(os.path.expanduser("~"), "Documents", "Codigo"),
    ".pst": os.path.join(os.path.expanduser("~"), "Documents", "Emails"),
}
OUTROS = os.path.join(os.path.expanduser("~"), "Downloads", "Outros")


def extensao_conhecida(ext):
    return ext in DESTINOS


def mover_arquivo(caminho, arquivo, ext):
    destino = DESTINOS.get(ext, OUTROS)
    os.makedirs(destino, exist_ok=True)
    destino_final = os.path.join(destino, arquivo)
    # Se já existir, renomeia com sufixo (1), (2)...
    contador = 1
    while os.path.exists(destino_final):
        nome, e = os.path.splitext(arquivo)
        destino_final = os.path.join(destino, f"{nome} ({contador}){e}")
        contador += 1
    try:
        shutil.move(caminho, destino_final)
        print(f"  Movido: {arquivo} -> {destino}")
    except (PermissionError, shutil.Error) as erro:
        print(f"  SKIP {arquivo}: {erro}")


# Função para organizar arquivos e pastas
def organizar_downloads():
    print(f"\nOrganizando {DOWNLOADS}...")
    for item in os.listdir(DOWNLOADS):
        caminho = os.path.join(DOWNLOADS, item)
        if caminho.endswith(("Programas", "Compactados", "Torrents", "Imagens_Disk", "Outros")):
            continue
        if os.path.isfile(caminho):
            ext = os.path.splitext(item)[1].lower()
            mover_arquivo(caminho, item, ext)
        elif os.path.isdir(caminho):
            # Pastas vão para "Pastas"
            destino = os.path.join(DOWNLOADS, "Pastas")
            os.makedirs(destino, exist_ok=True)
            destino_final = os.path.join(destino, item)
            try:
                shutil.move(caminho, destino_final)
                print(f"  Movido pasta: {item} -> {destino}")
            except (PermissionError, shutil.Error) as erro:
                print(f"  SKIP pasta {item}: {erro}")


# Função para remover duplicados (mesmo nome e mesmo tamanho)
def remover_duplicados(pasta):
    print(f"\nBuscando duplicados em {pasta}...")
    vistos = {}
    for arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, arquivo)
        if os.path.isfile(caminho):
            tamanho = os.path.getsize(caminho)
            chave = (arquivo.lower(), tamanho)
            if chave in vistos:
                try:
                    os.remove(caminho)
                    print(f"  Removido duplicado: {arquivo}")
                except (PermissionError, OSError) as erro:
                    print(f"  SKIP {arquivo}: {erro}")
            else:
                vistos[chave] = caminho


# Função para limpar arquivos antigos (apenas temporários)
def limpar_temporarios(pasta, dias=7):
    print(f"\nLimpando temporários com mais de {dias} dias em {pasta}...")
    limite = datetime.now() - timedelta(days=dias)
    temporarios = (".tmp", ".temp", ".crdownload", ".part", ".download")
    for arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, arquivo)
        if os.path.isfile(caminho) and os.path.splitext(arquivo)[1].lower() in temporarios:
            modificado = datetime.fromtimestamp(os.path.getmtime(caminho))
            if modificado < limite:
                try:
                    os.remove(caminho)
                    print(f"  Removido temporário: {arquivo}")
                except (PermissionError, OSError) as erro:
                    print(f"  SKIP {arquivo}: {erro}")


# Loop principal do agente
def agente_downloads(intervalo=300):
    print(f"Agente de Downloads ativo. Intervalo: {intervalo}s. Ctrl+C para parar.")
    while True:
        try:
            rodar_passagem()
            print("Downloads organizada!")
        except Exception as erro:
            print(f"Erro: {erro}")
        time.sleep(intervalo)


def rodar_passagem():
    organizar_downloads()
    remover_duplicados(DOWNLOADS)
    limpar_temporarios(DOWNLOADS, dias=7)


# Log em arquivo para execução em segundo plano e resposta ao bot
def rodar_uma_vez():
    log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Logs_Agente")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"agente_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    import sys as _sys
    import io

    class DualWriter:
        def __init__(self, out1, out2):
            self.out1 = out1
            self.out2 = out2
        def write(self, data):
            self.out1.write(data)
            self.out2.write(data)
        def flush(self):
            self.out1.flush()
            self.out2.flush()

    if hasattr(_sys.stdout, "reconfigure"):
        try:
            _sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    with open(log_path, "w", encoding="utf-8") as log:
        escritor = io.TextIOWrapper(log.buffer, encoding="utf-8", line_buffering=True)
        original = _sys.stdout
        _sys.stdout = DualWriter(original, escritor)
        try:
            rodar_passagem()
        except Exception as erro:
            print(f"Erro: {erro}")
        finally:
            _sys.stdout = original
        escritor.flush()
    print(f"\nLog salvo em: {log_path}")


def relatorio():
    print(f"Downloads: {DOWNLOADS}")
    total_arquivos = 0
    total_tamanho = 0
    for raiz, pastas, arquivos in os.walk(DOWNLOADS):
        for a in arquivos:
            caminho = os.path.join(raiz, a)
            try:
                total_tamanho += os.path.getsize(caminho)
                total_arquivos += 1
            except OSError:
                pass
    print(f"Arquivos: {total_arquivos}")
    print(f"Tamanho total: {total_tamanho / 1024 / 1024:.2f} MB")
    print(f"\nPastas em {DOWNLOADS}:")
    for item in sorted(os.listdir(DOWNLOADS)):
        caminho = os.path.join(DOWNLOADS, item)
        if os.path.isdir(caminho):
            qtd = sum(len(f) for _, _, f in os.walk(caminho))
            print(f"  {item} ({qtd} arquivos)")
    print(f"\nLivre no disco C:")
    try:
        if hasattr(ctypes, "windll"):
            free = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p("C:\\"), None, None, ctypes.pointer(free)
            )
            free_gb = free.value / 1024 / 1024 / 1024
        else:
            free_gb = shutil.disk_usage("C:\\").free / 1024 / 1024 / 1024
        print(f"  {free_gb:.2f} GB")
    except Exception:
        free_gb = shutil.disk_usage("C:\\").free / 1024 / 1024 / 1024
        print(f"  {free_gb:.2f} GB")


def executar_comando_local(command: str, args: list) -> str:
    """Executa o comando requisitado e retorna a resposta formatada em texto."""
    import io, contextlib
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if command == "organizar":
            rodar_passagem()
        elif command == "relatorio":
            relatorio()
        elif command == "duplicados":
            remover_duplicados(DOWNLOADS)
        elif command == "limpar":
            limpar_temporarios(DOWNLOADS, dias=7)
        elif command == "lixeira":
            import subprocess
            res = subprocess.run(["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"], capture_output=True, text=True)
            if res.returncode == 0:
                print("🗑️ Lixeira do Windows esvaziada com sucesso no PC local!")
            else:
                print(f"Erro ao esvaziar lixeira: {res.stderr}")
        elif command == "logs":
            log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Logs_Agente")
            logs = sorted([os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.startswith("agente_")]) if os.path.exists(log_dir) else []
            if logs:
                with open(logs[-1], "r", encoding="utf-8", errors="ignore") as f:
                    print("\n".join(f.readlines()[-25:]))
            else:
                print("Nenhum log encontrado.")
        else:
            rodar_passagem()
    return buffer.getvalue().strip() or "Comando executado com sucesso."


def conectar_bot_nuvem(server_url: str = "http://nsq5vpnj66edqa92qtr5peel.72.61.130.70.sslip.io"):
    """Loop de escuta remota do agente no PC para atender comandos enviados via Telegram ao bot na nuvem."""
    import json
    import urllib.request

    poll_url = f"{server_url.rstrip('/')}/api/agent/poll"
    result_url = f"{server_url.rstrip('/')}/api/agent/result"
    print(f"📡 Agente local conectado à nuvem: {server_url}")
    print("Aguardando comandos enviados pelo Telegram (Ctrl+C para encerrar)...")

    while True:
        try:
            req = urllib.request.Request(poll_url, headers={"User-Agent": "AlfredoLocalAgent/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                task = data.get("task")
                if task:
                    task_id = task.get("id")
                    command = task.get("command")
                    args = task.get("args", [])
                    print(f"⚡ Comando recebido da nuvem: {command} (ID: {task_id})")
                    saida = executar_comando_local(command, args)

                    res_payload = json.dumps({"id": task_id, "output": saida}).encode("utf-8")
                    post_req = urllib.request.Request(
                        result_url,
                        data=res_payload,
                        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "AlfredoLocalAgent/1.0"},
                        method="POST",
                    )
                    with urllib.request.urlopen(post_req, timeout=10) as p_resp:
                        print(f"✅ Resultado enviado para a nuvem!")
        except Exception:
            pass
        time.sleep(3)


if __name__ == "__main__":
    args = [a.lower() for a in sys.argv[1:]]
    if "--remote" in args or "-r" in args:
        url = args[args.index("--remote") + 1] if "--remote" in args and len(args) > args.index("--remote") + 1 else "http://nsq5vpnj66edqa92qtr5peel.72.61.130.70.sslip.io"
        conectar_bot_nuvem(url)
    elif "once" in args or "1x" in args:
        rodar_uma_vez()
    elif "--relatorio" in args:
        relatorio()
    elif "--duplicados" in args:
        remover_duplicados(DOWNLOADS)
    elif "--limpar" in args:
        limpar_temporarios(DOWNLOADS, dias=7)
    else:
        intervalo = 300
        if len(args) > 0:
            try:
                intervalo = int(args[0])
            except ValueError:
                pass
        agente_downloads(intervalo)
