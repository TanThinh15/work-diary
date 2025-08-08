import requests
import logging
import subprocess
import os
import sys
import json
from tkinter import messagebox

class AutoUpdater:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Lấy phiên bản từ config và đảm bảo nó không có tiền tố 'v'
        self.app_version = self.config_manager.get_app_version().lstrip('v')
        self.update_repo_url = self.config_manager.get_update_repo_url()
        self.logger = logging.getLogger(__name__)

    def _version_gt(self, v1, v2):
        """
        So sánh hai chuỗi phiên bản (ví dụ: '1.0.1' > '1.0.0').
        Hàm này đã được cải tiến để xử lý cả chuỗi phiên bản có tiền tố 'v' hoặc không.
        """
        def normalize(v):
            # Xóa tiền tố 'v' nếu có và chuyển các phần thành số nguyên
            return [int(x) for x in v.lstrip('v').split('.')]
        return normalize(v1) > normalize(v2)

    def _download_and_prompt_install(self, download_url, version_tag):
        """Tải xuống file .exe mới và nhắc người dùng chạy nó."""
        try:
            self.logger.info(f"Attempting to download update from: {download_url}")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            # Dùng tên file từ URL để tránh trùng lặp
            file_name = download_url.split('/')[-1]
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(download_dir, exist_ok=True)
            new_exe_path = os.path.join(download_dir, file_name)

            self.logger.info(f"Saving update to: {new_exe_path}")
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.info(f"Update downloaded to: {new_exe_path}")

            if messagebox.askyesno(
                "Tải xuống hoàn tất",
                f"Bản cập nhật đã được tải xuống thành công tại:\n{new_exe_path}\n\n"
                "Bạn có muốn khởi chạy trình cài đặt ngay bây giờ không? Ứng dụng hiện tại sẽ đóng lại."
            ):
                subprocess.Popen([new_exe_path])
                sys.exit(0)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Download failed: {e}")
            messagebox.showerror(
                "Lỗi tải xuống",
                f"Không thể tải xuống bản cập nhật.\nLỗi: {e}"
            )
        except Exception as e:
            self.logger.error(f"Error during download/install prompt: {e}", exc_info=True)
            messagebox.showerror(
                "Lỗi cập nhật",
                f"Đã xảy ra lỗi khi chuẩn bị cài đặt bản cập nhật.\nLỗi: {e}"
            )

    def check_for_updates(self, manual_check=False):
        """
        Kiểm tra cập nhật ứng dụng từ kho lưu trữ GitHub.
        Nếu có phiên bản mới, nhắc người dùng tải xuống.
        """
        if not self.update_repo_url:
            self.logger.warning("Update repository URL is not configured.")
            if manual_check:
                messagebox.showinfo("Kiểm tra cập nhật", "URL kiểm tra cập nhật chưa được cấu hình.")
            return

        self.logger.info(f"Checking for updates from: {self.update_repo_url}")
        try:
            response = requests.get(self.update_repo_url, timeout=5)

            if response.status_code == 404:
                self.logger.info("No releases found on GitHub.")
                if manual_check:
                    messagebox.showinfo(
                        "Kiểm tra cập nhật",
                        "Chưa có bản phát hành nào trên GitHub. Vui lòng thử lại sau."
                    )
                return
            
            response.raise_for_status() # Ném lỗi cho các mã trạng thái khác 2xx

            try:
                latest_release = response.json()
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse update response: {e}")
                if manual_check:
                    messagebox.showerror(
                        "Lỗi cập nhật",
                        f"Không thể đọc thông tin cập nhật từ máy chủ.\nLỗi: {e}"
                    )
                return

            latest_version_tag = latest_release.get("tag_name", "v0.0.0")
            latest_download_url = None
            
            for asset in latest_release.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    latest_download_url = asset.get("browser_download_url")
                    break

            if not latest_download_url:
                self.logger.warning("No .exe asset found in the latest release.")
                if manual_check:
                    messagebox.showinfo(
                        "Kiểm tra cập nhật",
                        "Không tìm thấy tệp cài đặt (.exe) trong bản phát hành mới nhất."
                    )
                return

            # So sánh phiên bản
            if self._version_gt(latest_version_tag, self.app_version):
                self.logger.info(f"New version available: {latest_version_tag}. Current: {self.app_version}")
                if messagebox.askyesno(
                    "Cập nhật ứng dụng",
                    f"Đã có phiên bản mới ({latest_version_tag})! Phiên bản hiện tại của bạn là {self.app_version}.\n\n"
                    f"Bạn có muốn tải xuống bản cập nhật ngay bây giờ không?"
                ):
                    self._download_and_prompt_install(latest_download_url, latest_version_tag)
            elif manual_check:
                messagebox.showinfo(
                    "Kiểm tra cập nhật",
                    f"Bạn đang sử dụng phiên bản mới nhất ({self.app_version})."
                )

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during update check: {e}")
            if manual_check:
                messagebox.showerror(
                    "Lỗi mạng",
                    f"Không thể kiểm tra cập nhật. Vui lòng kiểm tra kết nối internet của bạn.\nLỗi: {e}"
                )
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during update check: {e}", exc_info=True)
            if manual_check:
                messagebox.showerror(
                    "Lỗi cập nhật",
                    f"Đã xảy ra lỗi không mong muốn khi kiểm tra cập nhật.\nLỗi: {e}"
                )
