import json
import sqlite3

import pytest

from datos import ErrorValidacion, Repositorio
from seguridad import Seguridad
import fhir
from tests.test_entrega9 import entorno, crear_bundle
from tests.test_entrega10 import solo_observaciones, datos_base


def sin_responsable(repo, tmp_path):
    bundle = solo_observaciones(crear_bundle(repo, tmp_path))
    for entry in bundle['entry']:
        if entry['resource']['resourceType'] == 'Observation':
            entry['resource'].pop('performer')
    return bundle


def escribir(bundle, tmp_path, nombre='recibido.json'):
    archivo = tmp_path/nombre
    archivo.write_text(fhir._xml(bundle) if archivo.suffix == '.xml' else json.dumps(bundle, ensure_ascii=False), encoding='utf-8')
    return archivo


@pytest.mark.parametrize('formato', ['json', 'xml'])
def test_importar_y_reexportar_observaciones_sin_responsable(entorno, tmp_path, formato):
    servicio, sesion, repo = entorno
    bundle = sin_responsable(repo, tmp_path)
    archivo = escribir(bundle, tmp_path, 'recibido.'+formato)
    original = archivo.read_bytes()
    antes = datos_base(servicio)
    plan = fhir.preparar_importacion(repo, archivo, 'Centro externo')
    assert datos_base(servicio) == antes
    assert any('4 observaciones sin profesional' in aviso for aviso in plan.resumen['advertencias'])
    assert fhir.confirmar_importacion(repo, plan, confirmado=False) is None
    assert datos_base(servicio) == antes
    resultado = fhir.confirmar_importacion(repo, plan, confirmado=True)
    assert resultado['creados']['SignosVitales'] == 1
    with servicio._repo.conectar() as c:
        fila = c.execute("SELECT * FROM SignosVitales WHERE origen_fhir='Centro externo'").fetchone()
        assert fila['medico_id'] is None
        assert fila['usuario_alta_id'] == servicio.autorizar(sesion)['id']
        assert (fila['presion_sistolica'], fila['presion_diastolica'], fila['frecuencia_cardiaca'], fila['temperatura']) == (121, 81, 75, 36.7)
        guardados = c.execute("SELECT contenido FROM RecursosFHIR WHERE origen='Centro externo'").fetchall()
        assert len(guardados) == 4
        assert all('performer' not in json.loads(r[0]) for r in guardados)
    plan = fhir.preparar_importacion(repo, archivo, 'Centro externo')
    assert fhir.confirmar_importacion(repo, plan, confirmado=True)['creados'] == {}
    assert archivo.read_bytes() == original
    paciente = next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType'] == 'Patient')
    pid = repo.buscar_paciente(paciente['identifier'][0]['value'])['id']
    salida = tmp_path/('reexportado.'+formato)
    fhir.exportar(repo, pid, salida, formato)
    reexportado = fhir.leer(salida)
    observaciones = [e['resource'] for e in reexportado['entry'] if e['resource']['resourceType'] == 'Observation' and e['resource']['effectiveDateTime'] == fila['fecha_hora']]
    assert len(observaciones) == 4
    assert all('performer' not in r for r in observaciones)
    otro = Seguridad(tmp_path/'receptor.db')
    otro.crear_admin_inicial('admin', 'OtroAdmin123', 'Otro administrador')
    receptor = otro.repositorio(otro.autenticar('admin', 'OtroAdmin123'))
    fhir.importar(receptor, salida, 'Equipo 2')
    with otro._repo.conectar() as c:
        recibida = c.execute('SELECT * FROM SignosVitales WHERE fecha_hora=?', (fila['fecha_hora'],)).fetchone()
        assert recibida['medico_id'] is None and recibida['temperatura'] == 36.7
        assert c.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('performer', [
    [{}], ['invalido'], [{'reference': 'Practitioner/no-existe'}],
    [{'reference': 'Practitioner/a'}, {'reference': 'Practitioner/b'}],
    {'reference': 'Practitioner/a'},
])
def test_responsable_declarado_invalido_no_se_ignora(entorno, tmp_path, performer):
    servicio, sesion, repo = entorno
    bundle = sin_responsable(repo, tmp_path)
    bundle['entry'][-1]['resource']['performer'] = performer
    antes = datos_base(servicio)
    with pytest.raises(ErrorValidacion, match='profesional|referencia'):
        fhir.preparar_importacion(repo, escribir(bundle, tmp_path), 'Centro')
    assert datos_base(servicio) == antes


@pytest.mark.parametrize('tipo', ['MedicationRequest', 'ServiceRequest'])
def test_solicitudes_siguen_requiriendo_prescriptor(entorno, tmp_path, tipo):
    servicio, sesion, repo = entorno
    bundle = crear_bundle(repo, tmp_path)
    recurso = next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType'] == tipo)
    recurso.pop('requester')
    antes = datos_base(servicio)
    with pytest.raises(ErrorValidacion, match='referencias'):
        fhir.preparar_importacion(repo, escribir(bundle, tmp_path), 'Centro')
    assert datos_base(servicio) == antes


