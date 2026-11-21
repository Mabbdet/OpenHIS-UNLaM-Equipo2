"""Subconjunto FHIR R4 para el intercambio académico local en JSON y XML.

Valida el contrato soportado, referencias y datos antes de persistir. No es un
validador de todos los perfiles FHIR ni un cliente de servidores remotos.
"""

from datetime import date, datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from uuid import uuid4
import xml.etree.ElementTree as ET

from defusedxml.ElementTree import fromstring
from defusedxml.common import DefusedXmlException
from datos import ErrorValidacion, validar_dni

NS = 'http://hl7.org/fhir'
LOINC = {'8480-6': ('presion_sistolica', 'mm[Hg]'), '8462-4': ('presion_diastolica', 'mm[Hg]'),
         '8867-4': ('frecuencia_cardiaca', '/min'), '8310-5': ('temperatura', 'Cel'),
         '59408-5': ('saturacion_oxigeno', '%')}
TIPOS = {'Patient', 'Practitioner', 'ServiceRequest', 'MedicationRequest', 'Observation'}
REPETIDOS = {'entry', 'identifier', 'name', 'given', 'qualification', 'coding', 'dosageInstruction',
             'note', 'performer', 'component', 'category', 'doseAndRate', 'reasonCode'}
ORDEN_MEDICATION = ['id','identifier','status','statusReason','intent','category','priority',
    'medicationCodeableConcept','subject','encounter','authoredOn','requester','performer','recorder',
    'reasonCode','reasonReference','note','dosageInstruction','dispenseRequest']


def fecha(valor):
    texto = str(valor or '').strip()
    try:
        if len(texto) == 10:
            return date.fromisoformat(texto).isoformat()
        dt = datetime.fromisoformat(texto.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)  # SQLite local conserva UTC.
        return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    except ValueError:
        raise ErrorValidacion('Fecha FHIR ausente o inválida.') from None


def _xml(recurso):
    def nodo(nombre, valor):
        e = ET.Element('{'+NS+'}'+nombre)
        if isinstance(valor, dict):
            items=list(valor.items())
            if valor.get('resourceType')=='MedicationRequest':
                items.sort(key=lambda kv:ORDEN_MEDICATION.index(kv[0]) if kv[0] in ORDEN_MEDICATION else -1)
            for k, v in items:
                if k == 'resourceType':
                    continue
                for item in v if isinstance(v, list) else [v]:
                    if item is None or item == '':
                        continue
                    child = nodo(item['resourceType'], item) if k == 'resource' else nodo(k, item)
                    if k == 'resource':
                        wrapper = ET.SubElement(e, '{'+NS+'}resource'); wrapper.append(child)
                    else:
                        e.append(child)
        else:
            e.set('value', str(valor).lower() if isinstance(valor, bool) else str(valor))
        return e
    ET.register_namespace('', NS)
    root = nodo(recurso['resourceType'], recurso)
    ET.indent(root)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')


def leer(archivo):
    p = Path(archivo)
    if p.stat().st_size > 5_000_000:
        raise ErrorValidacion('El intercambio supera el límite de 5 MB.')
    try:
        if p.suffix.lower() == '.json':
            def sin_duplicados(pares):
                d = {}
                for k, v in pares:
                    if k in d:
                        raise ValueError('Clave JSON repetida')
                    d[k] = v
                return d
            datos = json.loads(p.read_text(encoding='utf-8-sig'), object_pairs_hook=sin_duplicados,
                               parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        elif p.suffix.lower() == '.xml':
            root = fromstring(p.read_bytes(), forbid_dtd=True)
            def convertir(e,padre=''):
                if not e.tag.startswith('{'+NS+'}'):
                    raise ValueError('Namespace ajeno a FHIR')
                if 'value' in e.attrib:
                    v = e.attrib['value']
                    if (e.tag.endswith('}value') and padre in ('valueQuantity','quantity','doseQuantity')) or e.tag.endswith('}frequency') or e.tag.endswith('}period'):
                        return float(v) if '.' in v else int(v)
                    return v == 'true' if e.tag.endswith('}active') and v in ('true','false') else v
                d = {}
                for child in e:
                    k = child.tag.split('}')[-1]
                    if k == 'resource':
                        if len(child) != 1: raise ValueError('resource XML inválido')
                        value = convertir(child[0]); value['resourceType'] = child[0].tag.split('}')[-1]
                    else:
                        value = convertir(child,e.tag.split('}')[-1])
                    if k in REPETIDOS and not (k=='identifier' and e.tag=='{'+NS+'}Bundle'):
                        d.setdefault(k, []).append(value)
                    elif k in d:
                        raise ValueError('Elemento XML repetido')
                    else:
                        d[k] = value
                return d
            datos = convertir(root); datos['resourceType'] = root.tag.split('}')[-1]
        else:
            raise ValueError('Use un archivo .json o .xml')
        validar(datos)
        return datos
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError, ET.ParseError, DefusedXmlException) as error:
        raise ErrorValidacion(f'Intercambio FHIR inválido: {error}') from error


