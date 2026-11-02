
from pathlib import Path
import shutil
import hashlib

FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Audio": [".mp3", ".wav", ".ogg", ".flac", ".aac"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
}


def get_category(file_path):
    extension = Path(file_path).suffix.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category
    return "Others"


def format_size(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024


def scan_folder(folder_path):
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError("Selected folder does not exist.")

    results = {}
    for path in folder.iterdir():
        if path.is_file():
            category = get_category(path)
            results.setdefault(category, []).append(path.name)
    return results


def get_folder_stats(folder_path):
    folder = Path(folder_path)
    stats = {}
    total_size = 0
    total_files = 0

    for path in folder.iterdir():
        if path.is_file():
            category = get_category(path)
            size = path.stat().st_size
            item = stats.setdefault(
                category, {"count": 0, "size": 0}
            )
            item["count"] += 1
            item["size"] += size
            total_files += 1
            total_size += size

    return {
        "categories": stats,
        "total_files": total_files,
        "total_size": total_size
    }


def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(folder_path):
    folder = Path(folder_path)
    hashes = {}
    duplicates = []

    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        try:
            digest = calculate_hash(path)
            if digest in hashes:
                duplicates.append({
                    "file": str(path),
                    "original": str(hashes[digest]),
                    "size": path.stat().st_size
                })
            else:
                hashes[digest] = path
        except OSError:
            continue

    return duplicates


def get_unique_path(destination):
    destination = Path(destination)
    if not destination.exists():
        return destination

    counter = 1
    while True:
        candidate = destination.with_name(
            f"{destination.stem}_{counter}{destination.suffix}"
        )
        if not candidate.exists():
            return candidate
        counter += 1


def organize_files(folder_path):
    folder = Path(folder_path)
    moved_files = []
    failed_files = []

    for path in list(folder.iterdir()):
        if not path.is_file():
            continue

        try:
            category = get_category(path)
            target_folder = folder / category
            target_folder.mkdir(exist_ok=True)

            destination = get_unique_path(
                target_folder / path.name
            )
            shutil.move(str(path), str(destination))

            moved_files.append({
                "source": str(path),
                "destination": str(destination)
            })
        except Exception as error:
            failed_files.append({
                "file": path.name,
                "error": str(error)
            })

    return moved_files, failed_files


def undo_moves(moved_files):
    restored = []
    failed = []

    for item in reversed(moved_files):
        source = Path(item["source"])
        destination = Path(item["destination"])

        try:
            if not destination.exists():
                raise FileNotFoundError(
                    f"File not found: {destination}"
                )
            if source.exists():
                raise FileExistsError(
                    f"Original location already exists: {source}"
                )

            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))
            restored.append(str(source))

        except Exception as error:
            failed.append({
                "file": destination.name,
                "error": str(error)
            })

    return restored, failed
