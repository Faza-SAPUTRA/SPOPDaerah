import os
import io
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, make_response, session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from models import db, SpopData
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get('SPOP_SECRET_KEY', 'super-secret-key-spop')
ADMIN_USERNAME = os.environ.get('SPOP_ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('SPOP_ADMIN_PASSWORD', 'admin123')

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

def form_float(name):
    try:
        return float(request.form.get(name) or 0)
    except (TypeError, ValueError):
        return 0

def form_int(name):
    try:
        return int(request.form.get(name) or 0)
    except (TypeError, ValueError):
        return 0

def ensure_extra_columns():
    columns = {
        row[1] for row in db.session.execute(text("PRAGMA table_info(spop_data)")).fetchall()
    }
    extra_columns = {
        'tinggi_kolom': 'FLOAT',
        'lebar_bentang': 'FLOAT',
        'daya_dukung_lantai': 'FLOAT',
        'keliling_dinding': 'FLOAT',
        'luas_mezzanine': 'FLOAT',
        'kelas_bangunan_perkantoran': 'VARCHAR(50)',
        'kelas_bangunan_toko': 'VARCHAR(50)',
        'kelas_bangunan_rs': 'VARCHAR(50)',
        'luas_kamar_ac_central_rs': 'FLOAT',
        'luas_ruang_lain_ac_central_rs': 'FLOAT',
        'kelas_bangunan_olahraga': 'VARCHAR(50)',
        'jenis_hotel': 'VARCHAR(50)',
        'jumlah_bintang': 'VARCHAR(50)',
        'jumlah_kamar': 'INTEGER',
        'luas_kamar_ac_central_hotel': 'FLOAT',
        'luas_ruang_lain_ac_central_hotel': 'FLOAT',
        'tipe_bangunan_parkir': 'VARCHAR(50)',
        'kelas_bangunan_apartemen': 'VARCHAR(50)',
        'jumlah_apartemen': 'INTEGER',
        'luas_kamar_ac_central_apartemen': 'FLOAT',
        'luas_ruang_lain_ac_central_apartemen': 'FLOAT',
        'kapasitas_tangki': 'FLOAT',
        'letak_tangki': 'VARCHAR(50)',
        'kelas_bangunan_sekolah': 'VARCHAR(50)'
    }
    for column, column_type in extra_columns.items():
        if column not in columns:
            db.session.execute(text(f"ALTER TABLE spop_data ADD COLUMN {column} {column_type}"))
    db.session.commit()

def pdf_bytes_reportlab(data, kop_type):
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    page_w, page_h = 1190, 1683
    img_pfx = 'tangsel' if kop_type == 'tangsel' else 'kab'
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(page_w, page_h))

    def bg(page_no):
        image_path = os.path.join(app.root_path, 'static', 'img', f'{img_pfx}_{page_no}.png')
        pdf.drawImage(ImageReader(image_path), 0, 0, width=page_w, height=page_h)

    def draw_cells(value, x, y, w, count, h=24, size=15):
        text = (str(value or '')[:count]).ljust(count)
        cell_w = w / count
        pdf.setFont('Courier-Bold', size)
        for idx, char in enumerate(text):
            if char == ' ':
                continue
            cx = x + (idx + 0.5) * cell_w
            baseline = page_h - y - (h / 2) - (size * 0.33)
            pdf.drawCentredString(cx, baseline, char)

    def draw_text(value, x, y, w, count, size=15):
        draw_cells((value or '').upper(), x, y, w, count, 24, size)

    def draw_mark(value, code, x, y):
        if option_code(value) == str(code):
            pdf.setFont('Helvetica-Bold', 20)
            pdf.drawCentredString(x + 14, page_h - y - 19, 'X')

    def draw_date(date_value, x, y):
        draw_cells(date_value.strftime('%d'), x, y, 51, 2)
        draw_cells(date_value.strftime('%m'), x + 77, y, 51, 2)
        draw_cells(date_value.strftime('%y'), x + 153, y, 51, 2)

    def draw_nop(nop, y, first_x=299):
        n = digits_only(nop).ljust(18)
        draw_cells(n[0:2], first_x, y, 53, 2)
        draw_cells(n[2:4], first_x + 74, y, 53, 2)
        draw_cells(n[4:7], first_x + 149, y, 77, 3)
        draw_cells(n[7:10], first_x + 247, y, 81, 3)
        draw_cells(n[10:13], first_x + 349, y, 77, 3)
        draw_cells(n[13:17], first_x + 448, y, 102, 4)
        draw_cells(n[17:18], first_x + 600, y, 28, 1)

    op_rt, op_rw = split_rt_rw(data.rt_rw_op)
    wp_rt, wp_rw = split_rt_rw(data.rt_rw_wp)

    bg(1)
    draw_mark(data.jenis_transaksi, 1, 299, 250)
    draw_mark(data.jenis_transaksi, 2, 599, 250)
    draw_mark(data.jenis_transaksi, 3, 924, 250)
    draw_nop(data.nop, 339)
    draw_nop(data.nop_bersama, 381)
    draw_nop(data.nop_asal, 491)
    draw_cells(digits_only(data.no_sppt_lama), 299, 532, 127, 5)
    draw_text(data.jalan_op, 50, 675, 774, 30)
    draw_text((data.jalan_op or '')[30:], 50, 702, 774, 30)
    draw_text(data.blok_kav_no_op, 846, 675, 303, 12)
    draw_text(data.kelurahan_op, 50, 764, 650, 25)
    draw_cells(op_rw, 846, 764, 56, 2)
    draw_cells(op_rt, 949, 764, 77, 3)
    draw_mark(data.status_wp, 1, 223, 886)
    draw_mark(data.status_wp, 2, 398, 886)
    draw_mark(data.status_wp, 3, 599, 886)
    draw_mark(data.status_wp, 4, 821, 886)
    draw_mark(data.status_wp, 5, 998, 886)
    draw_mark(data.pekerjaan_wp, 1, 223, 927)
    draw_mark(data.pekerjaan_wp, 2, 398, 927)
    draw_mark(data.pekerjaan_wp, 3, 599, 927)
    draw_mark(data.pekerjaan_wp, 4, 821, 927)
    draw_mark(data.pekerjaan_wp, 5, 998, 927)
    draw_text(data.nama_wp, 50, 1010, 799, 31)
    draw_text((data.nama_wp or '')[31:], 50, 1036, 799, 31)
    draw_cells(digits_only(data.npwp_wp), 870, 1010, 305, 15, 23, 14)
    draw_text(data.jalan_wp, 50, 1098, 774, 30)
    draw_text((data.jalan_wp or '')[30:], 50, 1127, 774, 30)
    draw_text(data.blok_kav_no_wp, 846, 1098, 303, 12)
    draw_text(data.kelurahan_wp, 50, 1189, 650, 25)
    draw_cells(wp_rw, 846, 1189, 56, 2)
    draw_cells(wp_rt, 949, 1189, 77, 3)
    draw_text(data.kabupaten_wp, 50, 1251, 650, 25)
    draw_cells(digits_only(data.no_ktp_wp), 50, 1313, 650, 25, 24, 14)
    draw_cells(whole_number(data.luas_bumi, 6), 198, 1437, 277, 11)
    draw_text(data.kelas_zona_bumi, 1097, 1437, 53, 2)
    draw_mark(data.jenis_tanah, 1, 272, 1499)
    draw_mark(data.jenis_tanah, 2, 497, 1499)
    draw_mark(data.jenis_tanah, 3, 722, 1499)
    draw_mark(data.jenis_tanah, 4, 924, 1499)
    pdf.showPage()

    bg(2)
    draw_cells(whole_number(data.jumlah_bangunan, 3), 248, 99, 79, 3)
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawCentredString(320, page_h - 315, (data.nama_wp or '').upper())
    pdf.drawCentredString(645, page_h - 315, data.created_at.strftime('%d-%m-%y'))
    draw_date(data.created_at, 272, 514)
    draw_date(data.created_at, 870, 514)
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(858, page_h - 750, data.longitude or '')
    pdf.drawString(858, page_h - 775, data.latitude or '')
    pdf.showPage()

    if data.jenis_penggunaan_bangunan:
        bg(3)
        draw_mark(data.jenis_transaksi, 1, 299, 180)
        draw_mark(data.jenis_transaksi, 2, 599, 180)
        draw_mark(data.jenis_transaksi, 3, 924, 180)
        draw_nop(data.nop, 276, 198)
        draw_cells(whole_number(data.jumlah_bangunan, 3), 1047, 254, 78, 3)
        draw_cells('001', 1049, 298, 76, 3)
        jpb_positions = {
            1: (248, 415), 2: (522, 415), 3: (846, 415), 4: (248, 445),
            5: (522, 445), 6: (846, 445), 7: (248, 474), 8: (522, 474),
            9: (846, 474), 10: (248, 504), 11: (522, 504), 12: (846, 504),
            13: (248, 534), 14: (522, 534), 15: (846, 534), 16: (248, 564)
        }
        code = int(option_code(data.jenis_penggunaan_bangunan) or 0)
        if code in jpb_positions:
            x, y = jpb_positions[code]
            pdf.setFont('Helvetica-Bold', 20)
            pdf.drawCentredString(x + 14, page_h - y - 19, 'X')
        draw_cells(whole_number(data.luas_bangunan, 6), 248, 624, 277, 11)
        draw_cells(whole_number(data.jumlah_lantai, 3), 821, 624, 81, 3)
        draw_cells(whole_number(data.tahun_dibangun), 248, 657, 104, 4)
        draw_cells(whole_number(data.tahun_direnovasi), 248, 689, 104, 4)
        draw_cells(whole_number(data.daya_listrik), 973, 689, 176, 7)
        draw_mark(data.kondisi_pada_umumnya, 1, 248, 733)
        draw_mark(data.kondisi_pada_umumnya, 2, 423, 733)
        draw_mark(data.kondisi_pada_umumnya, 3, 599, 733)
        draw_mark(data.kondisi_pada_umumnya, 4, 772, 733)
        draw_cells(whole_number(data.jumlah_ac_split), 248, 1035, 54, 2)
        draw_cells(whole_number(data.jumlah_ac_window), 423, 1035, 52, 2)
        draw_cells(whole_number(data.luas_kolam_renang), 248, 1100, 104, 4)
        draw_cells(whole_number(data.jumlah_saluran_pes_pabx), 248, 1561, 104, 4)
        draw_cells(whole_number(data.kedalaman_sumur_artesis), 899, 1561, 102, 4)
        pdf.showPage()

        bg(4)
        c_values = [
            data.tinggi_kolom, data.lebar_bentang, data.daya_dukung_lantai,
            data.keliling_dinding, data.luas_mezzanine
        ]
        if any(value for value in c_values) or code in (3, 8):
            pdf.setFont('Helvetica-Bold', 20)
            pdf.drawCentredString(64, page_h - 108 - 19, 'X')
        draw_cells(whole_number(data.tinggi_kolom), 272, 140, 55, 2)
        draw_cells(whole_number(data.lebar_bentang), 698, 140, 52, 2)
        draw_cells(whole_number(data.daya_dukung_lantai), 272, 171, 105, 4)
        draw_cells(whole_number(data.keliling_dinding), 698, 171, 52, 2)
        draw_cells(whole_number(data.luas_mezzanine), 1047, 171, 102, 4)

        def draw_any_group(group_values, x, y, jpb_codes=()):
            if any(value for value in group_values) or code in jpb_codes:
                pdf.setFont('Helvetica-Bold', 20)
                pdf.drawCentredString(x + 14, page_h - y - 19, 'X')

        def draw_option(value, positions):
            selected = option_code(value)
            if selected in positions:
                x, y = positions[selected]
                pdf.setFont('Helvetica-Bold', 20)
                pdf.drawCentredString(x + 14, page_h - y - 19, 'X')

        class_positions_308 = {'1': (300, 308), '2': (522, 308), '3': (722, 308), '4': (949, 308)}
        class_positions_403 = {'1': (300, 403), '2': (522, 403), '3': (722, 403), '4': (949, 403)}
        class_positions_500 = {'1': (300, 500), '2': (522, 500), '3': (722, 500), '4': (949, 500)}
        class_positions_650 = {'1': (300, 650), '2': (522, 650), '3': (722, 650), '4': (949, 650)}
        class_positions_1026 = {'1': (300, 1026), '2': (522, 1026), '3': (722, 1026), '4': (949, 1026)}

        draw_any_group([data.kelas_bangunan_perkantoran], 50, 276, (2, 9))
        draw_option(data.kelas_bangunan_perkantoran, class_positions_308)
        draw_any_group([data.kelas_bangunan_toko], 50, 373, (4,))
        draw_option(data.kelas_bangunan_toko, class_positions_403)
        draw_any_group([data.kelas_bangunan_rs, data.luas_kamar_ac_central_rs, data.luas_ruang_lain_ac_central_rs], 50, 468, (5,))
        draw_option(data.kelas_bangunan_rs, class_positions_500)
        draw_cells(whole_number(data.luas_kamar_ac_central_rs), 300, 533, 126, 5)
        draw_cells(whole_number(data.luas_ruang_lain_ac_central_rs), 998, 533, 127, 5)
        draw_any_group([data.kelas_bangunan_olahraga], 50, 619, (6,))
        draw_option(data.kelas_bangunan_olahraga, class_positions_650)

        draw_any_group([
            data.jenis_hotel, data.jumlah_bintang, data.jumlah_kamar,
            data.luas_kamar_ac_central_hotel, data.luas_ruang_lain_ac_central_hotel
        ], 50, 714, (7,))
        draw_option(data.jenis_hotel, {'1': (300, 743), '2': (722, 743)})
        draw_option(data.jumlah_bintang, {
            '1': (300, 773), '2': (472, 773), '3': (648, 773),
            '4': (821, 773), '5': (998, 773)
        })
        draw_cells(whole_number(data.jumlah_kamar), 300, 807, 101, 4)
        draw_cells(whole_number(data.luas_kamar_ac_central_hotel), 648, 807, 126, 5)
        draw_cells(whole_number(data.luas_ruang_lain_ac_central_hotel), 1023, 807, 126, 5)

        draw_any_group([data.tipe_bangunan_parkir], 50, 893, (12,))
        draw_option(data.tipe_bangunan_parkir, {'1': (300, 925), '2': (522, 925), '3': (722, 925), '4': (949, 925)})
        draw_any_group([
            data.kelas_bangunan_apartemen, data.jumlah_apartemen,
            data.luas_kamar_ac_central_apartemen, data.luas_ruang_lain_ac_central_apartemen
        ], 50, 990, (13,))
        draw_option(data.kelas_bangunan_apartemen, class_positions_1026)
        draw_cells(whole_number(data.jumlah_apartemen), 272, 1059, 129, 5)
        draw_cells(whole_number(data.luas_kamar_ac_central_apartemen), 648, 1059, 126, 5)
        draw_cells(whole_number(data.luas_ruang_lain_ac_central_apartemen), 1023, 1059, 126, 5)
        draw_any_group([data.kapasitas_tangki, data.letak_tangki], 50, 1143, (15,))
        draw_cells(whole_number(data.kapasitas_tangki), 324, 1175, 127, 5)
        draw_option(data.letak_tangki, {'1': (673, 1175), '2': (870, 1175)})
        draw_any_group([data.kelas_bangunan_sekolah], 50, 1225, (16,))
        draw_option(data.kelas_bangunan_sekolah, {'1': (398, 1258), '2': (574, 1258)})

        draw_date(data.created_at, 349, 1430)
        draw_date(data.created_at, 349, 1456)
        draw_date(data.created_at, 870, 1456)
        pdf.showPage()

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

