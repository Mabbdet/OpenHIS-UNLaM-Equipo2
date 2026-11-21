"""Portal local de turnos: python turnero_web.py. Comparte BD/Salud.db con Tkinter."""

import argparse
from collections import defaultdict, deque
from datetime import timedelta
from functools import wraps
import hmac
import secrets
import sqlite3
from threading import RLock
import time

from flask import Flask, g, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException

from datos import RUTA_BD, ErrorValidacion
from seguridad import AccesoDenegado
from portal import Portal


def crear_app(ruta=RUTA_BD,config=None):
    app=Flask(__name__,template_folder='web/templates',static_folder='web/static')
    app.config.update(SECRET_KEY=secrets.token_hex(32),SESSION_COOKIE_NAME='openhis_portal',
        SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SESSION_REFRESH_EACH_REQUEST=False,MAX_CONTENT_LENGTH=8192,TRUSTED_HOSTS=['localhost','127.0.0.1','[::1]'])
    if config:app.config.update(config)
    portal=Portal(ruta);app.extensions['portal']=portal
    accesos={};intentos=defaultdict(deque);bloqueo=RLock()
    app.extensions['accesos_portal']=accesos

    def csrf():
        if '_csrf' not in session:session['_csrf']=secrets.token_urlsafe(32)
        return session['_csrf']

    @app.before_request
    def proteger():
        if request.method in ('POST','PUT','PATCH','DELETE'):
            recibido=request.headers.get('X-CSRF-Token','')
            if not recibido or not hmac.compare_digest(recibido,session.get('_csrf','')):
                return jsonify(error='La sesión del formulario venció. Actualice la página.'),403

    @app.after_request
    def encabezados(respuesta):
        respuesta.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
            'X-Frame-Options':'DENY','Referrer-Policy':'no-referrer',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"})
        return respuesta

    def autenticado(f):
        @wraps(f)
        def envolver(*args,**kwargs):
            sid=session.get('sid')
            with bloqueo:
                entrada=accesos.get(sid)
                if not entrada or entrada['vence']<=time.monotonic():
                    accesos.pop(sid,None);raise AccesoDenegado('Ingrese para gestionar sus turnos.')
                g.identidad=dict(entrada['identidad'])
            portal.identidad(g.identidad)  # Revalida bajas y renovación de clave antes de cada petición.
            return f(*args,**kwargs)
        return envolver

    def datos():
        d=request.get_json()
        if not isinstance(d,dict):raise ErrorValidacion('El formulario es inválido.')
        return d

    @app.get('/')
    def inicio():return render_template('turnero.html')

    @app.get('/api/sesion')
    def estado():
        token=csrf();sid=session.get('sid')
        with bloqueo:entrada=accesos.get(sid)
        if entrada and entrada['vence']>time.monotonic():
            try:return jsonify(csrf=token,paciente=portal.identidad(entrada['identidad']))
            except AccesoDenegado:
                with bloqueo:accesos.pop(sid,None)
        return jsonify(csrf=token,paciente=None)

    @app.post('/api/ingresar')
    def ingresar():
        d=datos();ip=request.remote_addr or 'local';momento=time.monotonic()
        with bloqueo:
            # Límite por origen independiente de cookies y del DNI ingresado.
            for origen in list(intentos):
                while intentos[origen] and intentos[origen][0]<momento-300:intentos[origen].popleft()
                if not intentos[origen]:del intentos[origen]
            if len(intentos[ip])>=8:return jsonify(error='Demasiados intentos. Espere cinco minutos.'),429
            intentos[ip].append(momento)
        identidad=portal.ingresar(d.get('dni',''),d.get('clave',''))
        with bloqueo:
            accesos.pop(session.get('sid'),None)
            for sid in list(accesos):
                if accesos[sid]['vence']<=momento:del accesos[sid]
            sid=secrets.token_urlsafe(32)
            accesos[sid]={'identidad':identidad,'vence':momento+1800}
        session.clear();session.permanent=True;session['sid']=sid
        return jsonify(paciente=portal.identidad(identidad),csrf=csrf())

    @app.post('/api/salir')
    def salir():
        with bloqueo:entrada=accesos.pop(session.get('sid'),None)
        if entrada:
            try:portal.salir(entrada['identidad'])
            except AccesoDenegado:pass
        session.clear();return jsonify(ok=True,csrf=csrf())

    @app.get('/api/catalogos')
    @autenticado
    def catalogos():return jsonify(portal.catalogos(g.identidad))

    @app.get('/api/disponibles')
    @autenticado
    def disponibles():return jsonify(huecos=portal.disponibles(g.identidad,request.args.get('fecha'),request.args.get('profesional_id') or None,request.args.get('especialidad_id') or None))

    @app.get('/api/turnos')
    @autenticado
    def turnos():return jsonify(turnos=portal.mis_turnos(g.identidad))

    @app.post('/api/turnos')
    @autenticado
    def reservar():return jsonify(turno_id=portal.reservar(g.identidad,datos())),201

    @app.post('/api/turnos/<int:turno_id>/<accion>')
    @autenticado
    def gestionar(turno_id,accion):return jsonify(turno_id=portal.gestionar(g.identidad,turno_id,accion,datos()))

    @app.errorhandler(AccesoDenegado)
    def denegado(error):return jsonify(error=str(error)),401

    @app.errorhandler(ErrorValidacion)
    def invalido(error):return jsonify(error=str(error)),409

    @app.errorhandler(sqlite3.Error)
    def base_ocupada(error):
        app.logger.warning('Operación SQLite rechazada: %s',type(error).__name__)
        return jsonify(error='No se pudo guardar la operación. Actualice y vuelva a intentar.'),409

    @app.errorhandler(HTTPException)
    def http(error):return jsonify(error=error.description),error.code

    return app


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Turnero web local del Equipo 2')
    parser.add_argument('--puerto',type=int,default=5000);parser.add_argument('--bd',default=str(RUTA_BD))
    args=parser.parse_args()
    from waitress import serve
    app=crear_app(args.bd)
    print(f'Turnero web: http://127.0.0.1:{args.puerto}',flush=True)
    serve(app,host='127.0.0.1',port=args.puerto,threads=4)
