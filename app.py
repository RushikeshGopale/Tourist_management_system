from flask import Flask,render_template,request,redirect,session,send_file,url_for
import mysql.connector
from fpdf import FPDF

app=Flask(__name__)
app.secret_key="tourist123"

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="touristuser",
        password="tourist123",
        database="tourist_db"
    )

# ---------------- LOGIN ----------------
@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/register_user",methods=["POST"])
def register_user():
    conn=get_connection()
    cur=conn.cursor()
    cur.execute(
        "INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
        (request.form["username"],request.form["email"],request.form["password"])
    )
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/login_user",methods=["POST"])
def login_user():
    conn=get_connection()
    cur=conn.cursor()
    cur.execute(
        "SELECT username,role FROM users WHERE email=%s AND password=%s",
        (request.form["email"],request.form["password"])
    )
    user=cur.fetchone()
    conn.close()

    if user:
        session["user"]=user[0]
        session["role"]=user[1]
        if user[1]=="admin":
            return redirect("/admin_dashboard")
        return redirect("/dashboard")
    return "Invalid Login"

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html",username=session["user"])

@app.route("/places")
def places():
    if "user" not in session:
        return redirect("/")
    return render_template("places.html")

# ---------------- BOOK ----------------
@app.route("/book", methods=["POST"])
def book():
    if "user" not in session:
        return redirect("/")

    trip_data={
        "Goa":{"days":3,"price":3000,"bus":"Yes"},
        "Manali":{"days":5,"price":2500,"bus":"Yes"},
        "Jaipur":{"days":2,"price":2000,"bus":"Yes"},
        "Kerala":{"days":4,"price":2800,"bus":"Yes"}
    }

    place=request.form["place"]
    date=request.form["date"]
    persons=int(request.form["persons"])

    days=trip_data[place]["days"]
    price=trip_data[place]["price"]
    bus=trip_data[place]["bus"]

    total_cost=persons*days*price

    conn=get_connection()
    cur=conn.cursor()
    cur.execute(
        """INSERT INTO bookings
        (username,place_name,travel_date,persons,days,total_cost,bus_available)
        VALUES(%s,%s,%s,%s,%s,%s,%s)""",
        (session["user"],place,date,persons,days,total_cost,bus)
    )
    conn.commit()
    conn.close()

    return redirect("/confirm_booking")

# ---------------- CONFIRM BOOKING ----------------
@app.route("/confirm_booking")
def confirm_booking():
    if "user" not in session:
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()
    cur.execute(
        """SELECT id,place_name,travel_date,persons,days,total_cost,bus_available
        FROM bookings WHERE username=%s ORDER BY id DESC LIMIT 1""",
        (session["user"],)
    )
    booking=cur.fetchone()
    conn.close()

    return render_template("confirm_booking.html",booking=booking)

# ---------------- MY BOOKINGS ----------------
@app.route("/my_bookings")
def my_bookings():
    if "user" not in session:
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()
    cur.execute(
        """SELECT id,place_name,travel_date,persons,days,total_cost,bus_available
        FROM bookings WHERE username=%s""",
        (session["user"],)
    )
    data=cur.fetchall()
    conn.close()

    return render_template("my_bookings.html",data=data)

# ---------------- CANCEL BOOKING ----------------
@app.route("/cancel/<int:id>")
def cancel(id):
    if "user" not in session:
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()

    # delete ONLY logged-in user's booking
    cur.execute(
        "DELETE FROM bookings WHERE id=%s AND username=%s",
        (id,session["user"])
    )
    conn.commit()
    conn.close()

    return redirect("/my_bookings")

# ---------------- DOWNLOAD TICKET ----------------
@app.route("/download_ticket")
def download_ticket():
    if "user" not in session:
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()
    cur.execute(
        """SELECT place_name,travel_date,persons,days,total_cost,bus_available
        FROM bookings WHERE username=%s ORDER BY id DESC LIMIT 1""",
        (session["user"],)
    )
    b=cur.fetchone()
    conn.close()

    pdf=FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",18)
    pdf.cell(0,10,"Naik Sai Tourist - Travel Ticket",ln=True,align="C")

    pdf.ln(10)
    pdf.set_font("Arial","",12)

    pdf.cell(0,10,f"Passenger Name : {session['user']}",ln=True)
    pdf.cell(0,10,f"Destination     : {b[0]}",ln=True)
    pdf.cell(0,10,f"Travel Date     : {b[1]}",ln=True)
    pdf.cell(0,10,f"Persons         : {b[2]}",ln=True)
    pdf.cell(0,10,f"Trip Duration   : {b[3]} Days",ln=True)
    pdf.cell(0,10,f"Bus Available   : {b[5]}",ln=True)
    pdf.cell(0,10,f"Total Cost      : Rs. {b[4]}",ln=True)

    pdf.output("ticket.pdf")
    return send_file("ticket.pdf",as_attachment=True)

# ---------------- ADMIN ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    conn=get_connection()
    cur=conn.cursor()
    cur.execute("SELECT * FROM bookings")
    data=cur.fetchall()
    conn.close()
    return render_template("admin_dashboard.html",bookings=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
