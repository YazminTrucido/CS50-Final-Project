from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import smtplib  # send email
import datetime  # datetime module

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final-project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():

    return render_template("index.html")


@app.route("/services", methods=["GET", "POST"])
def services():

    return render_template("services.html")


# NO PERMITIR REENVIAR FORMULARIO CON REFRESH
# COMO ENMASCARAR DATOS DE CREDENCIALES
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":
        # Remove accent marks and others
        name = (request.form.get("nombre")).encode(
            encoding="ascii", errors="replace").decode()
        type = (request.form.get("type")).encode(
            encoding="ascii", errors="replace").decode()
        ask = (request.form.get("ask")).encode(
            encoding="ascii", errors="replace").decode()
        customer_email = request.form.get("email").encode(
            encoding="ascii", errors="replace").decode()
        phone = request.form.get("phone").encode(
            encoding="ascii", errors="replace").decode()

        # Get our email credentials from DB
        rows = db.execute("SELECT * FROM credentials")

        if len(rows) != 1:
            return apology("error al enviar el formulario de consulta", 403)

        try:
            email = rows[0]["email"]
            receiver = rows[0]["email"]
            subject = "CONSULTA FINAL PROJECT CS50"
            message = f"Nombre y apellido: {name}\n\nCorreo electronico: {customer_email}\n\nCelular: {phone}\n\nTipo de consulta: {type}\n\nConsulta: {ask}"
            text = f"Subject: {subject}\n\n{message}"

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email, rows[0]["password"])

            server.sendmail(email, receiver, text)

            # Insert into DB
            db.execute(
                "INSERT INTO contacts (name, email, phone, type, text) VALUES(?, ?, ?, ?, ?)",
                request.form.get("nombre"),
                request.form.get("email"),
                request.form.get("phone"),
                request.form.get("type"),
                request.form.get("ask")
            )

        except:
            return apology("error al enviar el formulario de consulta", 403)

        flash('Consulta enviada con exito')
        return render_template("contact.html")

    else:
        return render_template("contact.html")


@login_required
@app.route("/book", methods=["GET", "POST"])
def book():

    return render_template("book.html")


@login_required
@app.route("/inventory", methods=["GET", "POST"])
def inventory():

    prodList = db.execute("SELECT * FROM inventory")

    # User reached route via POST to add product
    if request.method == "POST" and request.form.get("nameMod") != None:
        try:
            prodName = request.form.get("nameMod")
            notes = request.form.get("notesMod")
            quantity = request.form.get("quantMod")
            currentDT = datetime.datetime.now()

            # Update product into DB
            db.execute(
                "UPDATE inventory SET notes = ?, quantity = ?, lastModifiedDate = ? WHERE name = ?",
                notes,
                quantity,
                currentDT,
                prodName
            )

        except:
            return apology("error al modificar el articulo")

        # Redirect user to same page
        flash('Articulo modificado con exito')
        return redirect("/inventory")

    # User reached route via POST to modify product
    elif request.method == "POST" and request.form.get("nameAdd") != None:
        try:
            prodName = request.form.get("nameAdd")
            notes = request.form.get("notesAdd")
            quantity = request.form.get("quantAdd")

            # Insert product into DB
            db.execute(
                "INSERT INTO inventory (name, quantity, notes) VALUES(?, ?, ?)",
                prodName,
                quantity,
                notes
            )

        except:
            return apology("error al añadir un articulo")

        # Redirect user to same page
        flash('Articulo añadido con exito')
        return redirect("/inventory")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("inventory.html", rows=prodList)


