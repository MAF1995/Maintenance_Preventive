from zipfile import ZipFile

from maintenance_preventive.data.fetch_dataset import ensure_dataset_available


def test_ensure_dataset_available_extracts_required_files_from_local_archive(tmp_path):
    archive_path = tmp_path / "hydraulic.zip"
    output_dir = tmp_path / "raw"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("PS2.txt", "1 2 3\n4 5 6\n")
        archive.writestr("FS1.txt", "7 8\n9 10\n")
        archive.writestr("profile.txt", "100 100 0 130 0\n90 90 1 115 0\n")

    status = ensure_dataset_available(
        archive_path=archive_path,
        output_dir=output_dir,
    )

    assert status["dataset_ready"] is True
    assert status["used_local_archive"] is True
    assert (output_dir / "PS2.txt").exists()
    assert (output_dir / "FS1.txt").exists()
    assert (output_dir / "profile.txt").exists()
