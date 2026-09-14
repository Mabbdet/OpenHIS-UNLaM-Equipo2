"""Entrega 2: registro y búsqueda por consola. Ejecutar: python Pacientes.py."""

import sqlite3

from datos import CAMPOS_PACIENTE, ETIQUETAS, ErrorValidacion, Repositorio


def conectar_bd():
    return Repositorio()


def registrar_paciente(repositorio):
    entrada = {campo: input(f"{ETIQUETAS[campo]}: ") for campo in CAMPOS_PACIENTE}
    paciente_id = repositorio.registrar_paciente(entrada)
    print(f"\nPACIENTE REGISTRADO CON ÉXITO\nNúmero de Historia Clínica: {paciente_id}")


def buscar_paciente(repositorio):
    paciente = repositorio.buscar_paciente(input("DNI: "))
    if paciente is None:
        print("PACIENTE NO ENCONTRADO")
        return
    print(f"\nPACIENTE ENCONTRADO\nNúmero de Historia Clínica: {paciente['id']}")
    for campo in CAMPOS_PACIENTE:
        print(f"{ETIQUETAS[campo]}: {paciente[campo] or 'Sin informar'}")
    print(f"Fecha de registro (UTC): {paciente['fecha_registro']}")


def menu():
    repositorio = conectar_bd()
    while True:
        print("\nHOSPITAL UNIVERSITARIO SAN JUSTO\n1. Registrar nuevo paciente\n2. Buscar paciente por DNI\n3. Salir")
        try:
            opcion = input("Opción: ").strip()
            if opcion == "1":
                registrar_paciente(repositorio)
            elif opcion == "2":
                buscar_paciente(repositorio)
            elif opcion == "3":
                return
            else:
                print("Seleccione una opción entre 1 y 3.")
        except ErrorValidacion as error:
            print(f"ERROR: {error}")
        except sqlite3.Error:
            print("ERROR: No se pudo completar la operación en la base de datos.")
        except (EOFError, KeyboardInterrupt):
            print("\nPrograma finalizado.")
            return


if __name__ == "__main__":
    menu()
