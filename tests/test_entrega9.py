import copy
import json
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET

from PIL import Image
import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
import pytest

from datos import Repositorio, ErrorValidacion
from seguridad import Seguridad, AccesoDenegado
from cargar_demo import cargar_demo
from entrega9_app import IntervencionesApp, FHIRApp, DICOMApp
import fhir
import dicom
import intervenciones


@pytest.fixture
def entorno(repositorio):
    cargar_demo(repositorio)
    s=Seguridad(repositorio.ruta)
    s.crear_admin_inicial('admin','AdminTest123','Admin prueba')
    sesion=s.autenticar('admin','AdminTest123')
    return s,sesion,s.repositorio(sesion)


def crear_bundle(repo,tmp_path):
    paciente=repo.listar_pacientes()[0]['id']
    profesional=repo.listar_profesionales()[0]['id']
    intervenciones.registrar_practica(repo,paciente,profesional,'PRAC-E9','Práctica sintética')
    return fhir.exportar(repo,paciente,tmp_path/'salida.json')


def guardar(bundle,tmp_path,nombre='entrada.json'):
    p=tmp_path/nombre;p.write_text(json.dumps(bundle,ensure_ascii=False),encoding='utf-8');return p


def test_consulta_trazable_incluye_anulados(entorno):
    s,sesion,r=entorno
    p=r.listar_pacientes()[0]['id']
    receta=r.listar_prescripciones(p)[0]['id'];r.anular_prescripcion(receta);r.dar_baja_paciente(p)
    info=intervenciones.consultar(r,p)
    assert info['paciente']['activo']==0
    assert next(f for f in info['prescripciones'] if f['id']==receta)['activo']==0
    assert s.listar_auditoria(sesion,accion='Q')[0]['registro_id']==p


@pytest.mark.parametrize('formato',['json','xml'])
def test_exportar_importar_y_reimportar(entorno,tmp_path,formato):
    s,sesion,r=entorno
    bundle=crear_bundle(r,tmp_path)
    paciente=r.listar_pacientes()[0]['id']
    path=tmp_path/('salida.'+formato)
    if formato=='json':path=tmp_path/'salida.json'
    else:fhir.exportar(r,paciente,path,'xml')
    datos=fhir.leer(path)
    assert {e['resource']['resourceType'] for e in datos['entry']} >= {'Patient','Practitioner','MedicationRequest','ServiceRequest'}
    otra=Seguridad(tmp_path/'otra.db');otra.crear_admin_inicial('otro','OtroTest123','Otro admin')
    ses=otra.autenticar('otro','OtroTest123');externo=otra.repositorio(ses)
    resultado=fhir.importar(externo,path,'Hospital E2')
    assert resultado['creados']['Pacientes']==1
    assert resultado['creados']['Practicas']==1
    assert resultado['creados']['Prescripciones']>=1
    info=intervenciones.consultar(externo,externo.listar_pacientes()[0]['id'])
    assert info['practicas'][0]['descripcion']=='Práctica sintética'
    receta=info['prescripciones'][0]
    original=next(e['resource'] for e in datos['entry'] if e['resource']['resourceType']=='MedicationRequest')
    assert receta['dosis']==original['dosageInstruction'][0]['text']
    segundo=fhir.importar(externo,path,'Hospital E2')
    assert segundo['creados']=={} and segundo['omitidos']>=2
    with otra._repo.conectar() as c:
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_reutilizar_dni_inactivo_conflicto_y_referencias_fullurl(entorno,tmp_path):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    paciente=next(e for e in bundle['entry'] if e['resource']['resourceType']=='Patient')
    profesional=next(e for e in bundle['entry'] if e['resource']['resourceType']=='Practitioner')
    pid=r.buscar_paciente(paciente['resource']['identifier'][0]['value'])['id']
    pro=r.buscar_profesional(profesional['resource']['identifier'][0]['value'])['id']
    r.dar_baja_paciente(pid);r.dar_baja_profesional(pro)
    paciente['resource']['name'][0]['family']='Apellido externo diferente'
    for e in bundle['entry']:
        if e['resource']['resourceType'] in ('ServiceRequest','MedicationRequest'):
            e['resource']['subject']['reference']=paciente['fullUrl']
            e['resource']['requester']['reference']=profesional['fullUrl']
    antes=len(r.listar_pacientes(None)),len(r.listar_profesionales(None))
    resultado=fhir.importar(r,guardar(bundle,tmp_path),'Otro centro')
    assert resultado['conflictos']
    assert antes==(len(r.listar_pacientes(None)),len(r.listar_profesionales(None)))
    assert r.obtener_paciente(pid)['activo']==0
    assert r.buscar_profesional(profesional['resource']['identifier'][0]['value'])['activo']==0