def validar(bundle):
    if not isinstance(bundle, dict) or bundle.get('resourceType') != 'Bundle' or bundle.get('type') != 'collection':
        raise ErrorValidacion('Se requiere un Bundle FHIR de tipo collection.')
    entries = bundle.get('entry')
    if not isinstance(entries, list) or not 1 <= len(entries) <= 1000:
        raise ErrorValidacion('El Bundle debe tener entre 1 y 1000 entradas.')
    mapa = {}
    for e in entries:
        if not isinstance(e,dict) or not isinstance(e.get('resource'),dict):
            raise ErrorValidacion('Cada entrada debe contener un recurso.')
        r = e.get('resource', {})
        t, i = r.get('resourceType'), r.get('id')
        if t not in TIPOS or not isinstance(i, str) or not re.fullmatch(r'[A-Za-z0-9\-.]{1,64}', i):
            raise ErrorValidacion('Tipo de recurso o identificador no soportado.')
        claves = {t+'/'+i}
        if e.get('fullUrl'): claves.add(e['fullUrl'])
        for clave in claves:
            if clave in mapa: raise ErrorValidacion('Referencia o identificador repetido en el Bundle.')
            mapa[clave] = r
    for e in entries:
        r = e['resource']; t = r['resourceType']
        if t in ('Patient','Practitioner'):
            ids = r.get('identifier', [])
            if not ids or not ids[0].get('value'):
                raise ErrorValidacion('Falta DNI en identifier.value.')
            validar_dni(ids[0]['value'])
            if not r.get('name') or not r['name'][0].get('family') or not r['name'][0].get('given'):
                raise ErrorValidacion('Falta nombre o apellido del recurso.')
            if t == 'Patient' or r.get('birthDate'):
                nacimiento=str(r.get('birthDate') or '')
                try:
                    if date.fromisoformat(nacimiento).isoformat()!=nacimiento or date.fromisoformat(nacimiento)>date.today():
                        raise ValueError
                except ValueError:
                    raise ErrorValidacion('birthDate debe ser una fecha completa válida y no futura.') from None
            if not isinstance(r.get('active',True),bool):
                raise ErrorValidacion('active debe ser booleano.')
            if r.get('gender','unknown') not in ('male','female','other','unknown'):
                raise ErrorValidacion('Género FHIR no válido.')
        else:
            paciente = mapa.get(r.get('subject', {}).get('reference'))
            ref_prof = r.get('requester', {}).get('reference') or next(iter(r.get('performer', [])), {}).get('reference')
            profesional = mapa.get(ref_prof)
            if not paciente or paciente['resourceType'] != 'Patient' or not profesional or profesional['resourceType'] != 'Practitioner':
                raise ErrorValidacion('Las referencias deben resolver a Patient y Practitioner incluidos en el Bundle.')
            fecha(r.get('effectiveDateTime') if t == 'Observation' else r.get('authoredOn'))
            if t == 'Observation':
                if r.get('status') not in ('final','amended','corrected','entered-in-error','preliminary'):
                    raise ErrorValidacion('Estado de Observation no soportado.')
                coding = r.get('code', {}).get('coding', [{}])[0]
                q = r.get('valueQuantity', {})
                if coding.get('system') != 'http://loinc.org' or coding.get('code') not in LOINC:
                    raise ErrorValidacion('Observation requiere un código LOINC de signos vitales soportado.')
                valor = q.get('value')
                if isinstance(valor, bool) or not isinstance(valor,(int,float)) or not math.isfinite(valor):
                    raise ErrorValidacion('Observation requiere una medición numérica finita.')
                campo, unidad = LOINC[coding['code']]
                if q.get('system','http://unitsofmeasure.org') != 'http://unitsofmeasure.org' or q.get('code', q.get('unit')) != unidad or (campo != 'temperatura' and valor != int(valor)):
                    raise ErrorValidacion('Unidad o precisión incompatible con el signo vital local.')
            elif r.get('status') not in ({'active','completed','revoked','draft','unknown','entered-in-error','on-hold'} if t=='ServiceRequest' else {'active','completed','cancelled','stopped','draft','unknown','entered-in-error','on-hold'}):
                raise ErrorValidacion('Estado de solicitud no soportado.')
            elif r.get('intent') not in ('order','original-order','reflex-order','filler-order','instance-order','proposal','plan','option'):
                raise ErrorValidacion('La solicitud requiere un intent soportado.')
            if t=='MedicationRequest':
                cantidad=r.get('dispenseRequest',{}).get('quantity',{}).get('value')
                if cantidad is not None and (isinstance(cantidad,bool) or not isinstance(cantidad,(int,float)) or not math.isfinite(cantidad) or cantidad<=0 or cantidad!=int(cantidad)):
                    raise ErrorValidacion('La cantidad recibida debe ser un entero positivo para el modelo local.')
    return mapa


