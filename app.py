from flask import Flask, render_template, request, redirect, session, flash
import pymysql

app = Flask(__name__)
app.secret_key = 'secret_key'

# Koneksi ke database
db = pymysql.connect(host='localhost', user='root', password='password', db='db_sewa_motor')
cursor = db.cursor()

# Rute halaman utama
@app.route('/')
def index():
    return render_template('index.html')

# Rute login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Cek login dari database
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]  # Simpan user_id di session

            if user[6] == 'admin':
                return redirect('/admin')  # Jika admin, arahkan ke halaman admin
            else:
                return redirect('/user')  # Jika pengguna biasa, arahkan ke halaman user
        else:
            return render_template('login.html', error='Invalid email or password')
    else:
        return render_template('login.html', error='')

# Rute register admin dan user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        nama = request.form.get('nama')
        password = request.form.get('password')
        alamat = request.form.get('alamat')
        no_ktp = request.form.get('no_ktp')
        role = request.form.get('role')

        if not role:  # Memastikan 'role' tidak kosong
            return render_template('register.html', error='Role is required')

        # Validasi email unik
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return render_template('register.html', error='Email already exists')

        # Simpan data register admin atau user ke database
        cursor.execute("INSERT INTO users (email, nama, password, alamat, no_ktp, role) VALUES (%s, %s, %s, %s, %s, %s)",
                       (email, nama, password, alamat, no_ktp, role))
        db.commit()

        return redirect('/')  # Mengarahkan pengguna ke halaman utama (index)
    else:
        return render_template('register.html')

# Rute logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Hapus user_id dari session
    return redirect('/')

# Rute profil pengguna
@app.route('/profile')
def profile():
    if 'user_id' in session:
        user_id = session['user_id']

        # Ambil data pengguna dari database
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        return render_template('profile.html', user=user)
    else:
        return redirect('/login')

# Rute admin
@app.route('/admin')
def admin():
    if 'user_id' in session:
        user_id = session['user_id']

        # Ambil data pengguna dari database
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and user[6] == 'admin':
            # Mengambil data motor dari database
            cursor.execute("SELECT * FROM motor_rentals")
            motor_rentals = cursor.fetchall()

            return render_template('admin.html', motor_rentals=motor_rentals)
        else:
            return redirect('/profile')
    else:
        return redirect('/login')

# Rute daftar motor yang direntalkan
@app.route('/user')
def user():
    if 'user_id' in session:
        # Ambil data motor dari database
        cursor.execute("SELECT * FROM motor_rentals")
        motor_rentals = cursor.fetchall()

        return render_template('user.html', motor_rentals=motor_rentals)
    else:
        return redirect('/login')
    
# Route for renting a motor
@app.route('/rent', methods=['POST'])
def rent():
    if 'user_id' in session:
        user_id = session['user_id']
        id_motor = request.form.get('id_motor')
        jenis_transaksi = request.form.get('jenis_transaksi')
        tanggal_pinjam = request.form.get('tanggal_pinjam')
        tanggal_kembali = request.form.get('tanggal_kembali')

        # Insert the booking data into the 'bookings' table
        cursor.execute("INSERT INTO bookings (id_user, id_motor, jenis_transaksi, tanggal_pinjam, tanggal_kembali) VALUES (%s, %s, %s, %s, %s)",
                       (user_id, id_motor, jenis_transaksi, tanggal_pinjam, tanggal_kembali))
        db.commit()

        flash('Booking berhasil dilakukan')
        return redirect('/motor_list')  # Redirect to the motor list page
    else:
        return redirect('/login')


# Rute daftar motor yang direntalkan
@app.route('/motor_list')
def motor_list():
    if 'user_id' in session:
        # Ambil data motor dari database
        cursor.execute("SELECT * FROM motor_rentals")
        motor_rentals = cursor.fetchall()

        return render_template('motor_list.html', motor_rentals=motor_rentals)
    else:
        return redirect('/login')