@login_required
@app.route("/answer", methods=["GET", "POST"])
def answer():
    contactsList = db.execute("SELECT * FROM contacts")

    if request.method == "POST":
        # Get answer text
        answer = (request.form.get("answer")).encode(
            encoding="ascii", errors="replace").decode()
        customer_name = (request.form["nombre"]).encode(
            encoding="ascii", errors="replace").decode()
        ask = (request.form["ask"]).encode(
            encoding="ascii", errors="replace").decode()

        # Get our email credentials from DB
        rows = db.execute("SELECT * FROM credentials")

        if len(rows) != 1:
            return apology("error al enviar el formulario de consulta", 403)

        try:
            # Make email
            email = rows[0]["email"]
            receiver = request.form.get("email")
            subject = "RESPUESTA FINAL PROJECT CS50"
            body = f"Sr/a {customer_name},\n\nAgradecemos su consulta: {ask}\n\n{answer}\n\nCualquier otra consulta a las ordenes\n\nEsturion Party's"
            message = f"Subject: {subject}\n\n{body}"

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email, rows[0]["password"])

            server.sendmail(email, receiver, message)

            # Update status
            db.execute(
                "UPDATE contacts SET status = ? WHERE startDate = ? AND name = ?",
                'Atendido',
                request.form.get("startDate"),
                request.form.get("nombre")
            )

        except:
            return apology("error al enviar respuesta")

        # Redirect user to same page
        flash('Respuesta enviada con exito')
        return redirect("/answer")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        rows = db.execute("SELECT * FROM contacts")
        return render_template("answer.html", rows=contactsList)


@login_required
@app.route("/management", methods=["GET", "POST"])
def management():
    rows = db.execute(
        "SELECT * FROM users JOIN roles ON users.rol_id = roles.id")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("name"):
            flash('debe proporcionar un nombre de usuario')
            return render_template("management.html")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("name")
        )

        # Ensure username exists and password is correct
        if len(rows) > 0:
            flash('nombre de usuario proporcionado ya existe')
            return render_template("management.html")

        try:
            phone = request.form.get("phone")
            rolName = "personal"
            roles = db.execute(
                "SELECT * FROM roles WHERE rol = ?", rolName
            )

            # Password value is set into DB by default
            db.execute(
                "INSERT INTO users (username, rol_id, phone) VALUES(?, ?, ?)",
                request.form.get("name"),
                roles[0]["id"],
                phone
            )

        except:
            return apology("error al registrar un nuevo usuario", 403)

        # Redirect user to home page
        flash('Usuario registrado con exito')
        return redirect("/management")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("management.html", rows=rows)


@login_required
@app.route("/profile", methods=["GET", "POST"])
def profile():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get user data
        try:
            # Query database for user
            rows = db.execute(
                "SELECT * FROM users JOIN roles ON users.rol_id = roles.id WHERE username = ?", session["user_name"]
            )

            if not (check_password_hash(rows[0]["password"], request.form.get("oldPssw")) or rows[0]["password"] == request.form.get("oldPssw")):
                flash('Contraseña anterior incorrecta')
                return redirect("/profile")

            # Ensure password confirmation
            elif request.form.get("newPssw") != request.form.get("confirm"):
                flash('Contraseña nueva y confirmación no coinciden')
                return redirect("/profile")

            # Encript new pssw and update record
            passw = generate_password_hash(request.form.get("newPssw"))
            currentDT = datetime.datetime.now()
            db.execute(
                "UPDATE users SET password = ?, lastModifiedDate = ? WHERE username = ?",
                passw,
                currentDT,
                session["user_name"]
            )

        except:
            return apology("error con información de usuario")

        # Redirect user to same page
        flash('Perfil actualizado con exito')
        return redirect("/profile")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("profile.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("debe proporcionar un nombre de usuario", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("debe proporcionar una contraseña", 403)

        try:
            # Query database for username
            rows = db.execute(
                "SELECT * FROM users JOIN roles ON users.rol_id = roles.id WHERE username = ?",
                request.form.get("username")
            )

            # Ensure username exists and password is correct
            if len(rows) != 1 and not(check_password_hash(rows[0]["password"], request.form.get("password")) or request.form.get("password") == rows[0]["password"]):
                return apology("nombre de usuario y/o contraseña inválido", 403)

            # Remember which user has logged in
            session["user_name"]=rows[0]["username"]
            session["rol"]=rows[0]["rol"]
            session["phone"]=rows[0]["phone"]

        except:
            return apology("error al iniciar sesión de usuario", 403)

        # Redirect user to home page
        flash('Has iniciado sesión con exito')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash('Has cerrado sesión con exito')
    return redirect("/")