@pytest.mark.parametrize('caso',['referencia','codigo','fecha','numero','unidad','tipo','duplicado','matricula','cantidad','estado'])
def test_importacion_invalida_no_deja_datos_parciales(entorno,tmp_path,caso):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    obs=next((e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='Observation'),None)
    med=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='MedicationRequest')
    if obs is None:
        medcopy=med
        obs={'resourceType':'Observation','id':'obs-prueba','status':'final',
             'subject':medcopy['subject'],'performer':[medcopy['requester']],
             'effectiveDateTime':'2026-01-01T12:00:00Z','code':{'coding':[{'system':'http://loinc.org','code':'8867-4'}]},
             'valueQuantity':{'value':80,'unit':'/min'}}
        bundle['entry'].append({'resource':obs})
    if caso=='referencia':med['subject']['reference']='Patient/no-existe'
    elif caso=='codigo':obs['code']['coding'][0]['code']='no-soportado'
    elif caso=='fecha':med['authoredOn']='fecha inválida'
    elif caso=='numero':obs['valueQuantity']['value']=True
    elif caso=='unidad':obs['valueQuantity']['unit']='unidad-inválida';obs['valueQuantity']['code']='unidad-inválida'
    elif caso=='tipo':med['resourceType']='DiagnosticReport'
    elif caso=='duplicado':bundle['entry'].append(copy.deepcopy(bundle['entry'][0]))
    elif caso=='cantidad':med['dispenseRequest']={'quantity':{'value':'texto'}}
    elif caso=='estado':med['status']='revoked'
    elif caso=='matricula':
        pro=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='Practitioner')
        pro['identifier'][0]['value']='99911222' # Mismo número de matrícula, otro DNI.
    with s._repo.conectar() as c:antes=[c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['Pacientes','Profesionales','Prescripciones','Practicas','RecursosFHIR','Auditoria']]
    with pytest.raises((ErrorValidacion,ValueError)):fhir.importar(r,guardar(bundle,tmp_path),'Externo')
    with s._repo.conectar() as c:despues=[c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['Pacientes','Profesionales','Prescripciones','Practicas','RecursosFHIR','Auditoria']]
    assert antes==despues


def test_observation_deduplicacion_por_medicion_y_fecha(entorno,tmp_path):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    meds=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='MedicationRequest')
    bundle['entry']=[e for e in bundle['entry'] if e['resource']['resourceType'] in ('Patient','Practitioner')]
    obs={'resourceType':'Observation','id':'externa-1','status':'final','subject':meds['subject'],
         'performer':[meds['requester']],'effectiveDateTime':'2026-01-10T15:00:00-03:00',
         'code':{'coding':[{'system':'http://loinc.org','code':'8867-4'}]},'valueQuantity':{'value':79,'unit':'/min'}}
    bundle['entry'].append({'resource':obs})
    resultado=fhir.importar(r,guardar(bundle,tmp_path),'Centro')
    assert resultado['creados']['SignosVitales']==1
    obs['id']='externa-2';obs['effectiveDateTime']='2026-01-10T18:00:00Z'
    assert fhir.importar(r,guardar(bundle,tmp_path),'Centro')['omitidos']==1


def test_xml_seguro_y_archivo_grande(tmp_path):
    p=tmp_path/'hostil.xml';p.write_text('<!DOCTYPE a [<!ENTITY a SYSTEM "file:///secret">]><Bundle xmlns="http://hl7.org/fhir">&a;</Bundle>')
    with pytest.raises(ErrorValidacion):fhir.leer(p)
    p=tmp_path/'grande.json';p.write_bytes(b' '*5_000_001)
    with pytest.raises(ErrorValidacion):fhir.leer(p)


def test_profesional_externo_sin_datos_inventados(entorno,tmp_path):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    pro=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='Practitioner')
    pro['identifier'][0]['value']='99111222';pro['qualification'][0]['identifier'][0]['value']='EXTERNA-99'
    pro.pop('birthDate',None);pro.pop('gender',None)
    fhir.importar(r,guardar(bundle,tmp_path),'Centro nuevo')
    fila=r.buscar_profesional('99111222')
    assert fila['fecha_nacimiento'] is None and fila['sexo']=='U'
    assert fila['usuario_alta_id']==s.autorizar(sesion)['id']


