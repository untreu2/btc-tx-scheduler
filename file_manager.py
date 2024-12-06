import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

TX_DIR = Path('transactions')

def initialize_tx_dir():
    TX_DIR.mkdir(exist_ok=True)

def save_transaction(signed_tx_hex: str, scheduled_time_str: str) -> Path:
    existing_tx_files = list(TX_DIR.glob('tx*.json'))
    tx_number = len(existing_tx_files) + 1
    tx_filename = TX_DIR / f'tx{tx_number}.json'
    with open(tx_filename, 'w') as f:
        json.dump({'signed_tx_hex': signed_tx_hex, 'scheduled_time': scheduled_time_str}, f)
    return tx_filename

def load_transactions() -> List[Dict]:
    tx_files = list(TX_DIR.glob('tx*.json'))
    transactions = []
    for tx_file in tx_files:
        with open(tx_file, 'r') as f:
            data = json.load(f)
            transactions.append({
                'file': tx_file,
                'signed_tx_hex': data['signed_tx_hex'],
                'scheduled_time': datetime.strptime(data['scheduled_time'], "%Y-%m-%d %H:%M:%S")
            })
    return transactions

def delete_transaction(tx_file: Path):
    tx_file.unlink()
