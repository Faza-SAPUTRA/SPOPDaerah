import os
import io
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from sqlalchemy.exc import IntegrityError
from models import db, SpopData
import pandas as pd

app = Flask(__name__)
app.secret_key = 'super-secret-key-spop'

# Database config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'spop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def digits_only(value):
    return ''.join(ch for ch in str(value or '') if ch.isdigit())

def option_code(value):
    return str(value or '').split('.', 1)[0].strip()

def whole_number(value, width=0):
    if value in (None, ''):
        text = ''
    else:
        try:
            text = str(int(float(value)))
        except (TypeError, ValueError):
            text = digits_only(value)
    return text.zfill(width) if width and text else text

def split_rt_rw(value):
    parts = [part.strip() for part in str(value or '').replace('-', '/').split('/')]
    rt = digits_only(parts[0]) if parts else ''
    rw = digits_only(parts[1]) if len(parts) > 1 else ''
    return rt.zfill(3)[-3:] if rt else '', rw.zfill(2)[-2:] if rw else ''

app.jinja_env.globals.update(
    digits_only=digits_only,
    option_code=option_code,
    whole_number=whole_number,
    split_rt_rw=split_rt_rw
)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form/<region_type>')
def form(region_type):
    if region_type == 'tangsel':
        region_name = 'Kota Tangerang Selatan'
        region_prefix = '3676'
    elif region_type == 'kab_tangerang':
        region_name = 'Kabupaten Tangerang'
        region_prefix = '3719'
    else:
        flash("Wilayah tidak valid!")
        return redirect(url_for('index'))
        
    return render_template('form.html', 
                           region_type=region_type, 
                           region_name=region_name, 
                           region_prefix=region_prefix)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Gabungkan prefix daerah dengan inputan NOP user
        region_type = request.form.get('region_type')
        prefix = '3676' if region_type == 'tangsel' else '3719'
        full_nop = prefix + request.form.get('nop')
        
        data = SpopData(
            region_type=region_type,
            nop=full_nop,
            nop_bersama=request.form.get('nop_bersama'),
            jenis_transaksi=request.form.get('jenis_transaksi'),
            nop_asal=request.form.get('nop_asal'),
            no_sppt_lama=request.form.get('no_sppt_lama'),
            
            status_wp=request.form.get('status_wp'),
            pekerjaan_wp=request.form.get('pekerjaan_wp'),
            nama_wp=request.form.get('nama_wp'),
            npwp_wp=request.form.get('npwp_wp'),
            no_ktp_wp=request.form.get('no_ktp_wp'),
            email_wp=request.form.get('email_wp'),
            
            jalan_wp=request.form.get('jalan_wp'),
            blok_kav_no_wp=request.form.get('blok_kav_no_wp'),
            rt_rw_wp=request.form.get('rt_rw_wp'),
            kelurahan_wp=request.form.get('kelurahan_wp'),
            kabupaten_wp=request.form.get('kabupaten_wp'),
            kodepos_wp=request.form.get('kodepos_wp'),
            jalan_op=request.form.get('jalan_op'),
            blok_kav_no_op=request.form.get('blok_kav_no_op'),
            rt_rw_op=request.form.get('rt_rw_op'),
            kelurahan_op=request.form.get('kelurahan_op'),
            kabupaten_op=request.form.get('kabupaten_op'),
            luas_bumi=float(request.form.get('luas_bumi') or 0),
            kelas_zona_bumi=request.form.get('kelas_zona_bumi'),
            jenis_tanah=request.form.get('jenis_tanah'),
            jumlah_bangunan=int(request.form.get('jumlah_bangunan') or 0),
            luas_bangunan=float(request.form.get('luas_bangunan') or 0),
            longitude=request.form.get('longitude'),
            latitude=request.form.get('latitude'),
            
            # === DATA LSPOP ===
            jenis_penggunaan_bangunan=request.form.get('jenis_penggunaan_bangunan'),
            jumlah_lantai=int(request.form.get('jumlah_lantai') or 0),
            tahun_dibangun=int(request.form.get('tahun_dibangun') or 0),
            tahun_direnovasi=int(request.form.get('tahun_direnovasi') or 0),
            daya_listrik=int(request.form.get('daya_listrik') or 0),
            
            kondisi_pada_umumnya=request.form.get('kondisi_pada_umumnya'),
            konstruksi=request.form.get('konstruksi'),
            atap=request.form.get('atap'),
            dinding=request.form.get('dinding'),
            lantai=request.form.get('lantai'),
            langit_langit=request.form.get('langit_langit'),
            
            jumlah_ac_split=int(request.form.get('jumlah_ac_split') or 0),
            jumlah_ac_window=int(request.form.get('jumlah_ac_window') or 0),
            ac_sentral=request.form.get('ac_sentral'),
            luas_kolam_renang=float(request.form.get('luas_kolam_renang') or 0),
            kolam_renang_tipe=request.form.get('kolam_renang_tipe'),
            
            luas_perkerasan_halaman_ringan=float(request.form.get('luas_perkerasan_halaman_ringan') or 0),
            luas_perkerasan_halaman_sedang=float(request.form.get('luas_perkerasan_halaman_sedang') or 0),
            luas_perkerasan_halaman_berat=float(request.form.get('luas_perkerasan_halaman_berat') or 0),
            luas_perkerasan_halaman_dgn_penutup=float(request.form.get('luas_perkerasan_halaman_dgn_penutup') or 0),
            
            jumlah_lift_penumpang=int(request.form.get('jumlah_lift_penumpang') or 0),
            jumlah_lift_kapsul=int(request.form.get('jumlah_lift_kapsul') or 0),
            jumlah_lift_barang=int(request.form.get('jumlah_lift_barang') or 0),
            
            jumlah_tangga_berjalan_kurang=int(request.form.get('jumlah_tangga_berjalan_kurang') or 0),
            jumlah_tangga_berjalan_lebih=int(request.form.get('jumlah_tangga_berjalan_lebih') or 0),
            
            panjang_pagar=float(request.form.get('panjang_pagar') or 0),
            bahan_pagar=request.form.get('bahan_pagar'),
            
            pemadam_hydrant=request.form.get('pemadam_hydrant'),
            pemadam_sprinkler=request.form.get('pemadam_sprinkler'),
            pemadam_fire_alarm=request.form.get('pemadam_fire_alarm'),
            
            jumlah_saluran_pes_pabx=int(request.form.get('jumlah_saluran_pes_pabx') or 0),
            kedalaman_sumur_artesis=float(request.form.get('kedalaman_sumur_artesis') or 0)
        )
        db.session.add(data)
        db.session.commit()
        return redirect(url_for('success', id=data.id))
    except IntegrityError:
        db.session.rollback()
        flash("Error: Nomor Objek Pajak (NOP) tersebut sudah terdaftar di database! Silakan gunakan NOP yang berbeda.")
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}")
        return redirect(url_for('index'))

@app.route('/success/<int:id>', methods=['GET'])
def success(id):
    data = SpopData.query.get_or_404(id)
    return render_template('success.html', data=data)

@app.route('/cetak/<int:id>', methods=['GET'])
def cetak(id):
    data = SpopData.query.get_or_404(id)
    # Gunakan region_type dari database jika ada, atau fallback deteksi dari NOP
    kop_type = data.region_type
    if not kop_type:
        nop = data.nop or ""
        if nop.startswith("3676"):
            kop_type = "tangsel"
        elif nop.startswith("3719"):
            kop_type = "kab_tangerang"
        else:
            kop_type = "tangsel" # Default fallback
            
    return render_template('pdf_template.html', data=data, kop_type=kop_type)

@app.route('/admin/export', methods=['GET'])
def export_excel():
    all_data = SpopData.query.all()
    data_list = [d.to_dict() for d in all_data]
    
    df = pd.DataFrame(data_list)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data_SPOP')
        
    excel_buffer.seek(0)
    return send_file(
        excel_buffer,
        as_attachment=True,
        download_name='Export_Data_SPOP.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    app.run(debug=False, port=5000, use_reloader=False)
