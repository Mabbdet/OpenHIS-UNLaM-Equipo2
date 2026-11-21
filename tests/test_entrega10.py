from array import array
import copy
import hashlib
import json
import sqlite3
import struct

from PIL import Image
import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.uid import ExplicitVRLittleEndian, ExplicitVRBigEndian, JPEGBaseline8Bit
import pytest

from datos import ErrorValidacion
from seguridad import AccesoDenegado
from tests.test_entrega9 import entorno, crear_bundle, guardar
from entrega10_app import FHIRConfirmApp, DICOMVisorApp
import fhir
import dicom
import dicom_visor


def datos_base(s):
    with s._repo.conectar() as c:
        return {t:[tuple(r) for r in c.execute('SELECT * FROM '+t+' ORDER BY rowid')]
                for t in ('Pacientes','Profesionales','Prescripciones','SignosVitales','Practicas','RecursosFHIR','Farmacos','Auditoria','sqlite_sequence')}


def solo_observaciones(bundle):
    originales=[copy.deepcopy(e) for e in bundle['entry'] if e['resource']['resourceType'] in ('Patient','Practitioner')]
    rx=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='MedicationRequest')
    for i,(codigo,valor,unidad) in enumerate([('8480-6',121,'mm[Hg]'),('8462-4',81,'mm[Hg]'),('8867-4',75,'/min'),('8310-5',36.7,'Cel')]):
        originales.append({'resource':{'resourceType':'Observation','id':f'e10-{i}', 'status':'final',
            'subject':rx['subject'],'performer':[rx['requester']],'effectiveDateTime':'2026-11-01T12:00:00Z',
            'code':{'coding':[{'system':'http://loinc.org','code':codigo}]},
            'valueQuantity':{'value':valor,'unit':unidad}}})
    return {**bundle,'entry':originales}


def test_preanalisis_no_escribe_y_confirmacion_atomica(entorno,tmp_path):
    s,sesion,r=entorno
    bundle=solo_observaciones(crear_bundle(r,tmp_path));p=guardar(bundle,tmp_path)
    antes=datos_base(s)
    plan=fhir.preparar_importacion(r,p,'Centro de prueba')
    assert datos_base(s)==antes
    assert plan.resumen['creados']['SignosVitales']==1
    assert plan.resumen['acciones'][0]['tabla']=='SignosVitales'
    assert json.loads(plan.contenido_json)['resourceType']=='Bundle'
    assert fhir.confirmar_importacion(r,plan,confirmado=False) is None
    assert datos_base(s)==antes
    resultado=fhir.confirmar_importacion(r,plan,confirmado=True)
    assert resultado['creados']['SignosVitales']==1
    filas=[f for f in r.listar_signos(activos=None) if f['fecha_hora']=='2026-11-01T12:00:00Z']
    assert len(filas)==1 and filas[0]['presion_sistolica']==121 and filas[0]['presion_diastolica']==81
    assert filas[0]['frecuencia_cardiaca']==75 and filas[0]['temperatura']==36.7
    with s._repo.conectar() as c:
        ids={f[0] for f in c.execute("SELECT registro_id FROM RecursosFHIR WHERE origen=?",('Centro de prueba',))}
        assert ids=={filas[0]['id']}


@pytest.mark.parametrize('cambio',['archivo','base','permiso'])
def test_plan_obsoleto_bloquea_confirmacion(entorno,tmp_path,cambio):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path);p=guardar(bundle,tmp_path)
    plan=fhir.preparar_importacion(r,p,'Centro')
    if cambio=='archivo':p.write_text(p.read_text(encoding='utf-8')+' ',encoding='utf-8')
    elif cambio=='base':r.guardar_catalogo('especialidades',{'codigo':'POST-PLAN','nombre':'Posterior al análisis'})
    else:
        i=s.guardar_usuario(sesion,dict(usuario='admin2',password='AdminTest123',nombre_completo='Otro admin',rol='admin'))
        actor=s.autorizar(sesion)
        s.guardar_usuario(sesion,{**actor,'rol':'medico'},actor['id'])
    antes=datos_base(s)
    with pytest.raises(ErrorValidacion):fhir.confirmar_importacion(r,plan,confirmado=True)
    assert datos_base(s)==antes