def _persona(f, tipo):
    d = {'resourceType': tipo, 'id': ('p-' if tipo=='Patient' else 'pr-')+str(f['id']),
         'identifier': [{'system':'urn:openhis:dni','value':f['dni']}], 'active':bool(f['activo']),
         'name':[{'family':f['apellido'],'given':[f['nombre']]}],
         'gender':{'M':'male','F':'female','O':'other'}.get(f['sexo'],'unknown')}
    if f['fecha_nacimiento']: d['birthDate'] = f['fecha_nacimiento']
    if tipo=='Practitioner':
        d['qualification']=[{'identifier':[{'value':f['matricula']}], 'code':{'text':f['especialidad']}}]
    return d


def exportar(repo, paciente_id, destino, formato='json'):
    from seguridad import _auditar
    s = repo._servicio
    path = Path(destino)
    if formato not in ('json','xml') or path.suffix.lower() != '.'+formato:
        raise ErrorValidacion('Formato de salida JSON o XML incompatible con la extensión.')
    with s._repo.conectar() as c:
        c.execute('BEGIN IMMEDIATE'); actor=s._actor(c,repo._sesion,'FHIR')
        paciente = s._repo.obtener_paciente(paciente_id)
        recetas=s._repo.listar_prescripciones(paciente_id,activos=None)
        signos=s._repo.listar_signos(paciente_id,activos=None)
        practicas=[dict(f) for f in c.execute('SELECT * FROM Practicas WHERE paciente_id=?',(paciente_id,))]
        recursos=[_persona(paciente,'Patient')]
        ids={f['profesional_id'] for f in recetas+practicas}|{f['medico_id'] for f in signos if f['medico_id']}
        for i in sorted(ids):
            f=next(f for f in s._repo.listar_profesionales(None) if f['id']==i)
            recursos.append(_persona(f,'Practitioner'))
        for f in practicas:
            recursos.append({'resourceType':'ServiceRequest','id':'sr-'+str(f['id']),
                'status':'active' if f['activo'] else 'revoked','intent':'order',
                'code':{'coding':[{'system':f['sistema_codigo'],'code':f['codigo'],'display':f['descripcion']}],'text':f['descripcion']},
                'subject':{'reference':'Patient/p-'+str(paciente_id)},'authoredOn':fecha(f['fecha_solicitud']),
                'requester':{'reference':'Practitioner/pr-'+str(f['profesional_id'])}})
        for f in recetas:
            recursos.append({'resourceType':'MedicationRequest','id':'mr-'+str(f['id']),
                'status':'active' if f['activo'] else 'cancelled','intent':'order',
                'medicationCodeableConcept':{'coding':[{'system':'urn:openhis:farmacos','code':f['farmaco_codigo']}],'text':f['farmaco']},
                'subject':{'reference':'Patient/p-'+str(paciente_id)},'authoredOn':fecha(f['fecha_prescripcion']),
                'requester':{'reference':'Practitioner/pr-'+str(f['profesional_id'])},
                'dosageInstruction':[{'text':f['dosis'], 'timing':{'code':{'text':f['frecuencia']}},'route':{'text':f['via_administracion']}}],
                **({'dispenseRequest':{'quantity':{'value':f['cantidad']}}} if f['cantidad'] is not None else {}),
                **({'note':[{'text':f['indicaciones']}]} if f['indicaciones'] else {})})
        for f in signos:
            if not f['medico_id']: continue
            for code,(campo,unidad) in LOINC.items():
                if f[campo] is not None:
                    recursos.append({'resourceType':'Observation','id':f"obs-{f['id']}-{code}",
                        'status':'final' if f['activo'] else 'entered-in-error',
                        'code':{'coding':[{'system':'http://loinc.org','code':code}]},
                        'subject':{'reference':'Patient/p-'+str(paciente_id)},'effectiveDateTime':fecha(f['fecha_hora']),
                        'performer':[{'reference':'Practitioner/pr-'+str(f['medico_id'])}],
                        'valueQuantity':{'value':f[campo],'unit':unidad,'system':'http://unitsofmeasure.org','code':unidad}})
        bundle={'resourceType':'Bundle','id':str(uuid4()),'identifier':{'system':'urn:openhis:equipo2','value':str(uuid4())},
                'type':'collection','timestamp':datetime.now(timezone.utc).isoformat(),
                'entry':[{'fullUrl':'https://openhis.example.invalid/fhir/'+r['resourceType']+'/'+r['id'],'resource':r} for r in recursos]}
        validar(bundle)
        contenido=json.dumps(bundle,ensure_ascii=False,indent=2,allow_nan=False) if formato=='json' else _xml(bundle)
        path.parent.mkdir(parents=True,exist_ok=True)
        archivo=path.open('x',encoding='utf-8')
        try:
            with archivo: archivo.write(contenido)
            _auditar(c,actor,'Pacientes',paciente_id,'E',nuevo={'formato':'FHIR '+formato},referencia=path)
            c.commit()
        except Exception:
            path.unlink(missing_ok=True);raise
        return bundle


