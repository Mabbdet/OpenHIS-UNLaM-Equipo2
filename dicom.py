"""Secondary Capture y anonimización básica de imágenes sintéticas de un cuadro."""

from io import BytesIO
from pathlib import Path
from datetime import date, datetime
import hashlib

from PIL import Image, ImageOps
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid
from datos import ErrorValidacion

AVISO = ('Anonimización básica de metadatos. Revise texto identificatorio incrustado en los píxeles. '
         'Los campos 01/01 representan solo el año, no la fecha real. Secondary Capture no sustituye una adquisición diagnóstica.')
TECNICOS = ('Rows','Columns','SamplesPerPixel','PhotometricInterpretation','BitsAllocated','BitsStored',
            'HighBit','PixelRepresentation','PlanarConfiguration','PixelData')


def _anio(valor):
    v=str(valor or '')
    if not v: return ''
    if len(v)!=4 or not v.isascii() or not v.isdigit() or not 1 <= int(v) <= date.today().year:
        raise ErrorValidacion('El año debe tener cuatro dígitos y no ser futuro.')
    return v


def _nuevo():
    meta=FileMetaDataset()
    meta.MediaStorageSOPClassUID=SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID=generate_uid()
    meta.TransferSyntaxUID=ExplicitVRLittleEndian
    meta.ImplementationClassUID=pydicom.uid.PYDICOM_IMPLEMENTATION_UID
    ds=FileDataset(None,{},file_meta=meta,preamble=b'\0'*128)
    ds.SOPClassUID=meta.MediaStorageSOPClassUID;ds.SOPInstanceUID=meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID=generate_uid();ds.SeriesInstanceUID=generate_uid()
    ds.Modality='OT';ds.ConversionType='WSD';ds.ImageType=['DERIVED','SECONDARY']
    ds.PatientName='ANONIMO';ds.PatientID='ANONIMO';ds.PatientBirthDate='';ds.PatientSex=''
    ds.PatientIdentityRemoved='YES';ds.DeidentificationMethod='OpenHIS: lista permitida de metadatos; revisar pixeles'
    ds.StudyDate='';ds.StudyTime='';ds.AccessionNumber='';ds.StudyID='';ds.SeriesNumber='1';ds.InstanceNumber='1'
    ds.ReferringPhysicianName='';ds.Manufacturer='OpenHIS-UNLaM'
    return ds


def _guardar(repo, ds, destino, descripcion):
    from seguridad import _auditar
    repo.autorizar('DICOM')
    path=Path(destino);path.parent.mkdir(parents=True,exist_ok=True)
    memoria=BytesIO();ds.save_as(memoria,enforce_file_format=True)
    archivo=path.open('xb')
    try:
        with archivo: archivo.write(memoria.getvalue())
        s=repo._servicio
        with s._repo.conectar() as c:
            actor=s._actor(c,repo._sesion,'DICOM')
            _auditar(c,actor,'DICOM',None,'E',nuevo={'operacion':descripcion,'SOPInstanceUID':str(ds.SOPInstanceUID)},referencia=path)
    except Exception:
        path.unlink(missing_ok=True);raise
    return path