# Rute tambah motor
@app.route('/add_motor', methods=['GET', 'POST'])
def add_motor():
    if request.method == 'POST':
        image = request.files['image']
        jenis_motor = request.form.get('jenis_motor')
        jumlah_motor = request.form.get('jumlah_motor')
        tahun_motor = request.form.get('tahun_motor')
        warna_motor = request.form.get('warna_motor')
        deskripsi = request.form.get('deskripsi')
        harga = request.form.get('harga')
        pemilik = request.form.get('pemilik')

        # Simpan data motor baru ke database
        cursor.execute("INSERT INTO motor_rentals (image, jenis_motor, jumlah_motor, tahun_motor, warna_motor, deskripsi, harga, pemilik) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (image.filename, jenis_motor, jumlah_motor, tahun_motor, warna_motor, deskripsi, harga, pemilik))
        db.commit()

        flash('Motor berhasil ditambahkan')
        return redirect('/admin')
    else:
        return render_template('add_motor.html')
    
## Rute detail motor
@app.route('/detail_motor/<int:motor_id>', methods=['GET'])
def detail_motor(motor_id):
    if 'user_id' in session:
        user_id = session['user_id']

        # Ambil data pengguna dari database
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            if user[6] == 'user':
                # Ambil data motor berdasarkan motor_id
                cursor.execute("SELECT * FROM motor_rentals WHERE id = %s", (motor_id,))
                motor = cursor.fetchone()

                if motor:
                    return render_template('motor_detail.html', motor_id=motor_id, motor=motor)
                else:
                    flash("Motor ID tidak ditemukan")
                    return redirect('/user')
            elif user[6] == 'admin':
                # Ambil data motor berdasarkan motor_id
                cursor.execute("SELECT * FROM motor_rentals WHERE id = %s", (motor_id,))
                motor = cursor.fetchone()

                if motor:
                    return render_template('motor_detail.html', motor_id=motor_id, motor=motor)
                else:
                    flash("Motor ID tidak ditemukan")
                    return redirect('/admin')
            else:
                return redirect('/profile')
        else:
            return redirect('/profile')
    else:
        return redirect('/login')



# Rute edit motor
@app.route('/edit_motor/<int:motor_id>', methods=['GET', 'POST'])
def edit_motor(motor_id):
    if 'user_id' in session:
        user_id = session['user_id']

        # Ambil data pengguna dari database
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and user[6] == 'admin':
            # Ambil data motor berdasarkan motor_id
            cursor.execute("SELECT * FROM motor_rentals WHERE id = %s", (motor_id,))
            motor = cursor.fetchone()

            if motor:
                return render_template('edit_motor.html', motor_id=motor_id, motor=motor)
            else:
                flash("Motor ID tidak ditemukan")
                return redirect('/admin')
        else:
            return redirect('/profile')
    else:
        return redirect('/login')

# Rute hapus motor
@app.route('/delete_motor/<int:motor_id>', methods=['POST'])
def delete_motor(motor_id):
    if 'user_id' in session:
        user_id = session['user_id']

        # Ambil data pengguna dari database
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and user[6] == 'admin':
            # Periksa apakah ID motor tersedia dalam database sebelum menghapus
            cursor.execute("SELECT * FROM motor_rentals WHERE id = %s", (motor_id,))
            existing_motor = cursor.fetchone()

            if existing_motor:
                # Hapus data motor dari tabel 'motor_rentals'
                cursor.execute("DELETE FROM motor_rentals WHERE id = %s", (motor_id,))
                db.commit()

                return redirect('/admin')
            else:
                flash("Motor ID tidak ditemukan")
                return redirect('/admin')
        else:
            return redirect('/profile')
    else:
        return redirect('/login')

# Rute update motor
@app.route('/update_motor', methods=['POST'])
def update_motor():
    if 'user_id' in session:
        user_id = session['user_id']

        # Ambil data pengguna dari database
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and user[6] == 'admin':
            if request.method == 'POST':
                motor_id = request.form.get('motor_id')
                jenis_motor = request.form.get('jenis_motor')
                tahun_motor = request.form.get('tahun_motor')
                warna_motor = request.form.get('warna_motor')
                jumlah_motor = request.form.get('jumlah_motor')
                pemilik = request.form.get('pemilik')
                deskripsi = request.form.get('deskripsi')
                harga = request.form.get('harga')

                # Periksa apakah ID motor tersedia dalam database sebelum melakukan pembaruan
                cursor.execute("SELECT * FROM motor_rentals WHERE id = %s", (motor_id,))
                existing_motor = cursor.fetchone()

                if existing_motor:
                    # Update data motor ke dalam tabel 'motor_rentals'
                    sql = "UPDATE motor_rentals SET jenis_motor = %s, tahun_motor = %s, warna_motor = %s, jumlah_motor = %s, pemilik = %s, deskripsi = %s, harga = %s WHERE id = %s"
                    cursor.execute(sql, (jenis_motor, tahun_motor, warna_motor, jumlah_motor, pemilik, deskripsi, harga, motor_id))
                    db.commit()

                    flash('Motor berhasil diperbarui')
                    return redirect('/admin')
                else:
                    flash('Motor ID tidak ditemukan')
                    return redirect('/admin')
            else:
                return redirect('/admin')
        else:
            return redirect('/profile')
    else:
        return redirect('/login')


# Rute daftar pengguna
@app.route('/admin/users_list')
def users_list():
    if 'user_id' in session:
        # Ambil data pengguna dari database
        cursor.execute("SELECT * FROM users WHERE role = 'user'")
        users = cursor.fetchall()

        return render_template('users_list.html', users=users)
    else:
        return redirect('/login')
    

if __name__ == '__main__':
    app.run(debug=True)

