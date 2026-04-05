# ModbusTool — Manual de Usuario

> Herramienta exclusiva para **Linux** (Ubuntu 24.04 y otras distribuciones modernas).

## 1. Requisitos previos

### Sistema operativo
- **Linux** (probado en Ubuntu 24.04, compatible con Debian, Fedora, Arch, etc.)
- Python 3.10 o superior

### Hardware
- **Adaptador USB a RS485** con terminales A y B (chips recomendados: CH340, FT232, CP2102 con transceiver MAX485). Los adaptadores USB a RS232 (solo PL2303) **no funcionan** para RS485.
- **Sensor/dispositivo Modbus RTU** alimentado correctamente (comprobar voltaje requerido en el manual del sensor).

### Software
```bash
pip install -r modbustool/requirements.txt
```

### Permisos (Linux)
Tu usuario debe pertenecer al grupo `dialout` para acceder a puertos serie:
```bash
sudo usermod -aG dialout $USER
```
Cierra sesion y vuelve a entrar para que aplique.

---

## 2. Inicio

```bash
cd modbustool
python3 main.py
```

La ventana principal tiene dos zonas:
- **Panel izquierdo**: conexion, perfil de dispositivo, direccion del esclavo
- **Area derecha**: pestanas Dashboard, Monitor, Scanner, Configuration

---

## 3. Conexion

### 3.1 Conexion Serie (RS485/RTU)

1. Conecta el adaptador USB al PC
2. En el panel izquierdo, tu puerto aparecera automaticamente (ej. `/dev/ttyUSB0 - USB-Serial Controller`)
3. Configura los parametros de comunicacion:
   - **Baud Rate**: la velocidad del sensor (tipico: 4800 o 9600)
   - **Parity**: normalmente None
   - **Data Bits**: normalmente 8
   - **Stop Bits**: normalmente 1
   - **Timeout**: 1 segundo es un buen valor por defecto
4. Pulsa **Connect**

El indicador LED pasara a verde si la conexion es correcta.

### 3.2 Conexion TCP/IP

1. Selecciona la pestana "Modbus TCP" en el panel de conexion
2. Introduce la IP y el puerto (por defecto 502)
3. Pulsa **Connect**

### 3.3 Uso de perfiles

Si conoces tu sensor, selecciona su perfil en el desplegable **Device Profile** y pulsa **Apply Defaults**. Esto configurara automaticamente el baud rate, paridad y direccion del esclavo segun los valores de fabrica del sensor.

---

## 4. Dashboard

La pestana **Dashboard** es la vista principal para uso diario.

### Tarjetas de valores
Cada registro del sensor se muestra como una tarjeta grande con:
- Nombre del parametro (ej. "Temperature")
- Valor actual en grande
- Unidad (ej. "C", "%RH")
- Hora de la ultima lectura

### Botones de accion

| Boton | Funcion |
|-------|---------|
| **Read Sensor Data** | Lee todos los registros de medicion del sensor |
| **Read Device Config** | Lee la configuracion actual (direccion, baud rate, calibracion) |
| **Auto-Read** | Activa la lectura continua automatica con el intervalo configurado |

### Registro de actividad
En la parte inferior se muestra un log en texto plano con cada lectura realizada, sin codigos hexadecimales.

---

## 5. Scanner

Usa esta pestana cuando no conoces la configuracion de un dispositivo.

### 5.1 Escaneo de bus

Busca dispositivos conectados probando diferentes direcciones:

1. Configura el rango de direcciones a escanear (ej. 1 a 50)
2. Marca los baud rates a probar (ej. 4800 y 9600)
3. Selecciona las paridades a probar
4. Pulsa **Start Scan**

Los dispositivos encontrados aparecen en la tabla inferior con su direccion, baud rate y paridad detectados.

**Nota**: durante el escaneo, la conexion principal se desconecta para liberar el puerto serie.

### 5.2 Auto-deteccion de baud rate

Si sabes la direccion del dispositivo pero no su baud rate:

1. Introduce la direccion del esclavo
2. Pulsa **Auto-Detect**

La herramienta probara todas las combinaciones de baud rate y paridad hasta encontrar respuesta. Cuando lo encuentra, configura automaticamente los parametros de conexion.

---

## 6. Monitor

Pestana para lectura avanzada de registros con control total.

### 6.1 Lectura manual

1. Selecciona la funcion Modbus (FC03 para Holding Registers es la mas comun)
2. Introduce la direccion del registro de inicio
3. Indica cuantos registros leer
4. Selecciona el formato de visualizacion:
   - **Unsigned 16-bit**: valores 0-65535
   - **Signed 16-bit**: valores -32768 a 32767
   - **Hex**: valor en hexadecimal
   - **Float32**: dos registros combinados como numero decimal
5. Pulsa **Read Once**

### 6.2 Polling continuo

1. Configura el intervalo (ej. 1 segundo)
2. Pulsa **Start Polling**
3. Los valores se actualizan automaticamente en la tabla

### 6.3 Lectura de perfil

Si tienes un perfil seleccionado, pulsa **Read Profile Registers** para leer todos los registros definidos en el perfil con sus nombres.

