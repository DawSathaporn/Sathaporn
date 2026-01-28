import os
import re
import time
import requests
from github import Github, GithubException

# --- KONFIGURASI ---
GITHUB_TOKEN = os.getenv('GITHUB_PAT')  # Ambil dari environment variable
SOURCE_URL   = "https://raw.githubusercontent.com/SomchaiTeerapat/-/refs/heads/main/%E0%B8%AA%E0%B8%B3%E0%B8%AB%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%AA%E0%B9%88%E0%B8%A7%E0%B8%99%E0%B8%95%E0%B8%B1%E0%B8%A7%E0%B9%80%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%99%E0%B8%B1%E0%B9%89%E0%B8%99%20%E0%B9%82%E0%B8%9B%E0%B8%A3%E0%B8%94%E0%B8%AD%E0%B8%A2%E0%B9%88%E0%B8%B2%E0%B8%99%E0%B8%B3%E0%B8%AA%E0%B8%B4%E0%B9%88%E0%B8%87%E0%B9%83%E0%B8%94%E0%B8%81%E0%B9%87%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%97%E0%B8%B5%E0%B9%88%E0%B8%89%E0%B8%B1%E0%B8%99%E0%B9%82%E0%B8%9E%E0%B8%AA%E0%B8%95%E0%B9%8C%E0%B9%84%E0%B8%9B%E0%B9%83%E0%B8%8A%E0%B9%89?token=GHSAT0AAAAAADUIYMCWUQSARPQHJBUBWTTW2L2SP3A"
DEST_REPO    = "DawSathaporn/Sathaporn"   # Format: "username/repository"
GIT_BRANCH   = "main"
COMMIT_MSG   = "Auto update: Sync playlist from source + footer update"
SLEEP_BETWEEN_COMMITS_SEC = 0.7         # jeda antar commit

# --- FOOTER TOOLS ---
FOOTER_REGEX = r'#EXTM3U billed-msg="[^"]+"'

def generate_footer(dest_file_path):
    return f'#EXTM3U billed-msg="😎{dest_file_path}| lynk.id/magelife😎"'

def strip_footer(text):
    return re.sub(FOOTER_REGEX, '', text).strip()

def add_footer(text, dest_file_path):
    cleaned = strip_footer(text)
    return f"{cleaned}\n\n{generate_footer(dest_file_path)}\n"

# --- AMBIL KONTEN DARI SOURCE ---
def get_source_content():
    try:
        print(f"Mengambil konten dari: {SOURCE_URL} ...")
        r = requests.get(SOURCE_URL, timeout=30)
        r.raise_for_status()
        print("✅ Konten berhasil diambil.")
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengambil konten sumber: {e}")
        return None

# --- UPDATE FILE SATU PER SATU ---
def update_single_file(g, dest_file_path, base_content_no_footer):
    new_content_with_footer = add_footer(base_content_no_footer, dest_file_path)
    repo = g.get_repo(DEST_REPO)

    print(f"\n🟦 Memproses file: {dest_file_path}")

    try:
        contents = repo.get_contents(dest_file_path, ref=GIT_BRANCH)
        sha = contents.sha
        old_text = contents.decoded_content.decode("utf-8")
        old_no_footer = strip_footer(old_text)

        # Cek apakah konten sama (tanpa footer)
        if old_no_footer.strip() == base_content_no_footer.strip():
            print("➡️  Tidak ada perubahan, skip.")
            return

        # Update file jika ada perubahan
        print("✏️  Ada perubahan, memperbarui file...")
        repo.update_file(
            path=contents.path,
            message=COMMIT_MSG,
            content=new_content_with_footer,
            sha=sha,
            branch=GIT_BRANCH
        )
        print("✅ File berhasil di-update!")

    except GithubException as e:
        if e.status == 404:
            print("🆕 File belum ada, membuat baru...")
            repo.create_file(
                path=dest_file_path,
                message=COMMIT_MSG,
                content=new_content_with_footer,
                branch=GIT_BRANCH
            )
            print("✅ File baru berhasil dibuat.")
        else:
            print(f"❌ Error API GitHub: {e}")
    except Exception as e:
        print(f"❌ Error tak terduga: {e}")

# --- GENERATE FILE NAME OTOMATIS UNTUK NOVEMBER 2025 ---
def generate_november_files():
    month = "JANUARI"
    year = "2027"
    prefix = "ST"
    return [f"{prefix}{day}{month}{year}" for day in range(1, 31)]  # 1 s/d 30

# --- MAIN ---
def main():
    if not GITHUB_TOKEN:
        print("❌ Error: environment variable GITHUB_PAT belum diatur.")
        return

    # Ambil konten dari source
    src = get_source_content()
    if not src:
        return

    base_no_footer = strip_footer(src)
    g = Github(GITHUB_TOKEN)

    # Daftar file target (1-30 November)
    target_files = generate_november_files()
    print(f"\n📁 Daftar file target ({len(target_files)}):")
    print(target_files)

    for idx, dest_file_path in enumerate(target_files, start=1):
        print(f"\n({idx}/{len(target_files)}) Mulai update {dest_file_path}...")
        update_single_file(g, dest_file_path, base_no_footer)
        time.sleep(SLEEP_BETWEEN_COMMITS_SEC)

    print("\n🎯 Semua file selesai diproses!")

if __name__ == "__main__":
    main()
