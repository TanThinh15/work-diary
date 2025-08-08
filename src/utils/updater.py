import requests
import logging
import subprocess
import os
import sys
from tkinter import messagebox

class AutoUpdater:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.app_version = self.config_manager.get_app_version()
        self.update_url = self.config_manager.get_update_repo_url()
        self.logger = logging.getLogger(__name__)

    def check_for_updates(self, manual_check=False):
        """
        Checks for application updates from the configured GitHub repository.
        If a new version is available, prompts the user to download it.
        """
        if not self.update_url:
            self.logger.warning("Update repository URL is not configured.")
            if manual_check:
                messagebox.showinfo("Kiểm tra cập nhật", "URL kiểm tra cập nhật chưa được cấu hình.")
            return

        self.logger.info(f"Checking for updates from: {self.update_url}")
        try:
            response = requests.get(self.update_url, timeout=5)
            response.raise_for_status() # Raise an exception for HTTP errors
            latest_release = response.json()

            latest_version_tag = latest_release.get("tag_name", "v0.0.0").lstrip('v') # Remove 'v' prefix if exists
            latest_download_url = None
            
            # Find the .exe asset for Windows
            for asset in latest_release.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    latest_download_url = asset.get("browser_download_url")
                    break

            if not latest_download_url:
                self.logger.warning("No .exe asset found in the latest release.")
                if manual_check:
                    messagebox.showinfo("Kiểm tra cập nhật", "Không tìm thấy tệp cài đặt (.exe) trong bản phát hành mới nhất.")
                return

            if self._version_gt(latest_version_tag, self.app_version):
                self.logger.info(f"New version available: {latest_version_tag}. Current: {self.app_version}")
                if messagebox.askyesno(
                    "Cập nhật ứng dụng",
                    f"Đã có phiên bản mới ({latest_version_tag})! Phiên bản hiện tại của bạn là {self.app_version}.\n\nBạn có muốn tải xuống bản cập nhật ngay bây giờ không?"
                ):
                    self.logger.info(f"User chose to download update. URL: {latest_download_url}")
                    self._download_and_prompt_install(latest_download_url, latest_version_tag)
                else:
                    self.logger.info("User declined update.")
            elif manual_check:
                messagebox.showinfo("Kiểm tra cập nhật", f"Bạn đang sử dụng phiên bản mới nhất ({self.app_version}).")
                self.logger.info("Application is already up-to-date.")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during update check: {e}")
            if manual_check:
                messagebox.showerror("Lỗi mạng", f"Không thể kiểm tra cập nhật. Vui lòng kiểm tra kết nối internet của bạn.\nLỗi: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse update response: {e}")
            if manual_check:
                messagebox.showerror("Lỗi cập nhật", f"Không thể đọc thông tin cập nhật từ máy chủ.\nLỗi: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during update check: {e}", exc_info=True)
            if manual_check:
                messagebox.showerror("Lỗi cập nhật", f"Đã xảy ra lỗi không mong muốn khi kiểm tra cập nhật.\nLỗi: {e}")

    def _version_gt(self, v1, v2):
        """Compares two version strings (e.g., '1.0.1' > '1.0.0')."""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        return normalize(v1) > normalize(v2)

    def _download_and_prompt_install(self, download_url, version_tag):
        """Downloads the new exe and prompts the user to run it."""
        try:
            self.logger.info(f"Attempting to download update from: {download_url}")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            download_dir = os.path.join(os.path.expanduser("~"), "Downloads") # Or a temp dir
            os.makedirs(download_dir, exist_ok=True)
            new_exe_path = os.path.join(download_dir, f"WorkDiary_v{version_tag}.exe")

            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.info(f"Update downloaded to: {new_exe_path}")

            if messagebox.askyesno(
                "Tải xuống hoàn tất",
                f"Bản cập nhật đã được tải xuống thành công tại:\n{new_exe_path}\n\nBạn có muốn khởi chạy trình cài đặt ngay bây giờ không? Ứng dụng hiện tại sẽ đóng lại."
            ):
                self.logger.info(f"User chose to run update installer: {new_exe_path}")
                subprocess.Popen([new_exe_path]) # Run the new installer
                sys.exit(0) # Exit current application
            else:
                self.logger.info("User declined to run update installer immediately.")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Download failed: {e}")
            messagebox.showerror("Lỗi tải xuống", f"Không thể tải xuống bản cập nhật.\nLỗi: {e}")
        except Exception as e:
            self.logger.error(f"Error during download/install prompt: {e}", exc_info=True)
            messagebox.showerror("Lỗi cập nhật", f"Đã xảy ra lỗi khi chuẩn bị cài đặt bản cập nhật.\nLỗi: {e}")