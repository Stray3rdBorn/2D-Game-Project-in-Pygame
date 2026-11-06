import paths
import server_address


def test_data_folder_uses_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert paths.data_folder() == tmp_path / "DecaDome"


def test_data_folder_falls_back_to_appdata(monkeypatch, tmp_path):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert paths.data_folder() == tmp_path / "DecaDome"


def test_data_folder_falls_back_to_home(monkeypatch):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    assert paths.data_folder().name == "DecaDome"


def test_default_server_address_is_local():
    # the release job replaces this file, the repo copy must stay local
    assert server_address.API_URL.startswith("http://127.0.0.1")


def test_highscore_creates_the_folder(monkeypatch, tmp_path):
    import main
    monkeypatch.setattr(main, "HIGHSCORE_FILE", tmp_path / "new" / "highscore.json")
    main.save_highscore(7)
    assert main.load_highscore() == 7