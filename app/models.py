from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SpopData(db.Model):
    __tablename__ = 'spop_data'

    id = db.Column(db.Integer, primary_key=True)
    region_type = db.Column(db.String(50), nullable=True) # e.g. tangsel or kab_tangerang
    nop = db.Column(db.String(30), unique=True, nullable=False)
    nop_bersama = db.Column(db.String(30), nullable=True)
    jenis_transaksi = db.Column(db.String(50), nullable=True)
    
    nop_asal = db.Column(db.String(30), nullable=True)
    no_sppt_lama = db.Column(db.String(30), nullable=True)
    
    # Subjek Pajak / Wajib Pajak (WP)
    status_wp = db.Column(db.String(50), nullable=True)
    pekerjaan_wp = db.Column(db.String(50), nullable=True)
    nama_wp = db.Column(db.String(100), nullable=False)
    npwp_wp = db.Column(db.String(30), nullable=True)
    no_ktp_wp = db.Column(db.String(30), nullable=True)
    email_wp = db.Column(db.String(100), nullable=True)
    
    jalan_wp = db.Column(db.String(150), nullable=True)
    blok_kav_no_wp = db.Column(db.String(50), nullable=True)
    rt_rw_wp = db.Column(db.String(20), nullable=True)
    kelurahan_wp = db.Column(db.String(100), nullable=True)
    kabupaten_wp = db.Column(db.String(100), nullable=True)
    kodepos_wp = db.Column(db.String(10), nullable=True)
    
    # Letak Objek Pajak (OP)
    jalan_op = db.Column(db.String(150), nullable=True)
    blok_kav_no_op = db.Column(db.String(50), nullable=True)
    rt_rw_op = db.Column(db.String(20), nullable=True)
    kelurahan_op = db.Column(db.String(100), nullable=True)
    kabupaten_op = db.Column(db.String(100), nullable=True)
    
    # Data Bumi
    luas_bumi = db.Column(db.Float, nullable=True)
    kelas_zona_bumi = db.Column(db.String(50), nullable=True)
    jenis_tanah = db.Column(db.String(50), nullable=True)
    
    # Data Bangunan
    jumlah_bangunan = db.Column(db.Integer, default=0)
    luas_bangunan = db.Column(db.Float, default=0.0)
    
    # Koordinat
    longitude = db.Column(db.String(50), nullable=True)
    latitude = db.Column(db.String(50), nullable=True)
    
    # === DATA LSPOP (LAMPIRAN BANGUNAN) ===
    jenis_penggunaan_bangunan = db.Column(db.String(50), nullable=True)
    jumlah_lantai = db.Column(db.Integer, nullable=True)
    tahun_dibangun = db.Column(db.Integer, nullable=True)
    tahun_direnovasi = db.Column(db.Integer, nullable=True)
    daya_listrik = db.Column(db.Integer, nullable=True)
    
    kondisi_pada_umumnya = db.Column(db.String(50), nullable=True)
    konstruksi = db.Column(db.String(50), nullable=True)
    atap = db.Column(db.String(50), nullable=True)
    dinding = db.Column(db.String(50), nullable=True)
    lantai = db.Column(db.String(50), nullable=True)
    langit_langit = db.Column(db.String(50), nullable=True)
    
    # Fasilitas
    jumlah_ac_split = db.Column(db.Integer, nullable=True)
    jumlah_ac_window = db.Column(db.Integer, nullable=True)
    ac_sentral = db.Column(db.String(20), nullable=True)
    luas_kolam_renang = db.Column(db.Float, nullable=True)
    kolam_renang_tipe = db.Column(db.String(50), nullable=True)
    
    luas_perkerasan_halaman_ringan = db.Column(db.Float, nullable=True)
    luas_perkerasan_halaman_sedang = db.Column(db.Float, nullable=True)
    luas_perkerasan_halaman_berat = db.Column(db.Float, nullable=True)
    luas_perkerasan_halaman_dgn_penutup = db.Column(db.Float, nullable=True)
    
    jumlah_lift_penumpang = db.Column(db.Integer, nullable=True)
    jumlah_lift_kapsul = db.Column(db.Integer, nullable=True)
    jumlah_lift_barang = db.Column(db.Integer, nullable=True)
    
    jumlah_tangga_berjalan_kurang = db.Column(db.Integer, nullable=True)
    jumlah_tangga_berjalan_lebih = db.Column(db.Integer, nullable=True)
    
    panjang_pagar = db.Column(db.Float, nullable=True)
    bahan_pagar = db.Column(db.String(50), nullable=True)
    
    pemadam_hydrant = db.Column(db.String(20), nullable=True)
    pemadam_sprinkler = db.Column(db.String(20), nullable=True)
    pemadam_fire_alarm = db.Column(db.String(20), nullable=True)
    
    jumlah_saluran_pes_pabx = db.Column(db.Integer, nullable=True)
    kedalaman_sumur_artesis = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'region_type': self.region_type,
            'nop': self.nop,
            'nop_bersama': self.nop_bersama,
            'jenis_transaksi': self.jenis_transaksi,
            'nop_asal': self.nop_asal,
            'no_sppt_lama': self.no_sppt_lama,
            'status_wp': self.status_wp,
            'pekerjaan_wp': self.pekerjaan_wp,
            'nama_wp': self.nama_wp,
            'npwp_wp': self.npwp_wp,
            'no_ktp_wp': self.no_ktp_wp,
            'email_wp': self.email_wp,
            'jalan_wp': self.jalan_wp,
            'blok_kav_no_wp': self.blok_kav_no_wp,
            'rt_rw_wp': self.rt_rw_wp,
            'kelurahan_wp': self.kelurahan_wp,
            'kabupaten_wp': self.kabupaten_wp,
            'kodepos_wp': self.kodepos_wp,
            'jalan_op': self.jalan_op,
            'blok_kav_no_op': self.blok_kav_no_op,
            'rt_rw_op': self.rt_rw_op,
            'kelurahan_op': self.kelurahan_op,
            'kabupaten_op': self.kabupaten_op,
            'luas_bumi': self.luas_bumi,
            'kelas_zona_bumi': self.kelas_zona_bumi,
            'jenis_tanah': self.jenis_tanah,
            'jumlah_bangunan': self.jumlah_bangunan,
            'luas_bangunan': self.luas_bangunan,
            'longitude': self.longitude,
            'latitude': self.latitude,
            
            # LSPOP
            'jenis_penggunaan_bangunan': self.jenis_penggunaan_bangunan,
            'jumlah_lantai': self.jumlah_lantai,
            'tahun_dibangun': self.tahun_dibangun,
            'tahun_direnovasi': self.tahun_direnovasi,
            'daya_listrik': self.daya_listrik,
            'kondisi_pada_umumnya': self.kondisi_pada_umumnya,
            'konstruksi': self.konstruksi,
            'atap': self.atap,
            'dinding': self.dinding,
            'lantai': self.lantai,
            'langit_langit': self.langit_langit,
            'jumlah_ac_split': self.jumlah_ac_split,
            'jumlah_ac_window': self.jumlah_ac_window,
            'ac_sentral': self.ac_sentral,
            'luas_kolam_renang': self.luas_kolam_renang,
            'kolam_renang_tipe': self.kolam_renang_tipe,
            'luas_perkerasan_halaman_ringan': self.luas_perkerasan_halaman_ringan,
            'luas_perkerasan_halaman_sedang': self.luas_perkerasan_halaman_sedang,
            'luas_perkerasan_halaman_berat': self.luas_perkerasan_halaman_berat,
            'luas_perkerasan_halaman_dgn_penutup': self.luas_perkerasan_halaman_dgn_penutup,
            'jumlah_lift_penumpang': self.jumlah_lift_penumpang,
            'jumlah_lift_kapsul': self.jumlah_lift_kapsul,
            'jumlah_lift_barang': self.jumlah_lift_barang,
            'jumlah_tangga_berjalan_kurang': self.jumlah_tangga_berjalan_kurang,
            'jumlah_tangga_berjalan_lebih': self.jumlah_tangga_berjalan_lebih,
            'panjang_pagar': self.panjang_pagar,
            'bahan_pagar': self.bahan_pagar,
            'pemadam_hydrant': self.pemadam_hydrant,
            'pemadam_sprinkler': self.pemadam_sprinkler,
            'pemadam_fire_alarm': self.pemadam_fire_alarm,
            'jumlah_saluran_pes_pabx': self.jumlah_saluran_pes_pabx,
            'kedalaman_sumur_artesis': self.kedalaman_sumur_artesis,
            
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
