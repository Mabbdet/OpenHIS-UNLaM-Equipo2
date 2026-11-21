import tkinter as tk

from tests.test_entrega9 import entorno
from tests.test_final import final
from final_app import GestionTurnosApp
import portal
from seguridad import AccesoDenegado
import pytest


def test_habilitar_y_revocar_acceso_desde_escritorio(final,raiz_tk):
    s,ses,r,p,*_=final
    app=GestionTurnosApp(raiz_tk,r);app.paciente.seleccionar(p['id'])
    app.habilitar_web()
    ventanas=[w for w in raiz_tk.winfo_children() if isinstance(w,tk.Toplevel)]
    assert len(ventanas)==1
    with s._repo.conectar() as c:
        acceso=c.execute('SELECT * FROM AccesosPortal WHERE paciente_id=?',(p['id'],)).fetchone()
        assert acceso['activo']==1 and acceso['password_hash'].startswith('pbkdf2_sha256$')
    ventanas[0].destroy()
    app.deshabilitar_web()
    with s._repo.conectar() as c:assert c.execute('SELECT activo FROM AccesosPortal WHERE paciente_id=?',(p['id'],)).fetchone()[0]==0


def test_administrativo_habilita_clave_y_renovar_invalida_la_anterior(final):
    s,ses,r,p,*_=final
    s.guardar_usuario(ses,dict(usuario='recepcion_web',password='PruebaClave123',nombre_completo='Recepción ficticia',rol='administrativo'))
    repo=s.repositorio(s.autenticar('recepcion_web','PruebaClave123'))
    primera=portal.habilitar_acceso(repo,p['id']);servicio=portal.Portal(s._repo.ruta)
    sesion=servicio.ingresar(p['dni'],primera)
    nueva=portal.habilitar_acceso(repo,p['id'])
    with pytest.raises(AccesoDenegado):servicio.ingresar(p['dni'],primera)
    with pytest.raises(AccesoDenegado):servicio.identidad(sesion)
    assert servicio.ingresar(p['dni'],nueva)['paciente_id']==p['id']
