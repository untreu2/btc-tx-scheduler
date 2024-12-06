import json
from pathlib import Path
from datetime import datetime
from time import sleep
from file_manager import load_transactions, save_transaction, delete_transaction
from broadcaster import broadcast_transaction
from signer import generate_private_key, sign_transaction
from utils import get_current_time

def list_transactions():
    transactions = load_transactions()
    if not transactions:
        print("No transactions found.")
        return
    for tx in transactions:
        print(f"ID: {tx['file'].name}")
        print(f"Scheduled Time: {tx['scheduled_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("Status: pending")
        print("-" * 30)

def create_transaction():
    mnemonic_words = input("Enter your mnemonic: ").strip()
    recipient_address = input("Enter recipient address: ").strip()
    amount = float(input("Enter amount (BTC): ").strip())
    fee_rate = float(input("Enter fee rate (satoshis/byte): ").strip())
    scheduled_time_str = input("Enter scheduled time (YYYY-MM-DD HH:MM:SS): ").strip()

    try:
        key = generate_private_key(mnemonic_words)
    except ValueError as ve:
        print(f"Error: {ve}")
        return

    unspents = key.get_unspents()
    if not unspents:
        print("Error: No unspent transactions available.")
        return

    outputs = [(recipient_address, amount, 'btc')]

    try:
        unsigned_tx_hex = key.create_transaction(
            outputs, fee=0, absolute_fee=True, unspents=unspents, combine=True
        )
        estimated_size = len(unsigned_tx_hex) // 2
        total_fee_satoshis = int(fee_rate * estimated_size)
        signed_tx_hex = sign_transaction(key, outputs, total_fee_satoshis, unspents)
    except ValueError as ve:
        print(f"Error: {ve}")
        return

    tx_filename = save_transaction(signed_tx_hex, scheduled_time_str)
    print(f"Transaction created and saved as: {tx_filename.name}")

def delete_transaction_cli():
    tx_id = input("Enter transaction ID to delete: ").strip()
    tx_file = Path('transactions') / tx_id
    if tx_file.exists():
        delete_transaction(tx_file)
        print("Transaction deleted successfully.")
    else:
        print("Error: Transaction not found.")

def broadcast_transaction_cli():
    tx_id = input("Enter transaction ID to broadcast: ").strip()
    tx_file = Path('transactions') / tx_id
    if tx_file.exists():
        with open(tx_file, 'r') as f:
            tx_data = json.load(f)
            signed_tx_hex = tx_data['signed_tx_hex']
            try:
                broadcast_transaction(signed_tx_hex)
                delete_transaction(tx_file)
                print("Transaction broadcasted successfully.")
            except Exception as e:
                print(f"Error: {e}")
    else:
        print("Error: Transaction not found.")

def check_and_broadcast_transactions():
    transactions = load_transactions()
    now = get_current_time()

    for tx in transactions:
        if tx['scheduled_time'] <= now:
            print(f"Broadcasting transaction ID: {tx['file'].name}")
            try:
                broadcast_transaction(tx['signed_tx_hex'])
                delete_transaction(tx['file'])
                print(f"Transaction {tx['file'].name} broadcasted successfully.")
            except Exception as e:
                print(f"Error broadcasting transaction {tx['file'].name}: {e}")

def main():
    while True:
        print("\nMenu:")
        print("1. List Transactions")
        print("2. Schedule a Transaction")
        print("3. Delete a Transaction")
        print("4. Broadcast a Transaction")
        print("5. Start Auto-Broadcast")
        print("6. Exit")

        choice = input("Choose an option: ").strip()

        if choice == '1':
            list_transactions()
        elif choice == '2':
            create_transaction()
        elif choice == '3':
            delete_transaction_cli()
        elif choice == '4':
            broadcast_transaction_cli()
        elif choice == '5':
            print("Auto-broadcast started. Press Ctrl+C to stop.")
            try:
                while True:
                    check_and_broadcast_transactions()
                    sleep(60)
            except KeyboardInterrupt:
                print("\nAuto-broadcast stopped.")
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
