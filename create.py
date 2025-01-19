from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from bitcoinlib.keys import HDKey
from bitcoinlib.transactions import Transaction
import json
import requests
from datetime import datetime
import file_manager

def create_and_sign_bitcoin_transaction(mnemonic, sender_addresses, recipient_address, amount, fee):
    inputs = []
    input_value = 0
    for address in sender_addresses:
        url = f'https://blockstream.info/api/address/{address}/utxo'
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"Error fetching UTXOs for {address}: {response.status_code} - {response.text}")
            utxos = response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
        except json.JSONDecodeError:
            raise Exception("Failed to decode JSON response from API.")
        
        for utxo in utxos:
            inputs.append({
                'txid': utxo['txid'],
                'vout': utxo['vout'],
                'value': utxo['value'],
                'address': address
            })
            input_value += utxo['value']
            if input_value >= amount + fee:
                break
        if input_value >= amount + fee:
            break
    
    if input_value < amount + fee:
        raise Exception("Insufficient balance.")

    outputs = [{'address': recipient_address, 'value': amount}]
    
    change = input_value - (amount + fee)
    if change > 0:
        outputs.append({'address': sender_addresses[0], 'value': change})
    
    tx_data = {'inputs': inputs, 'outputs': outputs}
    with open('unsigned_transaction.json', 'w') as f:
        json.dump(tx_data, f, indent=4)
    print("Unsigned transaction saved to unsigned_transaction.json")

    seed = Bip39SeedGenerator(mnemonic).Generate()
    bip44_ctx = Bip44.FromSeed(seed, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    
    tx = Transaction()
    for utxo in inputs:
        tx.add_input(utxo['txid'], utxo['vout'])
    for output in outputs:
        tx.add_output(output['value'], output['address'])
    
    for i, utxo in enumerate(inputs):
        address_index = sender_addresses.index(utxo['address'])
        priv_key_hex = bip44_ctx.AddressIndex(address_index).PrivateKey().Raw().ToHex()
        key = HDKey(priv_key_hex)
        tx.sign(key, i)
    
    signed_tx_hex = tx.raw_hex()
    signed_tx_data = {
        'inputs': inputs,
        'outputs': outputs,
        'signed_transaction_hex': signed_tx_hex
    }
    
    with open('signed_transaction.json', 'w') as f:
        json.dump(signed_tx_data, f, indent=4)
    
    print("Signed transaction saved to signed_transaction.json")
    return signed_tx_hex

def main():
    mnemonic_phrase = input("Enter your mnemonic phrase: ")
    num_senders = int(input("Enter number of sender addresses: "))
    sender_addresses = [input(f"Enter sender address {i + 1} (bc1... format): ") for i in range(num_senders)]
    recipient = input("Enter recipient address (bc1... format): ")
    amount_to_send = int(input("Enter amount to send (in satoshi): "))
    fee_amount = int(input("Enter fee amount (in satoshi): "))
    
    scheduled_date_str = input("Enter scheduled date and time (YYYY-MM-DD HH:MM:SS): ")
    try:
        scheduled_date = datetime.strptime(scheduled_date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD HH:MM:SS")
        return
    
    file_manager.initialize_tx_dir()
    
    signed_tx = create_and_sign_bitcoin_transaction(mnemonic_phrase, sender_addresses, recipient, amount_to_send, fee_amount)
    print("Signed transaction HEX:", signed_tx)
    
    saved_tx_path = file_manager.save_transaction(signed_tx, scheduled_date_str)
    print(f"Signed transaction saved to {saved_tx_path}")

if __name__ == "__main__":
    main()