def test_conflictos_observations_y_dosis_se_bloquean_en_analisis(entorno,tmp_path):
    s,sesion,r=entorno;bundle=solo_observaciones(crear_bundle(r,tmp_path))
    copia=copy.deepcopy(bundle['entry'][-1]);copia['resource']['id']='otro';copia['resource']['valueQuantity']['value']=39.5
    bundle['entry'].append(copia);antes=datos_base(s)
    with pytest.raises(ErrorValidacion,match='contradictorios'):fhir.preparar_importacion(r,guardar(bundle,tmp_path),'Centro')
    assert datos_base(s)==antes


def test_preanalisis_referencias_rotas_y_dosis_ausente(entorno,tmp_path):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    rx=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='MedicationRequest')
    rx['dosageInstruction']=[{}]
    antes=datos_base(s)
    with pytest.raises(ErrorValidacion,match='dosis'):fhir.preparar_importacion(r,guardar(bundle,tmp_path),'Centro')
    assert datos_base(s)==antes
    rx['subject']['reference']='Patient/no-existe'
    with pytest.raises(ErrorValidacion,match='referencias'):fhir.preparar_importacion(r,guardar(bundle,tmp_path),'Centro')


def test_farmacos_existentes_y_dosis_estructurada(entorno,tmp_path):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path)
    rx=next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='MedicationRequest')
    rx['dosageInstruction']=[{'doseAndRate':[{'doseQuantity':{'value':2,'unit':'mg'}}],
        'route':{'coding':[{'display':'Oral'}]},'timing':{'repeat':{'frequency':1,'period':8,'periodUnit':'h'}}}]
    antes=len(r.listar_catalogo('farmacos'))
    resultado=fhir.importar(r,guardar(bundle,tmp_path),'Centro')
    assert len(r.listar_catalogo('farmacos'))==antes
    fila=max(r.listar_prescripciones(activos=None),key=lambda f:f['id'])
    assert fila['dosis']=='2 mg' and fila['via_administracion']=='Oral' and fila['frecuencia']=='1 veces cada 8 h'


def dataset_pixeles(bits=8,samples=1,photo='MONOCHROME2',valores=None,firmado=0,stored=None,endian='<',planar=0):
    ds=dicom._nuevo();ds.Rows=1;ds.Columns=2;ds.SamplesPerPixel=samples;ds.PhotometricInterpretation=photo
    ds.BitsAllocated=bits;ds.BitsStored=stored or bits;ds.HighBit=ds.BitsStored-1;ds.PixelRepresentation=firmado
    ds.file_meta.TransferSyntaxUID=ExplicitVRLittleEndian if endian=='<' else ExplicitVRBigEndian
    valores=valores or [0,255]
    ds.PixelData=struct.pack(endian+('B' if bits==8 else 'H')*len(valores),*valores)
    if samples==3:ds.PlanarConfiguration=planar
    return ds


@pytest.mark.parametrize('bits,photo,valores,firmado,stored,endian,esperado',[
    (8,'MONOCHROME2',[0,255],0,8,'<',[0,255]),
    (8,'MONOCHROME1',[0,255],0,8,'<',[255,0]),
    (16,'MONOCHROME2',[0,65535],0,16,'<',[0,255]),
    (16,'MONOCHROME2',[0,65535],0,16,'>',[0,255]),
    (16,'MONOCHROME2',[0xF800,0x07FF],1,12,'<',[0,255]),
    (16,'MONOCHROME2',[120,120],0,16,'<',[0,0]),
])
def test_visor_grises_8_16_y_signed(bits,photo,valores,firmado,stored,endian,esperado):
    ds=dataset_pixeles(bits=bits,photo=photo,valores=valores,firmado=firmado,stored=stored,endian=endian)
    imagen=dicom_visor.decodificar(ds)
    assert [imagen.getpixel((x,0)) for x in range(2)]==esperado