def test_dicom_pixeles_privados_uid_y_anios(entorno,tmp_path):
    s,sesion,r=entorno
    imagen=tmp_path/'prueba.png';Image.new('L',(13,9),80).save(imagen)
    original=tmp_path/'original.dcm';anon=tmp_path/'anonimo.dcm'
    dicom.convertir(r,imagen,original,'1980','2026','F')
    ds=pydicom.dcmread(original);assert ds.Rows==9 and ds.Columns==13
    ds.PatientName='PACIENTE^SECRETO';ds.PatientID='DNI-SECRETO';ds.PatientAddress='DIRECCION-SECRETA'
    ds.PatientBirthDate='19800820';ds.StudyDate='20261020';ds.AccessionNumber='SECRETO'
    ds.add_new((0x0011,0x0010),'LO','CREADOR-SECRETO')
    nested=Dataset();nested.PatientName='SECRETO^ANIDADO';ds.RequestAttributesSequence=Sequence([nested])
    ds.save_as(original,enforce_file_format=True)
    dicom.anonimizar(r,original,anon);a=pydicom.dcmread(anon)
    assert a.PixelData==ds.PixelData
    assert a.PatientBirthDate=='19800101' and a.StudyDate=='20260101' and a.PatientSex=='F'
    assert a.PatientName=='ANONIMO' and a.PatientID=='ANONIMO'
    assert not any(e.tag.is_private for e in a.iterall())
    assert 'RequestAttributesSequence' not in a
    for campo in ('StudyInstanceUID','SeriesInstanceUID','SOPInstanceUID'):assert getattr(ds,campo)!=getattr(a,campo)
    assert a.file_meta.MediaStorageSOPInstanceUID==a.SOPInstanceUID
    assert b'SECRETO' not in anon.read_bytes()
    assert dicom.metadatos(r,anon)['PatientIdentityRemoved']=='YES'
    assert s.listar_auditoria(sesion,tabla='DICOM',accion='E')
    with pytest.raises(ErrorValidacion):dicom.anonimizar(r,anon,anon)
    with pytest.raises(FileExistsError):dicom.convertir(r,imagen,anon)


@pytest.mark.parametrize('rol',['medico','enfermero','administrativo'])
def test_permisos_de_modulos_nuevos(entorno,tmp_path,rol):
    s,sesion,r=entorno
    s.guardar_usuario(sesion,dict(usuario='prueba',nombre_completo='Prueba',password='ClaveTest123',rol=rol))
    otro=s.repositorio(s.autenticar('prueba','ClaveTest123'))
    with pytest.raises(AccesoDenegado):fhir.exportar(otro,1,tmp_path/'prohibido.json')
    if rol=='administrativo':
        with pytest.raises(AccesoDenegado):intervenciones.consultar(otro,1)
        with pytest.raises(AccesoDenegado):dicom.metadatos(otro,'no-existe.dcm')
    else:assert intervenciones.consultar(otro,1)


def test_gui_flujo_de_los_tres_modulos(entorno,raiz_tk,tmp_path):
    s,sesion,r=entorno
    app=IntervencionesApp(raiz_tk,r);assert app.consultar()['paciente']
    app.cuerpo.destroy();app=FHIRApp(raiz_tk,r)
    app.codigo.set('GUI');app.descripcion.set('Práctica GUI sintética');app.registrar_practica()
    bundle=app.exportar('json',tmp_path/'gui.json');assert bundle['resourceType']=='Bundle'
    assert app.importar(tmp_path/'gui.json')['creados']
    app.cuerpo.destroy();app=DICOMApp(raiz_tk,r)
    imagen=tmp_path/'gui.png';Image.new('L',(16,16),90).save(imagen)
    app.imagen.set(str(imagen));app.convertir(tmp_path/'gui.dcm');app.anonimizar(tmp_path/'gui_anon.dcm')
    assert app.ver_metadatos()['PatientName']=='ANONIMO'


def test_migracion_repetible_y_preserva_relaciones(entorno):
    s,sesion,r=entorno
    antes=r.listar_prescripciones(activos=None)
    for _ in range(2):Seguridad(s._repo.ruta)
    assert r.listar_prescripciones(activos=None)==antes
    with s._repo.conectar() as c:
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]


def test_tipo_invalido_dosis_rollback_y_exportacion_sin_sobrescritura(entorno,tmp_path):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    med=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='MedicationRequest')
    med['dosageInstruction']=[]
    with s._repo.conectar() as c: antes=c.execute('SELECT COUNT(*) FROM RecursosFHIR').fetchone()[0]
    with pytest.raises(ErrorValidacion):fhir.importar(r,guardar(bundle,tmp_path),'Externo')
    with s._repo.conectar() as c: assert c.execute('SELECT COUNT(*) FROM RecursosFHIR').fetchone()[0]==antes
    with pytest.raises(FileExistsError):fhir.exportar(r,r.listar_pacientes()[0]['id'],tmp_path/'salida.json')


def test_fallo_auditoria_revierte_intercambio_y_retira_exportaciones(entorno,tmp_path):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    with s._repo.conectar() as c:
        c.execute("CREATE TRIGGER fallo_e9 BEFORE INSERT ON Auditoria WHEN NEW.tipo_accion IN ('I','E','Q') BEGIN SELECT RAISE(ABORT,'fallo simulado'); END")
        antes=c.execute('SELECT COUNT(*) FROM Practicas').fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):fhir.importar(r,guardar(bundle,tmp_path),'Externo')
    with s._repo.conectar() as c: assert c.execute('SELECT COUNT(*) FROM Practicas').fetchone()[0]==antes
    with pytest.raises(sqlite3.IntegrityError):fhir.exportar(r,r.listar_pacientes()[0]['id'],tmp_path/'fallo.json')
    assert not (tmp_path/'fallo.json').exists()
    with pytest.raises(sqlite3.IntegrityError):intervenciones.consultar(r,r.listar_pacientes()[0]['id'])
