from pathlib import Path
import subprocess

def test_shell_scripts_have_valid_bash_syntax():
    root=Path(__file__).resolve().parents[3]
    for path in sorted((root/"infrastructure/deployment/scripts").glob("*.sh")):
        completed=subprocess.run(["bash","-n",str(path)],capture_output=True,text=True)
        assert completed.returncode == 0, completed.stderr

def test_build_release_creates_commit_keyed_archive(tmp_path):
    root=Path(__file__).resolve().parents[3]
    completed=subprocess.run(
        ["bash",str(root/"infrastructure/deployment/scripts/build-release.sh"),str(root),str(tmp_path)],
        cwd=root,capture_output=True,text=True,env={"PATH": __import__("os").environ["PATH"], "COMMIT_SHA": "abc1234"},
    )
    assert completed.returncode == 0, completed.stderr
    archive=Path(completed.stdout.strip())
    assert archive.is_file()
    assert archive.with_suffix(archive.suffix+".sha256").is_file()