def importar(repo, archivo, origen):
    repo.autorizar('FHIR')
    try:
        return _importar(repo,archivo,origen)
    except (KeyError,TypeError,AttributeError,IndexError,OverflowError) as error:
        raise ErrorValidacion('Estructura o tipo de dato no compatible con el perfil FHIR soportado.') from error


def _importar(repo, archivo, origen):
    from seguridad import _auditar
    repo.autorizar('FHIR')
    origen=str(origen).strip()
    if not origen: raise ErrorValidacion('Identifique la institución de origen del intercambio.')
    bundle=leer(archivo);mapa=validar(bundle);s=repo._servicio
    resultado={'creados':{},'reutilizados':{},'omitidos':0,'conflictos':[]}
    with s._repo.conectar() as c:
        c.execute('BEGIN IMMEDIATE');actor=s._actor(c,repo._sesion,'FHIR')
        resueltos={}
        def insertar(tabla,datos):
            datos['usuario_alta_id']=actor['id']
            campos=','.join(datos);params=','.join('?' for _ in datos)
            i=c.execute(f'INSERT INTO {tabla} ({campos}) VALUES ({params})',tuple(datos.values())).lastrowid
            _auditar(c,actor,tabla,i,'I',nuevo=datos,referencia=archivo)
            resultado['creados'][tabla]=resultado['creados'].get(tabla,0)+1
            return i
        def catalogo(tabla,codigo,nombre,**extras):
            f=c.execute(f'SELECT id FROM {tabla} WHERE codigo=?',(codigo,)).fetchone()
            if f: return f[0]
            return insertar(tabla,dict(codigo=codigo,nombre=nombre,**extras))
        for e in bundle['entry']:
            r=e['resource'];t=r['resourceType']
            if t not in ('Patient','Practitioner'): continue
            tabla='Pacientes' if t=='Patient' else 'Profesionales';dni=validar_dni(r['identifier'][0]['value'])
            f=c.execute(f'SELECT * FROM {tabla} WHERE dni=?',(dni,)).fetchone()
            if f:
                i=f['id'];resultado['reutilizados'][tabla]=resultado['reutilizados'].get(tabla,0)+1
                if (r['name'][0]['family']!=f['apellido'] or ' '.join(r['name'][0]['given'])!=f['nombre']):
                    resultado['conflictos'].append(f'{tabla}: DNI {dni}; datos locales conservados.')
                    _auditar(c,actor,tabla,i,'C',nuevo={'DNI':dni,'regla':'reutilizar sin sobrescribir'},referencia=archivo)
            else:
                d=dict(dni=dni,nombre=' '.join(r['name'][0]['given']),apellido=r['name'][0]['family'],
                    sexo={'male':'M','female':'F','other':'O'}.get(r.get('gender'),'U'),
                    fecha_nacimiento=r.get('birthDate'),activo=int(r.get('active',True)))
                if t=='Practitioner':
                    matricula=next((x.get('value') for q in r.get('qualification',[]) for x in q.get('identifier',[]) if x.get('value')),None)
                    if not matricula: raise ErrorValidacion('El profesional nuevo requiere matrícula.')
                    if c.execute('SELECT id FROM Profesionales WHERE matricula=?',(matricula,)).fetchone():
                        raise ErrorValidacion('Matrícula existente con otro DNI. No se sobrescribió el profesional.')
                    d.update(matricula=matricula,especialidad_id=catalogo('Especialidades','FHIR-SIN-ESPECIALIDAD','Especialidad no informada en FHIR'))
                i=insertar(tabla,d)
            resueltos[t+'/'+r['id']]=i
        for key,r in mapa.items():
            if r['resourceType'] in ('Patient','Practitioner'):
                resueltos[key]=resueltos[r['resourceType']+'/'+r['id']]
        for e in bundle['entry']:
            r=e['resource'];t=r['resourceType']
            if t in ('Patient','Practitioner'): continue
            serial=json.dumps(r,sort_keys=True,ensure_ascii=False,allow_nan=False)
            anterior=c.execute('SELECT contenido FROM RecursosFHIR WHERE origen=? AND tipo=? AND id_externo=?',(origen,t,r['id'])).fetchone()
            if anterior:
                if anterior[0]!=serial: raise ErrorValidacion('El ID externo ya existe con contenido distinto. Importación cancelada.')
                resultado['omitidos']+=1;continue
            pid=resueltos[r['subject']['reference']]
            profesional_ref=r.get('requester',{}).get('reference') or r['performer'][0]['reference']
            pro=resueltos[profesional_ref]
            activo=int(r.get('status') not in ('cancelled','revoked','stopped','entered-in-error'))
            if t=='ServiceRequest':
                cc=r.get('code',{});coding=cc.get('coding',[{}])[0]
                if not coding.get('code'): raise ErrorValidacion('ServiceRequest requiere código de práctica.')
                tabla='Practicas';i=insertar(tabla,dict(paciente_id=pid,profesional_id=pro,codigo=coding['code'],
                    sistema_codigo=coding.get('system','urn:openhis:externo'),descripcion=cc.get('text') or coding.get('display') or coding['code'],
                    fecha_solicitud=fecha(r['authoredOn']),activo=activo))
            elif t=='MedicationRequest':
                cc=r.get('medicationCodeableConcept',{});coding=cc.get('coding',[{}])[0]
                nombre=cc.get('text') or coding.get('display')
                if not nombre: raise ErrorValidacion('MedicationRequest requiere medicamento.')
                codigo='FHIR-'+sha256((coding.get('system','')+'|'+coding.get('code',nombre)).encode()).hexdigest()[:24]
                farmaco=catalogo('Farmacos',codigo,nombre)
                dos=r.get('dosageInstruction',[{}])[0]
                tabla='Prescripciones';i=insertar(tabla,dict(paciente_id=pid,profesional_id=pro,farmaco_id=farmaco,
                    dosis=dos.get('text') or 'No informada',via_administracion=dos.get('route',{}).get('text') or 'No informada',
                    frecuencia=dos.get('timing',{}).get('code',{}).get('text') or 'No informada',
                    cantidad=r.get('dispenseRequest',{}).get('quantity',{}).get('value'),
                    indicaciones='\n'.join(n.get('text','') for n in r.get('note',[])),fecha_prescripcion=fecha(r['authoredOn']),activo=activo))
            else:
                campo=LOINC[r['code']['coding'][0]['code']][0];valor=r['valueQuantity']['value'];momento=fecha(r['effectiveDateTime'])
                # Se compara una fecha normalizada y la medición; no se duplica por cambiar el ID externo.
                filas=c.execute(f'SELECT id,fecha_hora FROM SignosVitales WHERE paciente_id=? AND {campo}=?',(pid,valor)).fetchall()
                existente=next((f['id'] for f in filas if fecha(f['fecha_hora'])==momento),None)
                tabla='SignosVitales'
                if existente: i=existente;resultado['omitidos']+=1
                else: i=insertar(tabla,dict(paciente_id=pid,medico_id=pro,fecha_hora=momento,**{campo:valor},motivo_consulta='Observación FHIR externa',activo=activo))
            c.execute('INSERT INTO RecursosFHIR (origen,tipo,id_externo,tabla_local,registro_id,contenido) VALUES (?,?,?,?,?,?)',
                      (origen,t,r['id'],tabla,i,serial))
        _auditar(c,actor,'RecursosFHIR',None,'I',nuevo=resultado,referencia=archivo)
    return resultado
