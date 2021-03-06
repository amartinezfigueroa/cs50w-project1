import os
from django.shortcuts import redirect

from flask import Flask,flash, session, render_template,redirect, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
from helper import login_required
import datetime
import requests


load_dotenv()

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgresql://guoakllcseoxhk:c668ba40006b4d6122f65751cf2b3df659f02b284534809fa11af022a58109a2@ec2-18-215-96-22.compute-1.amazonaws.com:5432/d96asn15oirh76")
db = scoped_session(sessionmaker(bind=engine))


#usuarios

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/iniciosecion" ,methods=["POST" , "GET"])
def inisiosecion():
    session.clear()
    if request.method == "POST":
        
        if not request.form.get("nombre"):
            flash("Llenar todos los campos")
            return render_template("iniciosecion.html")

        usuarios = request.form.get("nombre")
        #print(usuarios)
        
        if not request.form.get("contraseña"):
            flash("Llenar todos los campos")
            return render_template("iniciosecion.html")

        password = request.form.get("contraseña")
        #print(password)

        consult = db.execute("SELECT * FROM usuarios WHERE usuario = :us and contraseña = :contra", {"us": usuarios, "contra": password}).fetchone()
        
        if len(consult) == 0:
            flash("El usuario no existe")
            return render_template("iniciosecion.html")

        
        print(consult[0])

        session["id_user"] = consult[0]
        return redirect("/")
     

    else:
        return render_template("iniciosecion.html")


@app.route("/registro", methods = ["POST", "GET"])
def registro():
    if request.method == "POST":
        rusuario = request.form.get("rusername")
        print(rusuario)

        rcontraseña = request.form.get("rpassword")
        print(rcontraseña)

        rconfirmacion = request.form.get("rconfirmation")
        print(rconfirmacion)

        if rcontraseña != rconfirmacion:
            flash("la contraseña no coincide")
            return render_template("registro.html") 
        
        usuario = db.execute('select usuario from usuarios where usuario = :usuario', {'usuario': rusuario}).rowcount
        print(usuario)

        #register["id_user"] = usuario[0]


        if usuario == 0:
            db.execute('Insert into usuarios (usuario , contraseña) values(:rusuario, :rcontraseña)', {'rusuario': rusuario, 'rcontraseña': rcontraseña})
            db.commit()
            return render_template("index.html")
        else:
            flash("El usuario ya existe")
            return render_template("registro.html")

        
        return render_template("layout.html")
           
    else:
        return render_template("registro.html")
      

@app.route("/busqueda", methods = ["POST", "GET"])
def busqueda():

    if request.method == "POST":
        busca = request.form.get("busqueda")
        print(busca)
       
        buscar = db.execute('select * from libros where isbn like :buscarr or title like :buscarr or author like :buscarr or year like :buscarr', {'buscarr': '%' + busca +'%'}).fetchall()

        for row in buscar:
            print(row)
            return render_template("busqueda.html", buscar=buscar)
        else:
            flash("No se encontraron coincidencias")
        return render_template("busqueda.html")
        
    return render_template("busqueda.html")

@app.route("/busqueda/<isbn>", methods = ["POST", "GET"])
def info(isbn):
    print(isbn)
    isbn = db.execute('select * from libros where isbn = :informa', {'informa': isbn}).fetchone()
    if request.method == "POST":
       
        puntuacion = request.form.get("puntuacion")
        r = request.form.get("r")
        print(puntuacion)
        print(r)

        db.execute('Insert into puntuacion (comentario , fecha_comentario, puntuacion, id_libro_fk, id_usuario_fk) values(:comentario, :fecha_comentario, :puntuacion, :id_libro_fk, :id_usuario_fk)', {'comentario' :r, 'fecha_comentario' : datetime.datetime.now(), 'puntuacion' :puntuacion, 'id_libro_fk' :isbn.id_libros, 'id_usuario_fk' :session["id_user"]})
        db.commit()
        return render_template("book.html", isbn = isbn)
  
    return render_template("book.html", isbn = isbn)

@app.route("/Cerrarsecion")
def cerrar():

    session.clear()

    return render_template ("iniciosecion.html")

@app.route("/api/<isbn>", methods = ["POST", "GET"])
def api(isbn):
    
    con = db.execute('select isbn,title,author,year from libros where isbn like :buscarr', {'buscarr':isbn}).fetchone()
    
    if con is None:
        return {"Error": "No hay resultados"}

    response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()
    print(response)

    try:

        response = response ["items"][0]
        averageRating = response ["volumeInfo"]["averageRating"]
        print(averageRating)
        ratingsCount = response ["volumeInfo"]["ratingsCount"]
        print(ratingsCount)
    except:
        averageRating = 0
        ratingsCount = 0

    diccionario = con._asdict()
    diccionario["review_count"] = ratingsCount
    diccionario["average_score"] = averageRating
    return diccionario