def resolve_kop_type(data):
    kop_type = data.region_type
    if kop_type:
        return kop_type

    nop = data.nop or ""
    if nop.startswith("3676"):
        return "tangsel"
    if nop.startswith("3719"):
        return "kab_tangerang"
    return "tangsel"

app.jinja_env.globals.update(
    digits_only=digits_only,
    option_code=option_code,
    whole_number=whole_number,
    split_rt_rw=split_rt_rw
)

with app.app_context():
    db.create_all()
    ensure_extra_columns()

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Silakan login sebagai admin terlebih dahulu.")
            return redirect(url_for('admin_login'))
        return view(*args, **kwargs)
    return wrapped

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
            luas_bumi=form_float('luas_bumi'),
            kelas_zona_bumi=request.form.get('kelas_zona_bumi'),
            jenis_tanah=request.form.get('jenis_tanah'),
            jumlah_bangunan=form_int('jumlah_bangunan'),
            luas_bangunan=form_float('luas_bangunan'),
            longitude=request.form.get('longitude'),
            latitude=request.form.get('latitude'),
            
            # === DATA LSPOP ===
            jenis_penggunaan_bangunan=request.form.get('jenis_penggunaan_bangunan'),
            jumlah_lantai=form_int('jumlah_lantai'),
            tahun_dibangun=form_int('tahun_dibangun'),
            tahun_direnovasi=form_int('tahun_direnovasi'),
            daya_listrik=form_int('daya_listrik'),
            
            kondisi_pada_umumnya=request.form.get('kondisi_pada_umumnya'),
            konstruksi=request.form.get('konstruksi'),
            atap=request.form.get('atap'),
            dinding=request.form.get('dinding'),
            lantai=request.form.get('lantai'),
            langit_langit=request.form.get('langit_langit'),
            
            jumlah_ac_split=form_int('jumlah_ac_split'),
            jumlah_ac_window=form_int('jumlah_ac_window'),
            ac_sentral=request.form.get('ac_sentral'),
            luas_kolam_renang=form_float('luas_kolam_renang'),
            kolam_renang_tipe=request.form.get('kolam_renang_tipe'),
            
            luas_perkerasan_halaman_ringan=form_float('luas_perkerasan_halaman_ringan'),
            luas_perkerasan_halaman_sedang=form_float('luas_perkerasan_halaman_sedang'),
            luas_perkerasan_halaman_berat=form_float('luas_perkerasan_halaman_berat'),
            luas_perkerasan_halaman_dgn_penutup=form_float('luas_perkerasan_halaman_dgn_penutup'),
            
            jumlah_lift_penumpang=form_int('jumlah_lift_penumpang'),
            jumlah_lift_kapsul=form_int('jumlah_lift_kapsul'),
            jumlah_lift_barang=form_int('jumlah_lift_barang'),
            
            jumlah_tangga_berjalan_kurang=form_int('jumlah_tangga_berjalan_kurang'),
            jumlah_tangga_berjalan_lebih=form_int('jumlah_tangga_berjalan_lebih'),
            
            panjang_pagar=form_float('panjang_pagar'),
            bahan_pagar=request.form.get('bahan_pagar'),
            
            pemadam_hydrant=request.form.get('pemadam_hydrant'),
            pemadam_sprinkler=request.form.get('pemadam_sprinkler'),
            pemadam_fire_alarm=request.form.get('pemadam_fire_alarm'),
            
            jumlah_saluran_pes_pabx=form_int('jumlah_saluran_pes_pabx'),
            kedalaman_sumur_artesis=form_float('kedalaman_sumur_artesis'),

            tinggi_kolom=form_float('tinggi_kolom'),
            lebar_bentang=form_float('lebar_bentang'),
            daya_dukung_lantai=form_float('daya_dukung_lantai'),
            keliling_dinding=form_float('keliling_dinding'),
            luas_mezzanine=form_float('luas_mezzanine'),
            kelas_bangunan_perkantoran=request.form.get('kelas_bangunan_perkantoran'),
            kelas_bangunan_toko=request.form.get('kelas_bangunan_toko'),
            kelas_bangunan_rs=request.form.get('kelas_bangunan_rs'),
            luas_kamar_ac_central_rs=form_float('luas_kamar_ac_central_rs'),
            luas_ruang_lain_ac_central_rs=form_float('luas_ruang_lain_ac_central_rs'),
            kelas_bangunan_olahraga=request.form.get('kelas_bangunan_olahraga'),
            jenis_hotel=request.form.get('jenis_hotel'),
            jumlah_bintang=request.form.get('jumlah_bintang'),
            jumlah_kamar=form_int('jumlah_kamar'),
            luas_kamar_ac_central_hotel=form_float('luas_kamar_ac_central_hotel'),
            luas_ruang_lain_ac_central_hotel=form_float('luas_ruang_lain_ac_central_hotel'),
            tipe_bangunan_parkir=request.form.get('tipe_bangunan_parkir'),
            kelas_bangunan_apartemen=request.form.get('kelas_bangunan_apartemen'),
            jumlah_apartemen=form_int('jumlah_apartemen'),
            luas_kamar_ac_central_apartemen=form_float('luas_kamar_ac_central_apartemen'),
            luas_ruang_lain_ac_central_apartemen=form_float('luas_ruang_lain_ac_central_apartemen'),
            kapasitas_tangki=form_float('kapasitas_tangki'),
            letak_tangki=request.form.get('letak_tangki'),
            kelas_bangunan_sekolah=request.form.get('kelas_bangunan_sekolah')
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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        flash("Username atau password admin salah.")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Admin berhasil logout.")
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    entries = SpopData.query.order_by(SpopData.created_at.desc()).all()
    total = len(entries)
    tangsel_count = sum(1 for item in entries if item.region_type == 'tangsel')
    kab_count = sum(1 for item in entries if item.region_type == 'kab_tangerang')
    return render_template(
        'admin_dashboard.html',
        entries=entries,
        total=total,
        tangsel_count=tangsel_count,
        kab_count=kab_count
    )

@app.route('/cetak/<int:id>', methods=['GET'])
def cetak(id):
    data = SpopData.query.get_or_404(id)
    kop_type = resolve_kop_type(data)
    return render_template('pdf_template.html', data=data, kop_type=kop_type)

@app.route('/cetak/<int:id>/pdf', methods=['GET'])
def cetak_pdf(id):
    data = SpopData.query.get_or_404(id)
    kop_type = resolve_kop_type(data)
    filename = f'SPOP-{data.nop}.pdf'
    pdf_bytes = pdf_bytes_reportlab(data, kop_type)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/admin/export', methods=['GET'])
@admin_required
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

@app.route('/admin/export/<int:id>', methods=['GET'])
@admin_required
def export_single_excel(id):
    data = SpopData.query.get_or_404(id)
    df = pd.DataFrame([data.to_dict()])
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data_SPOP')
    excel_buffer.seek(0)
    safe_nop = digits_only(data.nop) or str(data.id)
    return send_file(
        excel_buffer,
        as_attachment=True,
        download_name=f'SPOP_{safe_nop}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    app.run(debug=False, port=5000, use_reloader=False)