@pytest.mark.parametrize('planar,valores',[(0,[255,0,0,0,255,0]),(1,[255,0,0,255,0,0])])
def test_visor_rgb(planar,valores):
    ds=dataset_pixeles(samples=3,photo='RGB',valores=valores,planar=planar)
    imagen=dicom_visor.decodificar(ds)
    assert [imagen.getpixel((x,0)) for x in range(2)]==[(255,0,0),(0,255,0)]


@pytest.mark.parametrize('caso',['comprimido','sin_pixeles','incompleto','fotometria'])
def test_metadatos_disponibles_sin_imagen(entorno,tmp_path,caso):
    s,sesion,r=entorno;ds=dataset_pixeles()
    hijo=Dataset();hijo.PatientName='NOMBRE^FICTICIO';ds.RequestAttributesSequence=Sequence([hijo])
    ds.PatientComments='x'*550
    if caso=='comprimido':
        from pydicom.encaps import encapsulate
        ds.file_meta.TransferSyntaxUID=JPEGBaseline8Bit;ds.PixelData=encapsulate([b'no es una imagen real'])
    elif caso=='sin_pixeles':del ds.PixelData
    elif caso=='incompleto':ds.Rows=100
    else:ds.PhotometricInterpretation='PALETTE COLOR'
    p=tmp_path/'caso.dcm';ds.save_as(p,enforce_file_format=True);antes=p.read_bytes()
    vista=dicom_visor.visualizar(r,p)
    assert vista['imagen'] is None
    assert 'FILE META INFORMATION' in vista['metadatos'] and 'RequestAttributesSequence' in vista['metadatos']
    assert 'NOMBRE^FICTICIO' in vista['metadatos'] and '[abreviado]' in vista['metadatos']
    assert p.read_bytes()==antes
    logs=s.listar_auditoria(sesion,tabla='DICOM',accion='Q')
    assert json.loads(logs[0]['datos_nuevos'])['imagen_previsualizada'] is False


def test_conversion_vinculada_a_paciente_y_anonimizacion(entorno,tmp_path,raiz_tk):
    s,sesion,r=entorno;app=DICOMVisorApp(raiz_tk,r)
    assert len(app.libro.tabs())==3
    app.selector_paciente.current(1);app.cargar_paciente();app.selector_profesional.current(1);app.cargar_profesional()
    im=tmp_path/'imagen.png';Image.new('L',(32,16),88).save(im);app.imagen.set(str(im))
    app.campos['study_date'].set('2026-10-20');app.campos['study_time'].set('13:45')
    ruta=app.convertir(tmp_path/'vinculado.dcm');ds=pydicom.dcmread(ruta)
    assert ds.PatientID==app.pacientes[0]['dni'] and ds.PatientIdentityRemoved=='NO'
    assert ds.ReferringPhysicianName and ds.StudyDate=='20261020' and ds.StudyTime=='134500'
    assert app.imagen_tk is not None and app.libro.select()==str(app.visor)
    original=ruta.read_bytes();anon=app.anonimizar(tmp_path/'anonimo.dcm')
    assert ruta.read_bytes()==original and pydicom.dcmread(anon).PatientID=='ANONIMO'


def test_gui_analiza_cancela_y_confirma(entorno,tmp_path,raiz_tk,monkeypatch):
    s,sesion,r=entorno;bundle=crear_bundle(r,tmp_path);p=guardar(bundle,tmp_path)
    app=FHIRConfirmApp(raiz_tk,r);antes=datos_base(s)
    plan=app.analizar(p)
    assert datos_base(s)==antes and app.plan is plan and str(app.boton_confirmar['state'])=='normal'
    monkeypatch.setattr('tkinter.messagebox.askyesno',lambda *a,**k:False)
    assert app.confirmar() is None and datos_base(s)==antes
    monkeypatch.setattr('tkinter.messagebox.askyesno',lambda *a,**k:True)
    assert app.confirmar()['creados']
    assert app.plan is None and str(app.boton_confirmar['state'])=='disabled'
    app.analizar(p);app.origen.set('Otro origen')
    assert app.plan is None
