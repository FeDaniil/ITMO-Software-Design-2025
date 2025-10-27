import tempfile
from src.sd_cli.cat import cat


def test_cat(capsys):
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(b"aboba")
        tmp.seek(0)
        cat(tmp.name)
        assert capsys.readouterr().out == "aboba"
