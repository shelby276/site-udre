import os, sqlite3, secrets, csv, io
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, session, url_for, abort, Response, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changez-moi")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changez-moi")
DB = os.environ.get("DB_PATH", "udre.db")
PAIEMENT = "0823740122"
PRIX = 10

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("""CREATE TABLE IF NOT EXISTS membres(id INTEGER PRIMARY KEY, ref TEXT UNIQUE,
        nom TEXT, postnom TEXT, prenom TEXT, naissance TEXT, province TEXT, commune TEXT, quartier TEXT,
        telephone TEXT, email TEXT, statut TEXT DEFAULT 'en attente', cree TEXT)""")
    return g.db

@app.teardown_appcontext
def close(e):
    d = g.pop("db", None)
    if d: d.close()

def csrf():
    if "t" not in session: session["t"] = secrets.token_hex(16)
    return session["t"]
app.jinja_env.globals["csrf"] = csrf

def check():
    if request.form.get("t") != session.get("t"): abort(400)

@app.route("/")
def index(): return render_template("index.html")

@app.route("/a-propos")
def apropos(): return render_template("apropos.html")

@app.route("/organisation")
def organisation(): return render_template("organisation.html")

@app.route("/adhesion", methods=["GET", "POST"])
def adhesion():
    err = None
    if request.method == "POST":
        check()
        f = {k: request.form.get(k, "").strip()[:100] for k in
             ["nom", "postnom", "prenom", "naissance", "province", "commune", "quartier", "telephone", "email"]}
        try:
            n = datetime.strptime(f["naissance"], "%Y-%m-%d").date()
            age = (date.today() - n).days // 365.25
        except ValueError:
            age = 0
        if not (f["nom"] and f["prenom"] and f["telephone"] and f["province"]):
            err = "Remplissez les champs obligatoires."
        elif age < 18:
            err = "Il faut avoir 18 ans révolus pour adhérer."
        elif request.form.get("statuts") != "on" or request.form.get("nationalite") != "on":
            err = "Cochez les deux engagements pour continuer."
        if not err:
            ref = "UDRE-" + secrets.token_hex(3).upper()
            db().execute("INSERT INTO membres(ref,nom,postnom,prenom,naissance,province,commune,quartier,telephone,email,cree) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                         (ref, *[f[k] for k in ["nom", "postnom", "prenom", "naissance", "province", "commune", "quartier", "telephone", "email"]], datetime.now().isoformat(timespec="minutes")))
            db().commit()
            return render_template("merci.html", ref=ref, prix=PRIX, num=PAIEMENT)
    return render_template("adhesion.html", err=err, prix=PRIX)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and "mdp" in request.form:
        check()
        if secrets.compare_digest(request.form["mdp"], ADMIN_PASSWORD):
            session["admin"] = True
        return redirect(url_for("admin"))
    if not session.get("admin"): return render_template("login.html")
    rows = db().execute("SELECT * FROM membres ORDER BY id DESC").fetchall()
    return render_template("admin.html", rows=rows)

@app.post("/admin/valider/<int:i>")
def valider(i):
    if not session.get("admin"): abort(403)
    check()
    db().execute("UPDATE membres SET statut='actif' WHERE id=?", (i,)); db().commit()
    return redirect(url_for("admin"))

@app.route("/admin/export")
def export():
    if not session.get("admin"): abort(403)
    o = io.StringIO(); w = csv.writer(o)
    rows = db().execute("SELECT * FROM membres").fetchall()
    w.writerow(rows[0].keys() if rows else ["vide"])
    for r in rows: w.writerow(list(r))
    return Response(o.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=membres.csv"})

@app.route("/admin/sortir")
def sortir():
    session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(debug=False, port=5000)
