from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

folder = Path(__file__).resolve().parent
archive = folder / "rsa_benchmark_untuk_tim.zip"
sources = sorted(p for p in folder.iterdir() if p.is_file()
                 and p.suffix in {".py", ".js", ".html", ".md", ".bat", ".ps1"})
with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
    for source in sources:
        bundle.write(source, "rsa_benchmark/" + source.name)
with ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    for source in sources:
        assert bundle.read("rsa_benchmark/" + source.name) == source.read_bytes()
print(f"Paket diperbarui: {archive.name} ({len(sources)} berkas sumber)")
