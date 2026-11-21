"""Visor académico sin NumPy: metadatos completos y preview no diagnóstica."""

from array import array
import sys
from pathlib import Path
from PIL import Image, ImageOps
import pydicom
from datos import ErrorValidacion


def metadatos_completos(ds):
    lineas=['[FILE META INFORMATION]']
    def recorrer(dataset,nivel=0):
        for e in dataset:
            cabecera=f"{'  '*nivel}{e.tag} {e.keyword or e.name} [{e.VR}]"
            if e.VR=='SQ':
                lineas.append(cabecera+f' — {len(e.value)} elemento(s)')
                for i,item in enumerate(e.value,1):
                    lineas.append('  '*(nivel+1)+f'Elemento {i}')
                    recorrer(item,nivel+2)
            else:
                v=f'<{len(e.value)} bytes>' if isinstance(e.value,bytes) else str(e.value).replace('\n',' ')
                lineas.append(cabecera+' = '+(v[:500]+'… [abreviado]' if len(v)>500 else v))
    recorrer(ds.file_meta)
    lineas.append('\n[DATASET / METADATOS]');recorrer(ds)
    return '\n'.join(lineas)


def decodificar(ds):
    syntax=ds.file_meta.TransferSyntaxUID
    if syntax.is_compressed:raise ErrorValidacion('Imagen comprimida: metadatos disponibles; se requiere un decodificador compatible.')
    if int(getattr(ds,'NumberOfFrames',1))!=1:raise ErrorValidacion('La vista previa básica admite un cuadro.')
    filas,columnas=int(ds.Rows),int(ds.Columns)
    if filas<=0 or columnas<=0 or filas*columnas>16_000_000:
        raise ErrorValidacion('Dimensiones de imagen fuera del límite del visor (16 millones de píxeles).')
    bits=int(ds.BitsAllocated);muestras=int(ds.SamplesPerPixel);photo=str(ds.PhotometricInterpretation)
    raw=ds.PixelData;cantidad=filas*columnas
    if bits not in (8,16) or muestras not in (1,3):raise ErrorValidacion('Representación de píxeles no soportada por el visor básico.')
    esperado=cantidad*muestras*(bits//8)
    if len(raw)<esperado:raise ErrorValidacion('PixelData incompleto.')
    if muestras==3:
        if bits!=8 or photo!='RGB':raise ErrorValidacion('Solo se admite RGB de 8 bits.')
        plano=int(getattr(ds,'PlanarConfiguration',0))
        if plano not in (0,1):raise ErrorValidacion('PlanarConfiguration no válida.')
        if plano==1:
            raw=bytes(v for rgb in zip(raw[:cantidad],raw[cantidad:2*cantidad],raw[2*cantidad:3*cantidad]) for v in rgb)
        return Image.frombytes('RGB',(columnas,filas),raw[:3*cantidad])
    if photo not in ('MONOCHROME1','MONOCHROME2'):raise ErrorValidacion('Interpretación fotométrica no soportada.')
    almacenados=int(ds.BitsStored);alto=int(ds.HighBit)
    if not 1<=almacenados<=bits or not almacenados-1<=alto<bits:raise ErrorValidacion('BitsStored/HighBit incompatibles.')
    valores=array('B' if bits==8 else 'H');valores.frombytes(raw[:esperado])
    if bits==16 and syntax.is_little_endian!=(sys.byteorder=='little'):valores.byteswap()
    mascara=(1<<almacenados)-1;desplazamiento=alto+1-almacenados
    firmado=int(ds.PixelRepresentation)
    if firmado not in (0,1):raise ErrorValidacion('PixelRepresentation no válida.')
    def numero(v):
        v=(v>>desplazamiento)&mascara
        return v-(1<<almacenados) if firmado and v&(1<<(almacenados-1)) else v
    valores=array('i',(numero(v) for v in valores))
    bajo,alto_val=min(valores),max(valores)
    # Los niveles se ajustan para inspección, sin modificar los datos DICOM.
    if bits==8 and almacenados==8 and not firmado:
        escalados=bytes(v for v in valores)
    elif bajo==alto_val:escalados=bytes(cantidad)
    else:escalados=bytes(round((v-bajo)*255/(alto_val-bajo)) for v in valores)
    im=Image.frombytes('L',(columnas,filas),escalados)
    return ImageOps.invert(im) if photo=='MONOCHROME1' else im


def visualizar(repo,ruta):
    from seguridad import _auditar
    repo.autorizar('DICOM')
    try:ds=pydicom.dcmread(ruta)
    except pydicom.errors.InvalidDicomError as error:
        raise ErrorValidacion('El archivo no es un DICOM válido.') from error
    texto=metadatos_completos(ds)
    try:
        imagen=decodificar(ds)
        aviso=f'{imagen.width} × {imagen.height} · {ds.PhotometricInterpretation} · {ds.BitsAllocated} bits. Vista no diagnóstica.'
    except (ValueError,KeyError,AttributeError,TypeError) as error:
        imagen=None;aviso=str(error)
    s=repo._servicio
    with s._repo.conectar() as c:
        actor=s._actor(c,repo._sesion,'DICOM')
        _auditar(c,actor,'DICOM',None,'Q',nuevo={'visualizacion_dicom':True,'imagen_previsualizada':imagen is not None},referencia=Path(ruta))
    return dict(metadatos=texto,imagen=imagen,aviso=aviso)
