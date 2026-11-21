'use strict';
const $ = id => document.getElementById(id);
let csrf = '', catalogos = null, elegido = null, reprogramacion = null, accionActual = null;
const etiquetas = {SOLICITADO:'Solicitado',CONFIRMADO:'Confirmado',CANCELADO:'Cancelado',REPROGRAMADO:'Reprogramado',ATENDIDO:'Atendido',AUSENTE:'Ausente'};
function aviso(texto, error=false) { $('aviso').textContent=texto; $('aviso').classList.toggle('error',error); $('aviso').hidden=false; }
async function api(ruta, datos) {
  const opciones={credentials:'same-origin',headers:{}};
  if(datos!==undefined){opciones.method='POST';opciones.headers={'Content-Type':'application/json','X-CSRF-Token':csrf};opciones.body=JSON.stringify(datos);}
  const r=await fetch(ruta,opciones), d=await r.json();
  if(d.csrf)csrf=d.csrf;
  if(!r.ok){if(r.status===401 && ruta!=='/api/ingresar')mostrarIngreso();throw new Error(d.error||'No se pudo completar la operación.');}
  return d;
}
function elemento(tipo, texto, clase) { const e=document.createElement(tipo); if(texto!==undefined)e.textContent=texto;if(clase)e.className=clase;return e; }
function fechaTexto(fecha){return new Intl.DateTimeFormat('es-AR',{weekday:'short',day:'numeric',month:'long'}).format(new Date(fecha+'T12:00:00'));}
function mostrarIngreso(){ $('ingreso').hidden=false;$('portal').hidden=true;$('clave').value='';elegido=null;reprogramacion=null;if($('dialogo').open)$('dialogo').close(); }
function seccion(nombre){$('reserva').hidden=nombre!=='reserva';$('mis-turnos').hidden=nombre!=='turnos';for(const [id,activo] of [['nav-reservar',nombre==='reserva'],['nav-turnos',nombre==='turnos']]){if(activo)$(id).setAttribute('aria-current','page');else $(id).removeAttribute('aria-current');}}
function estadoInicial(){elegido=null;reprogramacion=null;$('seleccion').hidden=true;$('modo').textContent='NUEVA CONSULTA';$('etiqueta-motivo').textContent='de la consulta';$('motivo').value='';$('nota-reserva').textContent='La reserva queda solicitada. Confirmala luego en Mis turnos.';$('boton-reservar').textContent='Reservar turno';$('cancelar-reprogramacion').hidden=true;}
async function mostrarPortal(paciente){
  $('ingreso').hidden=true;$('portal').hidden=false;$('nombre').textContent=paciente.nombre;$('clave').value='';
  catalogos=await api('/api/catalogos');$('especialidad').replaceChildren(new Option('Todas las especialidades',''));
  for(const e of catalogos.especialidades)$('especialidad').add(new Option(e.nombre,e.id));filtrarProfesionales();
  const hoy=new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Argentina/Buenos_Aires',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  $('fecha').min=hoy;$('fecha').value=hoy;estadoInicial();seccion('reserva');await cargarTurnos();
}
function filtrarProfesionales(){const esp=$('especialidad').value;$('profesional').replaceChildren(new Option('Cualquier profesional',''));for(const p of catalogos.profesionales.filter(p=>!esp||String(p.especialidad_id)===esp))$('profesional').add(new Option(`${p.nombre} ${p.apellido}`,p.id));}
async function buscar(){
  elegido=null;$('seleccion').hidden=true;$('huecos').replaceChildren(elemento('p','Buscando horarios…','vacio'));
  try{
    const q=new URLSearchParams({fecha:$('fecha').value,profesional_id:$('profesional').value,especialidad_id:$('especialidad').value});
    const d=await api('/api/disponibles?'+q);$('huecos').replaceChildren();$('cuenta-huecos').textContent=`${d.huecos.length} horarios disponibles`;
    if(!d.huecos.length){const v=elemento('div',undefined,'vacio');v.append(elemento('strong','No hay horarios para esta búsqueda'),elemento('p','Probá otra fecha, especialidad o profesional.'));$('huecos').append(v);return;}
    for(const h of d.huecos){const b=elemento('button',undefined,'hueco');b.type='button';b.setAttribute('aria-pressed','false');b.append(elemento('strong',`${h.hora_inicio} – ${h.hora_fin}`),elemento('span',h.profesional),elemento('span',h.especialidad,'especialidad'));b.addEventListener('click',()=>{elegido=h;for(const e of $('huecos').children)e.setAttribute('aria-pressed','false');b.setAttribute('aria-pressed','true');$('detalle-horario').textContent=`${fechaTexto(h.fecha)} · ${h.hora_inicio}`;$('detalle-profesional').textContent=`${h.profesional} · ${h.especialidad}`;$('seleccion').hidden=false;$('motivo').focus();});$('huecos').append(b);}
  }catch(e){$('huecos').replaceChildren(elemento('p','No se pudo consultar la disponibilidad. Repetí la búsqueda.','vacio'));throw e;}
}
async function cargarTurnos(){
  const d=await api('/api/turnos');$('lista-turnos').replaceChildren();$('cantidad').textContent=d.turnos.filter(t=>t.gestionable).length;
  if(!d.turnos.length){const v=elemento('div',undefined,'vacio');v.append(elemento('strong','Todavía no tenés turnos'),elemento('p','Reservá una consulta desde la sección Reservar un turno.'));$('lista-turnos').append(v);return;}
  for(const t of d.turnos){const tarjeta=elemento('article',undefined,'turno'), fecha=elemento('div'),detalle=elemento('div'), acciones=elemento('div',undefined,'acciones');fecha.append(elemento('span',etiquetas[t.estado]||t.estado,'estado '+t.estado),elemento('h3',fechaTexto(t.fecha)),elemento('p',`${t.hora_inicio} – ${t.hora_fin}`));detalle.append(elemento('h3',t.profesional),elemento('p',t.especialidad),elemento('p',t.motivo_consulta));if(t.turno_origen_id)detalle.append(elemento('p',`Reprogramado desde el turno #${t.turno_origen_id}`));if(t.gestionable){for(const [accion,titulo] of [['confirmar','Confirmar'],['reprogramar','Reprogramar'],['cancelar','Cancelar']]){if(accion==='confirmar'&&t.estado!=='SOLICITADO')continue;const b=elemento('button',titulo,accion==='confirmar'?'primario':'secundario');b.addEventListener('click',()=>accion==='reprogramar'?prepararCambio(t):abrirDialogo(t,accion));acciones.append(b);}}tarjeta.append(fecha,detalle,acciones);$('lista-turnos').append(tarjeta);}
}
function prepararCambio(t){estadoInicial();reprogramacion=t.id;$('modo').textContent=`REPROGRAMAR TURNO #${t.id}`;$('etiqueta-motivo').textContent='del cambio';$('nota-reserva').textContent='El turno anterior se conservará como reprogramado. El nuevo quedará solicitado para confirmar.';$('boton-reservar').textContent='Guardar nuevo horario';$('cancelar-reprogramacion').hidden=false;seccion('reserva');aviso('Buscá y elegí un horario nuevo para reprogramar.');$('huecos').replaceChildren(elemento('p','Buscá un nuevo horario para este turno.','vacio'));$('cuenta-huecos').textContent='';$('fecha').focus();}
function abrirDialogo(t,accion){accionActual={turno:t,accion};$('titulo-dialogo').textContent=accion==='confirmar'?'Confirmar tu asistencia':'Cancelar este turno';$('detalle-dialogo').textContent=`${fechaTexto(t.fecha)}, ${t.hora_inicio} · ${t.profesional}`;$('campo-razon').hidden=accion!=='cancelar';$('razon').required=accion==='cancelar';$('razon').value='';$('dialogo').showModal();}
function accion(form,fn){form.addEventListener('submit',async e=>{e.preventDefault();const b=form.querySelector('button[type=submit]');b.disabled=true;try{await fn();}catch(error){aviso(error.message,true);}finally{b.disabled=false;}});}
accion($('form-ingreso'),async()=>{const d=await api('/api/ingresar',{dni:$('dni').value,clave:$('clave').value});$('aviso').hidden=true;await mostrarPortal(d.paciente);});
accion($('form-buscar'),buscar);
accion($('form-reservar'),async()=>{if(!elegido)throw new Error('Elegí un horario disponible.');const datos={...elegido,motivo:$('motivo').value};const ruta=reprogramacion?`/api/turnos/${reprogramacion}/reprogramar`:'/api/turnos';await api(ruta,datos);estadoInicial();await cargarTurnos();seccion('turnos');aviso('El turno quedó solicitado. Confirmalo para completar la reserva.');$('huecos').replaceChildren(elemento('p','Repetí la búsqueda para reservar otro turno.','vacio'));$('cuenta-huecos').textContent='';});
accion($('form-accion'),async()=>{const {turno,accion}=accionActual;try{await api(`/api/turnos/${turno.id}/${accion}`,{motivo:$('razon').value});$('dialogo').close();await cargarTurnos();aviso(accion==='confirmar'?'Turno confirmado.':'Turno cancelado. El horario vuelve a estar disponible.');}catch(e){$('dialogo').close();await cargarTurnos();throw e;}});
$('especialidad').addEventListener('change',filtrarProfesionales);
$('nav-reservar').addEventListener('click',()=>seccion('reserva'));
$('nav-turnos').addEventListener('click',()=>{seccion('turnos');cargarTurnos().catch(e=>aviso(e.message,true));});
$('actualizar').addEventListener('click',()=>cargarTurnos().catch(e=>aviso(e.message,true)));
$('cancelar-reprogramacion').addEventListener('click',()=>{estadoInicial();seccion('turnos');});
$('cerrar-dialogo').addEventListener('click',()=>$('dialogo').close());
$('salir').addEventListener('click',async()=>{try{await api('/api/salir',{});mostrarIngreso();$('aviso').hidden=true;}catch(e){aviso(e.message,true);}});
api('/api/sesion').then(d=>d.paciente?mostrarPortal(d.paciente):mostrarIngreso()).catch(e=>aviso(e.message,true));
