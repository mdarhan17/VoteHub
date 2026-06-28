import random
from datetime import datetime, timedelta
from app.extensions import mysql

def generate_otp():
    return str(random.randint(100000, 999999))

def save_otp(email, purpose="register"):
    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=10)

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE otp_verifications
        SET is_used=1
        WHERE email=%s AND purpose=%s AND is_used=0
    """, (email, purpose))

    cur.execute("""
        INSERT INTO otp_verifications
        (email, otp_code, purpose, is_used, expires_at)
        VALUES (%s, %s, %s, 0, %s)
    """, (email, otp, purpose, expires_at))

    mysql.connection.commit()
    cur.close()

    return otp

def verify_otp_code(email, otp_code, purpose="register"):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT * FROM otp_verifications
        WHERE email=%s AND otp_code=%s AND purpose=%s AND is_used=0
        ORDER BY otp_id DESC
        LIMIT 1
    """, (email, otp_code, purpose))

    otp_record = cur.fetchone()

    if not otp_record:
        cur.close()
        return False, "Invalid OTP."

    if otp_record["expires_at"] < datetime.now():
        cur.close()
        return False, "OTP expired."

    cur.execute("""
        UPDATE otp_verifications
        SET is_used=1
        WHERE otp_id=%s
    """, (otp_record["otp_id"],))

    mysql.connection.commit()
    cur.close()

    return True, "OTP verified successfully."
