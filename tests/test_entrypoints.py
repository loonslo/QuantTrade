import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_command_line_emits_valid_json():
    process = subprocess.run([
        sys.executable, 'main.py', 'backtest', '--csv', 'examples/sample_ohlcv.csv',
    ], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=45)
    assert process.returncode == 0, process.stderr[-3000:]
    result = json.loads(process.stdout)
    assert result['strategy_name'] == 'ma_cross'
    assert result['performance']['total_trades'] > 0


def test_fresh_database_api_lifecycle(temp_dir):
    code = '''
import ccxt
def forbidden(*args, **kwargs):
    raise AssertionError('No exchange access allowed in this smoke test')
ccxt.Exchange.fetch = forbidden
from api.app import create_app
from fastapi.testclient import TestClient
from data.config.database_config import get_database_config
from sqlalchemy import inspect
with TestClient(create_app()) as client:
    assert client.get('/health').status_code == 200
    assert len(inspect(get_database_config().create_engine()).get_table_names()) > 5
with TestClient(create_app()) as client:
    assert client.get('/health').status_code == 200
print('fresh database and repeat startup passed')
'''
    environment = {**os.environ, 'DB_PATH': str(temp_dir / 'sys-test.db'),
                   'QUANTTRADE_ENABLE_SCHEDULER': '0', 'PYTHONUTF8': '1'}
    process = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=environment,
                             capture_output=True, text=True, encoding='utf-8', timeout=45)
    assert process.returncode == 0, process.stderr[-6000:]
    assert 'repeat startup passed' in process.stdout
