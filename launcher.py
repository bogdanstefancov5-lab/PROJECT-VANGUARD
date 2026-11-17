import os
import json
import zipfile
import threading
import subprocess
import requests
import customtkinter as ctk
import minecraft_launcher_lib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
GAME_DIR = os.path.join(BASE_DIR, "game_client")
MODS_DIR = os.path.join(GAME_DIR, "mods")
INSTALL_FLAG = os.path.join(GAME_DIR, "installed.flag")

DEFAULT_CONFIG = {
    "server_name": "PERIMETER // ПЕРИМЕТР",
    "server_ip": "127.0.0.1:25565",
    "minecraft_version": "1.20.1-forge-47.2.0",
    "modpack_zip_url": "https://ВАШ_САЙТ.ru/modpack.zip",
    "ram_gb": 4
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = load_config()
ctk.set_appearance_mode("dark")


class MilitaryLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["server_name"])
        self.geometry("760x440")
        self.resizable(False, False)
        self.configure(fg_color="#121412")

        self.border_frame = ctk.CTkFrame(
            self, fg_color="#181B18", border_width=2, border_color="#3A4236", corner_radius=6
        )
        self.border_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.top_bar = ctk.CTkFrame(self.border_frame, fg_color="#212620", height=45, corner_radius=4)
        self.top_bar.pack(fill="x", padx=10, pady=(10, 0))

        self.title_label = ctk.CTkLabel(
            self.top_bar, text=f"☢ {CONFIG['server_name']}",
            font=("Consolas", 16, "bold"), text_color="#9EB384"
        )
        self.title_label.pack(side="left", padx=15, pady=10)

        # Блок аккаунта сбоку
        self.account_frame = ctk.CTkFrame(
            self.border_frame, fg_color="#212620", border_width=1, border_color="#4B5644", corner_radius=4
        )
        self.account_frame.place(relx=0.97, rely=0.16, anchor="ne")

        ctk.CTkLabel(
            self.account_frame, text="БОЕЦ:", font=("Consolas", 12, "bold"), text_color="#8C9A82"
        ).pack(side="left", padx=(10, 5), pady=8)

        self.nick_entry = ctk.CTkEntry(
            self.account_frame, placeholder_text="Позывной...", width=135, height=28,
            border_width=1, border_color="#4B5644", fg_color="#141714",
            text_color="#E2E8DD", font=("Consolas", 13, "bold")
        )
        self.nick_entry.insert(0, "Soldier_01")
        self.nick_entry.pack(side="left", padx=(0, 10), pady=8)

        # Главная кнопка
        self.play_button = ctk.CTkButton(
            self.border_frame, text="", font=("Consolas", 22, "bold"),
            width=290, height=72, corner_radius=4, border_width=2, command=self.on_button_click
        )
        self.play_button.place(relx=0.5, rely=0.52, anchor="center")

        self.status_label = ctk.CTkLabel(
            self.border_frame, text="СИСТЕМА ГОТОВА", font=("Consolas", 12), text_color="#8C9A82"
        )
        self.status_label.place(relx=0.5, rely=0.68, anchor="center")

        self.progress_bar = ctk.CTkProgressBar(
            self.border_frame, width=360, height=10, corner_radius=2,
            fg_color="#121412", progress_color="#6B8E23"
        )
        self.progress_bar.set(0)
        self.update_button_state()

    def is_installed(self):
        return os.path.exists(INSTALL_FLAG)

    def update_button_state(self):
        if self.is_installed():
            self.play_button.configure(
                state="normal", text="▶ В БОЙ (ИГРАТЬ)", fg_color="#4A6B32",
                hover_color="#3B5727", border_color="#7CA35D", text_color="#FFFFFF"
            )
            self.status_label.configure(text="ПАПКА МОДОВ: /game_client/mods", text_color="#8C9A82")
        else:
            self.play_button.configure(
                state="normal", text="⬇ СКАЧАТЬ СБОРКУ", fg_color="#9E5824",
                hover_color="#7D441A", border_color="#D9823B", text_color="#FFFFFF"
            )
            self.status_label.configure(text="ТРЕБУЕТСЯ ЗАГРУЗКА ВОЕННОГО КЛИЕНТА", text_color="#D9823B")

    def on_button_click(self):
        nickname = self.nick_entry.get().strip()
        if not nickname:
            self.status_label.configure(text="ОШИБКА: ВВЕДИТЕ ПОЗЫВНОЙ!", text_color="#D9453B")
            return

        self.play_button.configure(state="disabled")
        self.progress_bar.place(relx=0.5, rely=0.75, anchor="center")

        if not self.is_installed():
            threading.Thread(target=self.download_modpack, daemon=True).start()
        else:
            threading.Thread(target=self.launch_minecraft, args=(nickname,), daemon=True).start()

    def download_modpack(self):
        zip_path = os.path.join(BASE_DIR, "temp_modpack.zip")
        try:
            self.status_label.configure(text="ЗАГРУЗКА СБОРКИ С СЕРВЕРА...", text_color="#E2E8DD")
            response = requests.get(CONFIG["modpack_zip_url"], stream=True, timeout=15)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.progress_bar.set((downloaded / total_size) * 0.8)
                            self.status_label.configure(
                                text=f"СКАЧАНО: {downloaded // (1024*1024)} / {total_size // (1024*1024)} МБ"
                            )

            self.status_label.configure(text="РАСПАКОВКА МОДОВ...")
            os.makedirs(MODS_DIR, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(GAME_DIR)

            self.progress_bar.set(1.0)
            os.remove(zip_path)
            with open(INSTALL_FLAG, "w") as f:
                f.write("ok")

            self.status_label.configure(text="ГОТОВО! НАЖМИТЕ «В БОЙ»", text_color="#7CA35D")
        except Exception as e:
            self.status_label.configure(text=f"ОШИБКА: {e}", text_color="#D9453B")
        finally:
            self.progress_bar.place_forget()
            self.progress_bar.set(0)
            self.update_button_state()

    def launch_minecraft(self, nickname):
        try:
            self.status_label.configure(text="ЗАПУСК БОЕВОГО КЛИЕНТА...", text_color="#E2E8DD")
            self.progress_bar.set(0.5)
            os.makedirs(MODS_DIR, exist_ok=True)

            ip_parts = CONFIG["server_ip"].split(":")
            ram = CONFIG.get("ram_gb", 4)

            options = {
                "username": nickname,
                "uuid": "00000000-0000-0000-0000-000000000000",
                "token": "0",
                "jvmArguments": [f"-Xmx{ram}G", "-Xms2G"],
                "server": ip_parts[0],
                "port": ip_parts[1] if len(ip_parts) > 1 else "25565"
            }

            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=CONFIG["minecraft_version"],
                minecraft_directory=GAME_DIR,
                options=options
            )
            self.progress_bar.set(1.0)
            self.status_label.configure(text="ИГРА ЗАПУЩЕНА!", text_color="#7CA35D")
            subprocess.Popen(command)
        except Exception as e:
            self.status_label.configure(text=f"ОШИБКА ЗАПУСКА: {e}", text_color="#D9453B")
        finally:
            self.after(3000, self.reset_after_launch)

    def reset_after_launch(self):
        self.progress_bar.place_forget()
        self.progress_bar.set(0)
        self.update_button_state()

if __name__ == "__main__":
    app = MilitaryLauncher()
    app.mainloop()
      
