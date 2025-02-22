# SNAP7 PLC Adquisition

Este repositorio contiene un conjunto de scripts en Python para la **lectura de datos** desde un **PLC Siemens** usando la librería **Snap7**, y el **envío asíncrono** de dichos datos a un servidor RabbitMQ para su posterior procesamiento o almacenamiento.

## Estructura de archivos

- **`SNAP7_Change_data.py`**  
  Define la clase `PLC_Instance`, la cual:
  - Se conecta a un PLC Siemens mediante Snap7.
  - Lee datos de varios tipos (bool, byte, int16, int32, float) de un DB (Data Block) configurado.
  - Identifica cuándo hay cambios en los valores leídos y, si detecta alguno, envía esos cambios a un servidor RabbitMQ (cola `datos_plc`).

- **`main.py`**  
  - Importa la clase `PLC_Instance` desde `SNAP7_Change_data.py`.
  - Configura un objeto `PLC1` indicando cuántos bytes y tipos de datos se leerán:
    - `DB=1000`  
    - `B_Bools=400`  (400 bits, equivalentes a 50 bytes, dedicados a señales booleanas)
    - `B_Bytes=20`   (20 bytes)
    - `B_Int16=596`  (596 bytes dedicados a variables de 16 bits)
    - `B_Int32=396`  (396 bytes dedicados a variables de 32 bits)
    - `B_Float=0`    (0 bytes dedicados a variables tipo float, aunque el código contempla la opción)
  - Conecta el PLC (por ejemplo, IP `121.11.244.12`, rack 0, slot 1).
  - Utiliza `asyncio.run(main())` para:
    1. Leer todos los datos una primera vez (`PLC1.GetAllDataPLC()`).
    2. En cada iteración, llamar a `PLC1.GetChangeDataPLC()`, que:
       - Lee el PLC.
       - Identifica si hay alguna variable que cambió desde la última lectura.
       - Si hay cambios, envía un mensaje (un `dict` en formato `str`) a RabbitMQ.

## Principios de funcionamiento

1. **Lectura de DB en Snap7**  
   - El PLC se conecta con `Snap7`, y `db_read` descarga un trozo de memoria (DB) de largo determinado.
   - El constructor `PLC_Instance` define cuántos bytes se dedican a:
     - Bits (booleanos).
     - Bytes puros.
     - Enteros de 16 bits (`Int16`).
     - Enteros de 32 bits (`Int32`).
     - Flotantes (`Float`).
   - Al leerlos, se asignan offsets en el buffer (por ejemplo, `B_Bools = 400` bits, `B_Bytes = 20` bytes, etc.).

2. **Identificación de datos**  
   - Los métodos `get_bool`, `get_byte`, `get_int`, `get_dint` y `get_real` (proveídos por la librería `snap7.util`) extraen los valores en cada offset.
   - Se crea un diccionario (`AllData` o `ChangeData`) con claves como `"Bool_011_o_({byte_index})_{bit_index}"`, `"Byte_011_o_({byte_index})"`, etc.

3. **Detección de cambios**  
   - La clase mantiene `ChangeData_mem`, un diccionario con el último valor conocido de cada variable.
   - Cada vez que se llama `GetChangeDataPLC()`, se compara el valor actual con el guardado:
     - Si cambió, se actualiza y se marca en `ChangeData`.
     - Al final de la lectura, si `ChangeData` no está vacío, se añade un `TimeStamp` y se envía a RabbitMQ.

4. **Envío a RabbitMQ**  
   - Mediante la librería `pika`, se crea una conexión a `localhost` (o la dirección configurada).
   - Se define la cola `datos_plc`.
   - Se publica el contenido de `ChangeData` (convertido a `str`) en esa cola.

5. **Ejemplo de uso**  
   - Ajustar IP, rack y slot en `main.py` según tu PLC.
   - Ajustar la dirección y cola de RabbitMQ en `SNAP7_Change_data.py` (por defecto host=‘localhost’).
   - Ejecutar `python main.py`.  
   - Ver en la consola las variables leídas y en la cola de RabbitMQ los mensajes que llegan con los datos cambiados.

## Requisitos

- Python 3.x  
- Librerías:
  - `snap7` (para comunicarse con el PLC)
  - `pika` (para conectarse a RabbitMQ)
  - `asyncio` (librería estándar de Python para manejo asíncrono)
- Un PLC Siemens accesible en la IP y DB configurados.
- Un servidor RabbitMQ corriendo, preferiblemente en la máquina local (localhost) o en la red correspondiente.

## Notas finales

- **Seguridad**: Asegúrate de tener los permisos adecuados en el PLC y en RabbitMQ.
- **Rendimiento**: Si se requieren altas tasas de lectura, habría que optimizar las conexiones o agrupar lecturas.
- **Escalabilidad**: Se podría almacenar o procesar los datos recibidos de RabbitMQ en una base de datos u otro servicio.

¡Disfruta de la lectura y monitoreo de tu PLC con Snap7 y la mensajería asíncrona de RabbitMQ!
