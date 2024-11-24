from flask import Flask, jsonify, request
import hashlib
import json
import os
from time import time
import signal
import sys

class Blockchain:
    def __init__(self):
        self.rantai = []  # Rantai blockchain
        self.transaksi_saat_ini = []  # Daftar transaksi saat ini
        self.muat_dari_file()  # Memuat data dari file jika ada
        if not self.rantai:  # Jika rantai kosong, buat Blok Genesis
            self.buat_blok(hash_sebelumnya='1', bukti=100)

    def buat_blok(self, bukti, hash_sebelumnya=None):
        blok = {
            'indeks': len(self.rantai) + 1,
            'timestamp': time(),
            'transaksi': self.transaksi_saat_ini,
            'bukti': bukti,
            'hash_sebelumnya': hash_sebelumnya or self.hash(self.rantai[-1]),
        }
        self.transaksi_saat_ini = []  # Reset daftar transaksi
        self.rantai.append(blok)
        return blok

    def transaksi_baru(self, name, privy_id, email):
        self.transaksi_saat_ini.append({
            'name': name,
            'privy_id': privy_id,
            'email': email,
        })
        return self.blok_terakhir['indeks'] + 1

    @staticmethod
    def hash(blok):
        string_blok = json.dumps(blok, sort_keys=True).encode()
        return hashlib.sha256(string_blok).hexdigest()

    @property
    def blok_terakhir(self):
        return self.rantai[-1]

    def bukti_kerja(self, bukti_terakhir):
        bukti = 0
        while not self.validasi_bukti(bukti_terakhir, bukti):
            bukti += 1
        return bukti

    @staticmethod
    def validasi_bukti(bukti_terakhir, bukti):
        tebakan = f'{bukti_terakhir}{bukti}'.encode()
        hash_tebakan = hashlib.sha256(tebakan).hexdigest()
        return hash_tebakan[:4] == "0000"

    def simpan_ke_file(self, nama_file="blockchain_data.json"):
        with open(nama_file, 'w') as file:
            json.dump(self.rantai, file, indent=4)
        print("Data blockchain berhasil disimpan ke file.")

    def muat_dari_file(self, nama_file="blockchain_data.json"):
        if os.path.exists(nama_file):
            with open(nama_file, 'r') as file:
                self.rantai = json.load(file)
            print("Data blockchain berhasil dimuat dari file.")
        else:
            print("File tidak ditemukan. Memulai blockchain baru.")

# Inisialisasi blockchain
blockchain = Blockchain()

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Rute API
@app.route('/tambahkan_blok', methods=['GET'])
def tambahkan_blok():
    bukti_terakhir = blockchain.blok_terakhir['bukti']
    bukti = blockchain.bukti_kerja(bukti_terakhir)
    blockchain.buat_blok(bukti)
    respons = {
        'pesan': 'Blok baru berhasil ditambahkan!',
        'blok': blockchain.rantai[-1]
    }
    return jsonify(respons), 200

@app.route('/transaksi/baru', methods=['POST'])
def transaksi_baru():
    data = request.get_json()
    # Validasi data yang dikirim
    diperlukan = ['name', 'privy_id', 'email']
    if not all(k in data for k in diperlukan):
        return 'Data tidak lengkap', 400

    indeks = blockchain.transaksi_baru(data['name'], data['privy_id'], data['email'])
    respons = {'pesan': f'Transaksi akan ditambahkan ke Blok {indeks}'}
    return jsonify(respons), 201

@app.route('/rantai', methods=['GET'])
def tampilkan_rantai():
    respons = {
        'rantai': blockchain.rantai,
        'panjang': len(blockchain.rantai),
    }
    return jsonify(respons), 200

# Fungsi untuk menyimpan data sebelum server berhenti
def simpan_dan_keluar(signal, frame):
    blockchain.simpan_ke_file()
    print("\nServer dihentikan. Data blockchain telah disimpan.")
    sys.exit(0)

# Tangani Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, simpan_dan_keluar)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100)
