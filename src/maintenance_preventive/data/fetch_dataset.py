from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from maintenance_preventive.config import (
    ARCHIVES_DIR,
    DATASET_ARCHIVE_PATH,
    DATASET_SOURCE_URL,
    FS1_PATH,
    PROFILE_PATH,
    PS2_PATH,
    RAW_DATA_DIR,
)


REQUIRED_DATASET_FILES = ("PS2.txt", "FS1.txt", "profile.txt")


def required_dataset_paths(output_dir: Path = RAW_DATA_DIR) -> dict[str, Path]:
    return {
        "PS2.txt": output_dir / PS2_PATH.name,
        "FS1.txt": output_dir / FS1_PATH.name,
        "profile.txt": output_dir / PROFILE_PATH.name,
    }


def dataset_is_available(output_dir: Path = RAW_DATA_DIR) -> bool:
    return all(path.exists() for path in required_dataset_paths(output_dir).values())


def download_dataset_archive(
    source_url: str = DATASET_SOURCE_URL,
    archive_path: Path = DATASET_ARCHIVE_PATH,
    force: bool = False,
) -> Path:
    if archive_path.exists() and not force:
        return archive_path

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(source_url, timeout=120) as response, archive_path.open("wb") as target:
        shutil.copyfileobj(response, target)
    return archive_path


def extract_required_dataset_files(
    archive_path: Path = DATASET_ARCHIVE_PATH,
    output_dir: Path = RAW_DATA_DIR,
    force: bool = False,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []

    with ZipFile(archive_path) as archive:
        archive_members = {Path(name).name: name for name in archive.namelist()}
        for filename in REQUIRED_DATASET_FILES:
            member = archive_members.get(filename)
            if member is None:
                raise FileNotFoundError(f"Le fichier {filename} est introuvable dans l'archive.")

            target_path = output_dir / filename
            if target_path.exists() and not force:
                extracted.append(target_path)
                continue

            with archive.open(member) as source, target_path.open("wb") as target:
                shutil.copyfileobj(source, target)
            extracted.append(target_path)

    return extracted


def ensure_dataset_available(
    *,
    source_url: str = DATASET_SOURCE_URL,
    archive_path: Path = DATASET_ARCHIVE_PATH,
    output_dir: Path = RAW_DATA_DIR,
    force: bool = False,
) -> dict[str, str | bool]:
    archive_was_downloaded = force or not archive_path.exists()
    files_were_missing = force or not dataset_is_available(output_dir)

    if force or not dataset_is_available(output_dir):
        download_dataset_archive(source_url=source_url, archive_path=archive_path, force=force)
        extract_required_dataset_files(archive_path=archive_path, output_dir=output_dir, force=force)

    return {
        "dataset_ready": dataset_is_available(output_dir),
        "used_local_archive": archive_path.exists() and not archive_was_downloaded,
        "archive_path": str(archive_path),
        "raw_data_dir": str(output_dir),
        "files_were_missing": files_were_missing,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recupere automatiquement PS2.txt, FS1.txt et profile.txt depuis UCI si besoin."
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    status = ensure_dataset_available(force=args.force)
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
