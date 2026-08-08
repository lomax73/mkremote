"""Test di connettività verso un router (ping + porte TCP), per capire
rapidamente se un problema è di rete (pacchetti persi verso quel sito)
o del servizio stesso (porta chiusa/rifiutata dal router)."""

import re
import socket
import subprocess
import time


def ping(ip: str, count: int = 4, timeout_s: int = 2) -> dict:
    try:
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', str(timeout_s), ip],
            capture_output=True, text=True, timeout=count * timeout_s + 5,
        )
    except subprocess.TimeoutExpired:
        return {'ok': False, 'output': 'Timeout eseguendo ping.', 'perdita_percento': None, 'rtt_medio_ms': None}

    output = result.stdout + result.stderr
    perdita = None
    match_perdita = re.search(r'([\d.]+)% packet loss', output)
    if match_perdita:
        perdita = float(match_perdita.group(1))
    rtt_medio = None
    match_rtt = re.search(r'= [\d.]+/([\d.]+)/', output)  # min/avg/max/mdev
    if match_rtt:
        rtt_medio = float(match_rtt.group(1))
    return {'ok': result.returncode == 0, 'output': output.strip(), 'perdita_percento': perdita, 'rtt_medio_ms': rtt_medio}


def test_porta_tcp(ip: str, port: int, timeout_s: float = 3.0) -> dict:
    inizio = time.monotonic()
    try:
        with socket.create_connection((ip, port), timeout=timeout_s):
            tempo_ms = round((time.monotonic() - inizio) * 1000)
            return {'aperta': True, 'tempo_ms': tempo_ms}
    except socket.timeout:
        tempo_ms = round((time.monotonic() - inizio) * 1000)
        return {'aperta': False, 'errore': 'nessuna risposta (probabile perdita di pacchetti)', 'tempo_ms': tempo_ms}
    except OSError as exc:
        tempo_ms = round((time.monotonic() - inizio) * 1000)
        return {'aperta': False, 'errore': str(exc), 'tempo_ms': tempo_ms}


def esegui_diagnostica(ip: str, porta_ssh: int, porta_api: int) -> dict:
    return {
        'ping': ping(ip),
        'ssh': test_porta_tcp(ip, porta_ssh),
        'api': test_porta_tcp(ip, porta_api),
    }
