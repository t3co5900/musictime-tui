"""Configuración faltante o de ejemplo: el aviso tiene que ser claro."""
import json

import pytest

from musictime import cli
from musictime import spotify as sp


@pytest.fixture
def config(tmp_path, monkeypatch):
    ruta = tmp_path / "config.json"
    monkeypatch.setattr(sp, "CONFIG", str(ruta))
    return ruta


def test_sin_archivo_avisa_que_falta_el_client_id(config):
    with pytest.raises(sp.SpotifyError, match="Falta tu Client ID"):
        sp.client_id()


def test_el_texto_de_ejemplo_no_cuenta_como_client_id(config):
    config.write_text(json.dumps({"client_id": sp.PLACEHOLDER}))
    with pytest.raises(sp.SpotifyError, match="Falta tu Client ID"):
        sp.client_id()


def test_client_id_vacio_o_con_espacios(config):
    config.write_text(json.dumps({"client_id": "   "}))
    with pytest.raises(sp.SpotifyError):
        sp.client_id()


def test_json_roto_da_un_mensaje_claro(config):
    config.write_text("{client_id: abc")
    with pytest.raises(sp.SpotifyError, match="JSON válido"):
        sp.client_id()


def test_client_id_valido_se_devuelve_sin_espacios(config):
    config.write_text(json.dumps({"client_id": "  abc123  "}))
    assert sp.client_id() == "abc123"


def test_musictime_sin_configurar_avisa_de_la_configuracion_y_no_del_login(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musictime"])
    monkeypatch.setattr(sp, "is_logged_in", lambda: False)
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert "Falta tu Client ID" in str(e.value)
    assert "iniciá sesión" not in str(e.value)


def test_musictime_configurado_pero_sin_login_pide_login(config, monkeypatch):
    config.write_text(json.dumps({"client_id": "abc"}))
    monkeypatch.setattr("sys.argv", ["musictime"])
    monkeypatch.setattr(sp, "is_logged_in", lambda: False)
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert "musictime login" in str(e.value)