### 6.4 Log de datos

La pestana inferior **Data Log** acumula todas las lecturas con timestamp. Pulsa **Export CSV** para guardar como archivo CSV.

### 6.5 Tramas raw

La pestana **Raw Frames (TX/RX)** muestra cada trama enviada y recibida en hexadecimal, util para depuracion.

---

## 7. Configuracion

### 7.1 Registros del perfil

Si hay un perfil seleccionado, veras cada registro con:
- Nombre y descripcion
- Valor actual (pulsa **Read** para leerlo)
- Control de escritura (campo de valor o desplegable + boton **Write**)

**Cambiar baud rate**: selecciona el nuevo valor en el desplegable y pulsa Write. La aplicacion reconecta automaticamente al nuevo baud rate.

**Cambiar direccion**: introduce la nueva direccion y pulsa Write. La aplicacion actualiza automaticamente el slave address.

Cada escritura requiere confirmacion en un dialogo.

### 7.2 Escritura generica

En la pestana **Generic Read/Write** puedes escribir a cualquier registro manualmente:
- **Write Single Register (FC06)**: un registro, un valor
- **Write Multiple Registers (FC16)**: varios registros a la vez (valores separados por comas)
- **Write Coil (FC05)**: activar/desactivar una bobina

### 7.3 Operaciones por lotes

La pestana **Batch Operations** permite asignar direcciones unicas a multiples dispositivos identicos:

1. Configura la direccion actual del dispositivo (normalmente 1, la de fabrica)
2. Establece la siguiente direccion a asignar (ej. 2)
3. Opcionalmente selecciona un baud rate objetivo
4. Conecta el primer dispositivo (solo uno en el bus)
5. Pulsa **Read Current Config** para verificar comunicacion
6. Pulsa **Assign Next Address** para programar el dispositivo
7. Desconecta el dispositivo, conecta el siguiente, repite

La direccion se incrementa automaticamente despues de cada asignacion.

---

## 8. Crear perfiles de dispositivo

### 8.1 Con el Wizard (recomendado)

1. Ve a **File > New Profile Wizard** o pulsa el boton naranja **New Profile...** en el panel izquierdo
2. **Paso 1 — Informacion del dispositivo**: nombre, fabricante, descripcion, y los parametros de comunicacion por defecto (baud rate, paridad, etc.)
3. **Paso 2 — Registros de datos**: anade los registros que contienen mediciones. Para cada uno:
   - Nombre (ej. "Temperature")
   - Direccion del registro (en hexadecimal, como aparece en el manual del sensor)
   - Unidad, tipo de dato, factor de escala
   - Funcion de lectura (FC03 o FC04)
4. **Paso 3 — Registros de configuracion**: anade los registros de configuracion. Hay botones rapidos para "Device Address" y "Baud Rate" que pre-rellenan los campos comunes. Solo ajusta la direccion del registro.
5. **Paso 4 — Revisar y guardar**: revisa el JSON generado y guardalo

El perfil aparece automaticamente en el selector.

### 8.2 Factor de escala

Muchos sensores transmiten valores multiplicados. Por ejemplo:
- Temperatura 23.5 C se transmite como **235** con escala **0.1**
- Humedad 48.6% se transmite como **486** con escala **0.1**

Configura el factor de escala en el wizard para que los valores se muestren correctamente.

### 8.3 Mapa de valores

Algunos registros usan codigos numericos. Por ejemplo, el baud rate:
- Valor 1 = 1200 baud
- Valor 2 = 2400 baud
- Valor 3 = 4800 baud
- etc.

Usa la opcion "Has value mapping" en el editor de registros para definir estas correspondencias.

---

## 9. Solucion de problemas

### No se detecta el puerto USB
- Comprueba que el adaptador esta conectado
- Verifica que tu usuario pertenece al grupo `dialout`
- Los puertos se refrescan automaticamente cada 5 segundos

### No responde ningun dispositivo
- **Alimentacion**: verifica que el sensor recibe el voltaje adecuado (muchos necesitan 7-30V, no solo 5V USB)
- **Cables A/B**: prueba a intercambiarlos. Si al intercambiar recibes una avalancha de bytes 0x00, estan al reves
- **Baud rate**: usa Auto-Detect en la pestana Scanner para encontrar el baud rate correcto
- **Direccion**: si no sabes la direccion, escanea el rango 1-247

### La aplicacion se congela durante el escaneo
- El escaneo de muchas direcciones a multiples baud rates puede tardar. Usa rangos pequenos primero
- Pulsa **Stop** para cancelar el escaneo en cualquier momento

### Valores incorrectos en el dashboard
- Verifica el factor de escala en el perfil (ej. 0.1 para temperaturas en decimas de grado)
- Comprueba el tipo de dato (int16 para valores con signo, uint16 para valores sin signo)

---

## 10. Enlaces

- [Robotika.cloud](https://robotika.cloud/) — Desarrollo
- [nkz-os.org](https://nkz-os.org) — Proyecto relacionado
- [github.com/basabot/modbus-tool](https://github.com/basabot/modbus-tool) — Codigo fuente
