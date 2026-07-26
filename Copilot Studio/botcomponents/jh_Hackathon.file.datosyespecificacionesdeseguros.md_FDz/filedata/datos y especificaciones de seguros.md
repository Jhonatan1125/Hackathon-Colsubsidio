# Póliza para Carros

## 1. Identificación del cliente

1. Solicitar la **Cédula (Serial)**.
2. Consultar la base de datos y recuperar automáticamente:
   - Nombre y apellidos.
   - Teléfono.
   - Correo electrónico.
   - Departamento y ciudad registrados.

## 2. Confirmación de datos de contacto

El bot deberá mostrar los datos recuperados y preguntar:

- ¿Este sigue siendo tu número de teléfono?
- ¿Este sigue siendo tu correo electrónico?

Si existe alguna modificación:

- Permitir la actualización.
- Guardar la información actualizada en la base de datos.

## 3. Información del vehículo

Solicitar:

- Placa.
- Marca.
- Año del modelo.
- Línea o referencia.
- Cilindraje.
- ¿Es vehículo 0 km? (Sí/No).
- ¿El vehículo cuenta con endoso o prenda? (Sí/No).

## 4. Ubicación habitual

Obtener por defecto:

- Departamento.
- Municipio.

Luego confirmar:

> Selecciona el departamento y municipio donde estacionas frecuentemente tu vehículo.

Si el cliente modifica la información:

- Actualizar en la base de datos.
- Utilizarla para futuras cotizaciones.

**Regla:** Si la información ya existe y está actualizada, no volver a solicitarla.

---

# Póliza para Motos

## 1. Identificación del cliente

1. Solicitar la **Cédula (Serial)**.
2. Recuperar automáticamente:
   - Nombre y apellidos.
   - Teléfono.
   - Correo electrónico.
   - Departamento y ciudad registrados.

## 2. Confirmación de datos de contacto

Confirmar:

- Teléfono.
- Correo electrónico.

Permitir actualización y guardar cambios.

## 3. Información de la moto

Solicitar:

- Placa.
- Marca.
- Año del modelo.
- Línea o referencia.
- Cilindraje.
- ¿Es moto 0 km? (Sí/No).
- ¿La moto cuenta con endoso o prenda? (Sí/No).

## 4. Ubicación habitual

Solicitar confirmación de:

- Departamento.
- Municipio donde permanece la moto habitualmente.

Actualizar información en caso de cambios.

**Regla:** Si dichos datos ya están almacenados, no volver a preguntarlos.

---

# Seguros para Bicicletas y Patinetas

## 1. Identificación del cliente

1. Solicitar la **Cédula (Serial)**.
2. Recuperar automáticamente:
   - Nombre y apellidos.
   - Fecha de nacimiento.
   - Fecha de expedición de la cédula.
   - Teléfono.
   - Correo electrónico.
   - Departamento y ciudad registrados.

## 2. Confirmación de datos de contacto

Confirmar:

- Teléfono.
- Correo electrónico.

Permitir actualización y almacenamiento.

## 3. Información del activo

Determinar:

- ¿Es una bicicleta o una patineta?

### Si es bicicleta

Preguntar:

- Tipo de bicicleta.

### Información general

Solicitar:

- Placa (si aplica).
- Marca.
- Línea o referencia.
- Año del modelo.
- Fecha de compra.
- Valor comercial (COP).
- Valor de accesorios o modificaciones (COP).

## 4. Ubicación habitual

Confirmar:

> Departamento y municipio donde permanece habitualmente el activo.

Actualizar información si es necesario.

**Regla:** Si ya existe en base de datos, omitir la pregunta.

---

# Seguros para Mascotas

## 1. Identificación del cliente

Solicitar la **Cédula (Serial)** y recuperar:

- Nombre y apellidos.
- Fecha de nacimiento.
- Fecha de expedición de la cédula.
- Ocupación.
- Salario.
- Profesión.
- Teléfono.
- Correo electrónico.

## 2. Información de la mascota

Solicitar:

- Nombre de la mascota.
- Tipo de mascota:
  - Perro.
  - Gato.
- Edad.
- Color.
- Raza.
- Peso.

## 3. Vacunas

Solicitar selección de vacunas aplicadas.

Ejemplo JSON:

```json
[
  {
    "vacuna": "Rabia",
    "aplicada": true
  },
  {
    "vacuna": "Moquillo",
    "aplicada": false
  },
  {
    "vacuna": "Parvovirus",
    "aplicada": true
  }
]
```

## 4. Enfermedades

Solicitar selección de enfermedades conocidas.

Ejemplo JSON:

```json
[
  {
    "enfermedad": "Diabetes",
    "aplica": false
  },
  {
    "enfermedad": "Artritis",
    "aplica": true
  },
  {
    "enfermedad": "Problemas cardíacos",
    "aplica": false
  }
]
```

## 5. Identificación de necesidad

El bot deberá deducir automáticamente si el cliente requiere:

- Medicina prepagada para mascotas.
- Asistencia para mascotas.
- Seguro integral para mascotas.