@pytest.mark.parametrize('origen', [None, '', '   '])
def test_altas_locales_siguen_exigiendo_profesional(entorno, tmp_path, origen):
    servicio, sesion, repo = entorno
    paciente = repo.listar_pacientes()[0]['id']
    with pytest.raises(ErrorValidacion):
        repo.registrar_signos(paciente, {'motivo_consulta': 'Prueba', 'medico_id': None, 'origen_fhir': 'No habilita la carga manual'})
    with servicio._repo.conectar() as c:
        with pytest.raises(sqlite3.IntegrityError, match='Seleccione un profesional'):
            c.execute('INSERT INTO SignosVitales(paciente_id,medico_id,origen_fhir) VALUES (?,NULL,?)', (paciente, origen))


def test_migracion_repetida_conserva_signos_y_origen(entorno, tmp_path):
    servicio, sesion, repo = entorno
    bundle = sin_responsable(repo, tmp_path)
    archivo = escribir(bundle, tmp_path)
    # Simular la restricción de la versión anterior.
    with servicio._repo.conectar() as c:
        anteriores = [dict(r) for r in c.execute('SELECT * FROM SignosVitales')]
        c.execute('DROP TRIGGER signos_medico_requerido')
        c.execute('DROP TRIGGER signos_conservar_origen_fhir')
        c.execute('ALTER TABLE SignosVitales DROP COLUMN origen_fhir')
        c.execute("""CREATE TRIGGER signos_medico_requerido BEFORE INSERT ON SignosVitales
            WHEN NEW.medico_id IS NULL BEGIN SELECT RAISE(ABORT, 'Seleccione un profesional para registrar signos vitales.'); END""")
    Repositorio(servicio._repo.ruta)
    with servicio._repo.conectar() as c:
        assert [dict(r) for r in c.execute('SELECT * FROM SignosVitales')] == anteriores
    fhir.importar(repo, archivo, 'Centro')
    antes = datos_base(servicio)
    Repositorio(servicio._repo.ruta)
    assert datos_base(servicio) == antes
    with servicio._repo.conectar() as c:
        with pytest.raises(sqlite3.IntegrityError, match='Conserve el origen'):
            c.execute("UPDATE SignosVitales SET origen_fhir=NULL WHERE origen_fhir='Centro'")
        assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_fechas_heredadas_y_metadatos_faltantes_se_advierten(entorno, tmp_path):
    servicio, sesion, repo = entorno
    bundle = sin_responsable(repo, tmp_path)
    for entry in bundle['entry']:
        recurso = entry['resource']
        if recurso['resourceType'] == 'Observation':
            recurso['effectiveDateTime'] = '2026-11-01 12:00:00'
        elif recurso['resourceType'] == 'Practitioner':
            for q in recurso['qualification']:
                q.pop('code', None)
    archivo = escribir(bundle, tmp_path)
    antes = datos_base(servicio)
    plan = fhir.preparar_importacion(repo, archivo, 'Centro')
    assert datos_base(servicio) == antes
    assert any('4 fechas sin zona' in a for a in plan.resumen['advertencias'])
    assert any('titulaciones sin code' in a for a in plan.resumen['advertencias'])
    assert any('no contiene prácticas' in a for a in plan.resumen['advertencias'])
    resultado = fhir.confirmar_importacion(repo, plan, confirmado=True)
    with servicio._repo.conectar() as c:
        fecha = c.execute("SELECT fecha_hora FROM SignosVitales WHERE origen_fhir='Centro'").fetchone()[0]
        assert fecha == '2026-11-01T12:00:00Z'
        auditado = json.loads(c.execute("SELECT datos_nuevos FROM Auditoria WHERE tabla_afectada='RecursosFHIR' ORDER BY id DESC LIMIT 1").fetchone()[0])
        assert auditado['advertencias'] == resultado['advertencias']


def test_identidad_inactiva_no_se_reactiva_al_recibir_signos_sin_profesional(entorno, tmp_path):
    servicio, sesion, repo = entorno
    bundle = sin_responsable(repo, tmp_path)
    paciente = next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType'] == 'Patient')
    pid = repo.buscar_paciente(paciente['identifier'][0]['value'])['id']
    repo.dar_baja_paciente(pid)
    cantidad = len(repo.listar_pacientes(None))
    resultado = fhir.importar(repo, escribir(bundle, tmp_path), 'Centro')
    assert resultado['creados']['SignosVitales'] == 1
    assert len(repo.listar_pacientes(None)) == cantidad
    assert repo.obtener_paciente(pid)['activo'] == 0