def convertir(repo, origen, destino, nacimiento='', estudio='', sexo='', *, metadatos=None):
    repo.autorizar('DICOM')
    nacimiento,estudio=_anio(nacimiento),_anio(estudio)
    if sexo not in ('','M','F','O'): raise ErrorValidacion('Sexo DICOM no válido.')
    p=Path(origen)
    if p.resolve()==Path(destino).resolve(): raise ErrorValidacion('Conserve el archivo original.')
    with Image.open(p) as imagen:
        if imagen.format not in ('PNG','JPEG') or imagen.width*imagen.height>40_000_000:
            raise ErrorValidacion('Use una imagen JPG/PNG de hasta 40 millones de píxeles.')
        imagen=ImageOps.exif_transpose(imagen).convert('L')
        datos=imagen.tobytes();ancho,alto=imagen.size
    ds=_nuevo()
    ds.Rows=alto;ds.Columns=ancho;ds.SamplesPerPixel=1;ds.PhotometricInterpretation='MONOCHROME2'
    ds.BitsAllocated=8;ds.BitsStored=8;ds.HighBit=7;ds.PixelRepresentation=0
    ds.PixelData=datos+(b'\0' if len(datos)%2 else b'')
    ds.PatientBirthDate=nacimiento+'0101' if nacimiento else ''
    ds.StudyDate=estudio+'0101' if estudio else '';ds.PatientSex=sexo
    if metadatos is not None:
        campos={'patient_name':'PatientName','patient_id':'PatientID','study_description':'StudyDescription',
                'series_description':'SeriesDescription','study_id':'StudyID','accession_number':'AccessionNumber',
                'referring_physician':'ReferringPhysicianName','performing_physician':'PerformingPhysicianName',
                'institution':'InstitutionName','institution_address':'InstitutionAddress','modality':'Modality'}
        for clave,atributo in campos.items():
            valor=str(metadatos.get(clave) or '').strip()
            if valor:
                maximo=1024 if clave=='institution_address' else 16 if clave in ('study_id','accession_number','modality') else 64
                if len(valor)>maximo:raise ErrorValidacion(f'{clave}: máximo {maximo} caracteres.')
                setattr(ds,atributo,valor)
        for clave,atributo in [('birth_date','PatientBirthDate'),('study_date','StudyDate')]:
            valor=str(metadatos.get(clave) or '').strip()
            if valor:
                try:parsed=date.fromisoformat(valor)
                except ValueError:raise ErrorValidacion('Use fechas completas AAAA-MM-DD.') from None
                if parsed.isoformat()!=valor or (clave=='birth_date' and parsed>date.today()):
                    raise ErrorValidacion('Fecha de nacimiento inválida o futura.')
                setattr(ds,atributo,parsed.strftime('%Y%m%d'))
        hora=str(metadatos.get('study_time') or '').strip()
        if hora:
            try:ds.StudyTime=datetime.strptime(hora,'%H:%M').strftime('%H%M%S')
            except ValueError:raise ErrorValidacion('Use hora HH:MM.') from None
        sexo_meta=str(metadatos.get('sex') or '')
        if sexo_meta not in ('','M','F','O'):raise ErrorValidacion('Sexo DICOM no válido.')
        ds.PatientSex=sexo_meta
        ds.PatientIdentityRemoved='NO'
        if 'DeidentificationMethod' in ds:del ds.DeidentificationMethod
    return _guardar(repo,ds,destino,'Conversión JPG/PNG a Secondary Capture')


def anonimizar(repo, origen, destino):
    repo.autorizar('DICOM')
    if Path(origen).resolve()==Path(destino).resolve(): raise ErrorValidacion('La salida debe ser distinta del original.')
    original=pydicom.dcmread(origen)
    if original.file_meta.TransferSyntaxUID.is_compressed or int(getattr(original,'NumberOfFrames',1))!=1:
        raise ErrorValidacion('Esta práctica admite un cuadro con transferencia sin compresión.')
    if not all(k in original for k in ('Rows','Columns','PixelData','BitsAllocated','BitsStored','HighBit','PixelRepresentation','SamplesPerPixel','PhotometricInterpretation')):
        raise ErrorValidacion('Faltan los atributos técnicos de píxeles.')
    # Reconstrucción por lista permitida: excluye nombres, privados, texto libre,
    # overlays y secuencias con posibles identificadores o referencias originales.
    ds=_nuevo()
    for k in TECNICOS:
        if k in original: ds.add(original.data_element(k))
    ds.file_meta.TransferSyntaxUID=original.file_meta.TransferSyntaxUID
    for campo in ('PatientBirthDate','StudyDate'):
        valor=str(getattr(original,campo,'') or '')
        if campo=='StudyDate' and not valor:
            valor=str(getattr(original,'AcquisitionDate','') or getattr(original,'SeriesDate','') or '')
        ds.data_element(campo).value=_anio(valor[:4])+'0101' if valor else ''
    sexo=str(getattr(original,'PatientSex',''))
    ds.PatientSex=sexo if sexo in ('M','F','O') else ''
    return _guardar(repo,ds,destino,'Anonimización básica; UID regenerados; secuencias y privados excluidos')


def metadatos(repo, ruta):
    from seguridad import _auditar
    repo.autorizar('DICOM')
    ds=pydicom.dcmread(ruta,stop_before_pixels=True)
    resultado={e.keyword or str(e.tag):str(e.value) for e in ds if e.VR!='SQ'}
    with repo._servicio._repo.conectar() as c:
        actor=repo._servicio._actor(c,repo._sesion,'DICOM')
        _auditar(c,actor,'DICOM',None,'Q',nuevo={'consulta_metadatos':True},referencia=ruta)
    return resultado
