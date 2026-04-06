"""Internationalization support — Basque, French, Spanish, English."""

import json
import os

_current_lang = "en"
_translations = {}

LANGUAGES = {
    "en": "English",
    "es": "Español",
    "eu": "Euskara",
    "fr": "Français",
}

# All translatable strings. Key = English text.
_STRINGS = {
    # Main window
    "ModbusTool — Universal Modbus Configuration & Monitor": {
        "es": "ModbusTool — Configuración y monitorización Modbus universal",
        "eu": "ModbusTool — Modbus konfigurazio eta monitorizazio unibertsala",
        "fr": "ModbusTool — Configuration et surveillance Modbus universelle",
    },
    # Menu
    "File": {
        "es": "Archivo", "eu": "Fitxategia", "fr": "Fichier",
    },
    "New Profile Wizard...": {
        "es": "Asistente de nuevo perfil...", "eu": "Profil berriaren morroia...", "fr": "Assistant nouveau profil...",
    },
    "Load Profile...": {
        "es": "Cargar perfil...", "eu": "Profila kargatu...", "fr": "Charger profil...",
    },
    "Reload Profiles": {
        "es": "Recargar perfiles", "eu": "Profilak birkargatu", "fr": "Recharger les profils",
    },
    "Quit": {
        "es": "Salir", "eu": "Irten", "fr": "Quitter",
    },
    "Connection": {
        "es": "Conexión", "eu": "Konexioa", "fr": "Connexion",
    },
    "Connect": {
        "es": "Conectar", "eu": "Konektatu", "fr": "Connecter",
    },
    "Disconnect": {
        "es": "Desconectar", "eu": "Deskonektatu", "fr": "Déconnecter",
    },
    "Help": {
        "es": "Ayuda", "eu": "Laguntza", "fr": "Aide",
    },
    "About": {
        "es": "Acerca de", "eu": "Honi buruz", "fr": "À propos",
    },
    # Tabs
    "Dashboard": {
        "es": "Panel", "eu": "Panela", "fr": "Tableau de bord",
    },
    "Monitor": {
        "es": "Monitor", "eu": "Monitorea", "fr": "Moniteur",
    },
    "Scanner": {
        "es": "Escáner", "eu": "Eskánerra", "fr": "Scanner",
    },
    "Configuration": {
        "es": "Configuración", "eu": "Konfigurazioa", "fr": "Configuration",
    },
    # Connection panel
    "Disconnected": {
        "es": "Desconectado", "eu": "Deskonektatuta", "fr": "Déconnecté",
    },
    "Connected": {
        "es": "Conectado", "eu": "Konektatuta", "fr": "Connecté",
    },
    "Serial RTU": {
        "es": "Serie RTU", "eu": "Serie RTU", "fr": "Série RTU",
    },
    "Modbus TCP": {
        "es": "Modbus TCP", "eu": "Modbus TCP", "fr": "Modbus TCP",
    },
    "Port:": {
        "es": "Puerto:", "eu": "Portua:", "fr": "Port :",
    },
    "Refresh": {
        "es": "Actualizar", "eu": "Eguneratu", "fr": "Actualiser",
    },
    "Baud Rate:": {
        "es": "Velocidad:", "eu": "Abiadura:", "fr": "Débit :",
    },
    "Parity:": {
        "es": "Paridad:", "eu": "Parekotasuna:", "fr": "Parité :",
    },
    "None (N)": {
        "es": "Ninguna (N)", "eu": "Bat ere ez (N)", "fr": "Aucune (N)",
    },
    "Even (E)": {
        "es": "Par (E)", "eu": "Bikoitia (E)", "fr": "Paire (E)",
    },
    "Odd (O)": {
        "es": "Impar (O)", "eu": "Bakoitia (O)", "fr": "Impaire (O)",
    },
    "Data Bits:": {
        "es": "Bits de datos:", "eu": "Datu bitak:", "fr": "Bits de données :",
    },
    "Stop Bits:": {
        "es": "Bits de parada:", "eu": "Geldiune bitak:", "fr": "Bits d'arrêt :",
    },
    "Timeout:": {
        "es": "Tiempo de espera:", "eu": "Itxaron-denbora:", "fr": "Délai d'attente :",
    },
    "Host/IP:": {
        "es": "Host/IP:", "eu": "Host/IP:", "fr": "Hôte/IP :",
    },
    "Device Profile": {
        "es": "Perfil de dispositivo", "eu": "Gailu profila", "fr": "Profil d'appareil",
    },
    "(No profile - Generic)": {
        "es": "(Sin perfil - Genérico)", "eu": "(Profilik gabe - Generikoa)", "fr": "(Pas de profil - Générique)",
    },
    "Select a profile to auto-configure parameters": {
        "es": "Selecciona un perfil para configurar automáticamente",
        "eu": "Hautatu profil bat automatikoki konfiguratzeko",
        "fr": "Sélectionnez un profil pour configurer automatiquement",
    },
    "Apply Defaults": {
        "es": "Aplicar valores por defecto", "eu": "Lehenetsiak aplikatu", "fr": "Appliquer les valeurs par défaut",
    },
    "New Profile...": {
        "es": "Nuevo perfil...", "eu": "Profil berria...", "fr": "Nouveau profil...",
    },
    "Target Device": {
        "es": "Dispositivo destino", "eu": "Helburu gailua", "fr": "Appareil cible",
    },
    "Slave Address:": {
        "es": "Dirección del esclavo:", "eu": "Esklabo helbidea:", "fr": "Adresse esclave :",
    },
    "(No ports found)": {
        "es": "(No se encontraron puertos)", "eu": "(Ez da porturik aurkitu)", "fr": "(Aucun port trouvé)",
    },
    "No port selected": {
        "es": "No se ha seleccionado puerto", "eu": "Ez da porturik hautatu", "fr": "Aucun port sélectionné",
    },
    "Connection Failed": {
        "es": "Conexión fallida", "eu": "Konexioa huts egin du", "fr": "Échec de connexion",
    },
    # Status bar
    "Ready — Select a port and connect to start": {
        "es": "Listo — Selecciona un puerto y conecta para empezar",
        "eu": "Prest — Hautatu portu bat eta konektatu hasteko",
        "fr": "Prêt — Sélectionnez un port et connectez-vous pour commencer",
    },
    "Profiles reloaded": {
        "es": "Perfiles recargados", "eu": "Profilak birkargatuta", "fr": "Profils rechargés",
    },
    "New profile created and loaded": {
        "es": "Nuevo perfil creado y cargado", "eu": "Profil berria sortu eta kargatu da", "fr": "Nouveau profil créé et chargé",
    },
    "Error": {
        "es": "Error", "eu": "Errorea", "fr": "Erreur",
    },
    # Dashboard
    "Read Sensor Data": {
        "es": "Leer datos del sensor", "eu": "Sentsoreko datuak irakurri", "fr": "Lire les données du capteur",
    },
    "Read Device Config": {
        "es": "Leer configuración", "eu": "Konfigurazioa irakurri", "fr": "Lire la configuration",
    },
    "Auto-Read": {
        "es": "Lectura automática", "eu": "Irakurketa automatikoa", "fr": "Lecture automatique",
    },
    "Stop Auto-Read": {
        "es": "Detener lectura automática", "eu": "Irakurketa automatikoa gelditu", "fr": "Arrêter la lecture automatique",
    },
    "Interval:": {
        "es": "Intervalo:", "eu": "Tartea:", "fr": "Intervalle :",
    },
    "Activity Log": {
        "es": "Registro de actividad", "eu": "Jarduera erregistroa", "fr": "Journal d'activité",
    },
    "Clear": {
        "es": "Limpiar", "eu": "Garbitu", "fr": "Effacer",
    },
    "No profile selected": {
        "es": "No se ha seleccionado perfil", "eu": "Ez da profilik hautatu", "fr": "Aucun profil sélectionné",
    },
    "Select a device profile to see sensor values": {
        "es": "Selecciona un perfil de dispositivo para ver los valores del sensor",
        "eu": "Hautatu gailu profil bat sentsorearen balioak ikusteko",
        "fr": "Sélectionnez un profil d'appareil pour voir les valeurs du capteur",
    },
    "Not connected": {
        "es": "No conectado", "eu": "Konektatu gabe", "fr": "Non connecté",
    },
    "waiting...": {
        "es": "esperando...", "eu": "itxaroten...", "fr": "en attente...",
    },
    # Scanner
    "Bus Scanner": {
        "es": "Escáner de bus", "eu": "Bus eskánerra", "fr": "Scanner de bus",
    },
    "Address Range": {
        "es": "Rango de direcciones", "eu": "Helbide tartea", "fr": "Plage d'adresses",
    },
    "From:": {
        "es": "Desde:", "eu": "Hemendik:", "fr": "De :",
    },
    "To:": {
        "es": "Hasta:", "eu": "Honaino:", "fr": "À :",
    },
    "Baud Rates": {
        "es": "Velocidades", "eu": "Abiadurak", "fr": "Débits",
    },
    "Parities": {
        "es": "Paridades", "eu": "Parekotasunak", "fr": "Parités",
    },
    "Start Scan": {
        "es": "Iniciar escaneo", "eu": "Eskaneatu hasi", "fr": "Démarrer le scan",
    },
    "Stop": {
        "es": "Detener", "eu": "Gelditu", "fr": "Arrêter",
    },
    "Auto-Detect Baud Rate": {
        "es": "Auto-detectar velocidad", "eu": "Abiadura auto-detektatu", "fr": "Auto-détecter le débit",
    },
    "Auto-Detect": {
        "es": "Auto-detectar", "eu": "Auto-detektatu", "fr": "Auto-détecter",
    },
    "Devices Found": {
        "es": "Dispositivos encontrados", "eu": "Aurkitutako gailuak", "fr": "Appareils trouvés",
    },
    "Address": {
        "es": "Dirección", "eu": "Helbidea", "fr": "Adresse",
    },
    "Baud Rate": {
        "es": "Velocidad", "eu": "Abiadura", "fr": "Débit",
    },
    "Parity": {
        "es": "Paridad", "eu": "Parekotasuna", "fr": "Parité",
    },
    # Monitor
    "Manual Read": {
        "es": "Lectura manual", "eu": "Eskuzko irakurketa", "fr": "Lecture manuelle",
    },
    "Function:": {
        "es": "Función:", "eu": "Funtzioa:", "fr": "Fonction :",
    },
    "Start Address:": {
        "es": "Dirección inicial:", "eu": "Hasierako helbidea:", "fr": "Adresse de départ :",
    },
    "Count:": {
        "es": "Cantidad:", "eu": "Kopurua:", "fr": "Nombre :",
    },
    "Format:": {
        "es": "Formato:", "eu": "Formatua:", "fr": "Format :",
    },
    "Read Once": {
        "es": "Leer una vez", "eu": "Behin irakurri", "fr": "Lire une fois",
    },
    "Start Polling": {
        "es": "Iniciar sondeo", "eu": "Galdeketa hasi", "fr": "Démarrer le sondage",
    },
    "Stop Polling": {
        "es": "Detener sondeo", "eu": "Galdeketa gelditu", "fr": "Arrêter le sondage",
    },
    "Read Profile Registers": {
        "es": "Leer registros del perfil", "eu": "Profilaren erregistroak irakurri", "fr": "Lire les registres du profil",
    },
    "Results": {
        "es": "Resultados", "eu": "Emaitzak", "fr": "Résultats",
    },
    "Data Log": {
        "es": "Registro de datos", "eu": "Datu erregistroa", "fr": "Journal de données",
    },
    "Raw Frames (TX/RX)": {
        "es": "Tramas raw (TX/RX)", "eu": "Trama gordinak (TX/RX)", "fr": "Trames brutes (TX/RX)",
    },
    "Export CSV": {
        "es": "Exportar CSV", "eu": "CSV esportatu", "fr": "Exporter CSV",
    },
    "Register": {
        "es": "Registro", "eu": "Erregistroa", "fr": "Registre",
    },
    "Name": {
        "es": "Nombre", "eu": "Izena", "fr": "Nom",
    },
    "Raw (dec)": {
        "es": "Crudo (dec)", "eu": "Gordina (dec)", "fr": "Brut (déc)",
    },
    "Raw (hex)": {
        "es": "Crudo (hex)", "eu": "Gordina (hex)", "fr": "Brut (hex)",
    },
    "Formatted": {
        "es": "Formateado", "eu": "Formateatua", "fr": "Formaté",
    },
    "Unit": {
        "es": "Unidad", "eu": "Unitatea", "fr": "Unité",
    },
    "Timestamp": {
        "es": "Marca de tiempo", "eu": "Denbora-marka", "fr": "Horodatage",
    },
    # Config tab
    "Profile Registers": {
        "es": "Registros del perfil", "eu": "Profilaren erregistroak", "fr": "Registres du profil",
    },
    "Generic Read/Write": {
        "es": "Lectura/escritura genérica", "eu": "Irakurketa/idazketa generikoa", "fr": "Lecture/écriture générique",
    },
    "Batch Operations": {
        "es": "Operaciones por lotes", "eu": "Sorta eragiketak", "fr": "Opérations par lots",
    },
    "Read": {
        "es": "Leer", "eu": "Irakurri", "fr": "Lire",
    },
    "Write": {
        "es": "Escribir", "eu": "Idatzi", "fr": "Écrire",
    },
    "Value:": {
        "es": "Valor:", "eu": "Balioa:", "fr": "Valeur :",
    },
    "Write Single Register (FC06)": {
        "es": "Escribir registro único (FC06)", "eu": "Erregistro bakarra idatzi (FC06)", "fr": "Écrire registre unique (FC06)",
    },
    "Write Multiple Registers (FC16)": {
        "es": "Escribir múltiples registros (FC16)", "eu": "Erregistro anitz idatzi (FC16)", "fr": "Écrire registres multiples (FC16)",
    },
    "Write Coil (FC05)": {
        "es": "Escribir bobina (FC05)", "eu": "Harilka idatzi (FC05)", "fr": "Écrire bobine (FC05)",
    },
    "Assign Next Address": {
        "es": "Asignar siguiente dirección", "eu": "Hurrengo helbidea esleitu", "fr": "Attribuer l'adresse suivante",
    },
    "Read Current Config": {
        "es": "Leer configuración actual", "eu": "Oraingo konfigurazioa irakurri", "fr": "Lire la configuration actuelle",
    },
    "Current Address:": {
        "es": "Dirección actual:", "eu": "Oraingo helbidea:", "fr": "Adresse actuelle :",
    },
    "Next Address:": {
        "es": "Siguiente dirección:", "eu": "Hurrengo helbidea:", "fr": "Adresse suivante :",
    },
    # Profile wizard
    "New Device Profile": {
        "es": "Nuevo perfil de dispositivo", "eu": "Gailu profil berria", "fr": "Nouveau profil d'appareil",
    },
    "Device Information": {
        "es": "Información del dispositivo", "eu": "Gailuaren informazioa", "fr": "Informations sur l'appareil",
    },
    "Data Registers": {
        "es": "Registros de datos", "eu": "Datu erregistroak", "fr": "Registres de données",
    },
    "Configuration Registers": {
        "es": "Registros de configuración", "eu": "Konfigurazio erregistroak", "fr": "Registres de configuration",
    },
    "Review & Save": {
        "es": "Revisar y guardar", "eu": "Berrikusi eta gorde", "fr": "Vérifier et enregistrer",
    },
    "Device Name:": {
        "es": "Nombre del dispositivo:", "eu": "Gailuaren izena:", "fr": "Nom de l'appareil :",
    },
    "Manufacturer:": {
        "es": "Fabricante:", "eu": "Fabrikatzailea:", "fr": "Fabricant :",
    },
    "Description:": {
        "es": "Descripción:", "eu": "Deskribapena:", "fr": "Description :",
    },
    "Communication Defaults": {
        "es": "Valores de comunicación por defecto", "eu": "Komunikazio lehenetsiak", "fr": "Paramètres de communication par défaut",
    },
    "Default Address:": {
        "es": "Dirección por defecto:", "eu": "Helbide lehenetsia:", "fr": "Adresse par défaut :",
    },
    "Default Baud Rate:": {
        "es": "Velocidad por defecto:", "eu": "Abiadura lehenetsia:", "fr": "Débit par défaut :",
    },
    "Default Parity:": {
        "es": "Paridad por defecto:", "eu": "Parekotasun lehenetsia:", "fr": "Parité par défaut :",
    },
    "Add Register": {
        "es": "Añadir registro", "eu": "Erregistroa gehitu", "fr": "Ajouter un registre",
    },
    "Edit": {
        "es": "Editar", "eu": "Editatu", "fr": "Modifier",
    },
    "Duplicate": {
        "es": "Duplicar", "eu": "Bikoiztu", "fr": "Dupliquer",
    },
    "Remove": {
        "es": "Eliminar", "eu": "Kendu", "fr": "Supprimer",
    },
    "Quick Add: Device Address": {
        "es": "Añadir rápido: Dirección", "eu": "Gehitu azkarra: Helbidea", "fr": "Ajout rapide : Adresse",
    },
    "Quick Add: Baud Rate": {
        "es": "Añadir rápido: Velocidad", "eu": "Gehitu azkarra: Abiadura", "fr": "Ajout rapide : Débit",
    },
    "Save Profile": {
        "es": "Guardar perfil", "eu": "Profila gorde", "fr": "Enregistrer le profil",
    },
    # Settings / Language
    "Settings": {
        "es": "Ajustes", "eu": "Ezarpenak", "fr": "Paramètres",
    },
    "Language": {
        "es": "Idioma", "eu": "Hizkuntza", "fr": "Langue",
    },
    "Language changed. Restart the application to apply.": {
        "es": "Idioma cambiado. Reinicia la aplicación para aplicar.",
        "eu": "Hizkuntza aldatuta. Berrabiarazi aplikazioa aldaketak aplikatzeko.",
        "fr": "Langue modifiée. Redémarrez l'application pour appliquer.",
    },
    "Restart Required": {
        "es": "Reinicio necesario", "eu": "Berrabiaraztea beharrezkoa", "fr": "Redémarrage requis",
    },
    # Scanner extra
    "Bus Scan — Find Devices": {
        "es": "Escaneo de bus — Buscar dispositivos",
        "eu": "Bus eskaneoa — Gailuak bilatu",
        "fr": "Scan du bus — Rechercher des appareils",
    },
    "Ready to scan": {
        "es": "Listo para escanear", "eu": "Eskaneatzeko prest", "fr": "Prêt à scanner",
    },
    "Clear Results": {
        "es": "Limpiar resultados", "eu": "Emaitzak garbitu", "fr": "Effacer les résultats",
    },
    "Scanning...": {
        "es": "Escaneando...", "eu": "Eskaneatzen...", "fr": "Scan en cours...",
    },
    "Stopping...": {
        "es": "Deteniendo...", "eu": "Gelditzen...", "fr": "Arrêt en cours...",
    },
    "Scan complete": {
        "es": "Escaneo completado", "eu": "Eskaneoa osatuta", "fr": "Scan terminé",
    },
    "device(s) found": {
        "es": "dispositivo(s) encontrado(s)", "eu": "gailu aurkituta", "fr": "appareil(s) trouvé(s)",
    },
    "Detecting...": {
        "es": "Detectando...", "eu": "Detektatzen...", "fr": "Détection...",
    },
    "Found": {
        "es": "Encontrado", "eu": "Aurkituta", "fr": "Trouvé",
    },
    "No Port": {
        "es": "Sin puerto", "eu": "Porturik ez", "fr": "Pas de port",
    },
    "Select a serial port before scanning.": {
        "es": "Selecciona un puerto serie antes de escanear.",
        "eu": "Hautatu serie portu bat eskaneatu aurretik.",
        "fr": "Sélectionnez un port série avant de scanner.",
    },
    "Select at least one baud rate!": {
        "es": "Selecciona al menos una velocidad!",
        "eu": "Hautatu gutxienez abiadura bat!",
        "fr": "Sélectionnez au moins un débit !",
    },
    "Register 0 Value": {
        "es": "Valor registro 0", "eu": "0 erregistroaren balioa", "fr": "Valeur registre 0",
    },
    "Type": {
        "es": "Tipo", "eu": "Mota", "fr": "Type",
    },
    # Monitor extra
    "Register Read": {
        "es": "Lectura de registros", "eu": "Erregistro irakurketa", "fr": "Lecture de registres",
    },
    "Log entries": {
        "es": "Entradas del registro", "eu": "Erregistro sarrerak", "fr": "Entrées du journal",
    },
    "Clear Log": {
        "es": "Limpiar registro", "eu": "Erregistroa garbitu", "fr": "Effacer le journal",
    },
    "READ ERROR": {
        "es": "ERROR DE LECTURA", "eu": "IRAKURKETA ERROREA", "fr": "ERREUR DE LECTURE",
    },
    "No data to export": {
        "es": "No hay datos para exportar", "eu": "Ez dago daturik esportatzeko", "fr": "Pas de données à exporter",
    },
    # Config extra
    "Confirm Write": {
        "es": "Confirmar escritura", "eu": "Idazketa berretsi", "fr": "Confirmer l'écriture",
    },
    "You are about to write to a device register.": {
        "es": "Vas a escribir en un registro del dispositivo.",
        "eu": "Gailuaren erregistro batean idatziko duzu.",
        "fr": "Vous allez écrire dans un registre de l'appareil.",
    },
    "Current value": {
        "es": "Valor actual", "eu": "Oraingo balioa", "fr": "Valeur actuelle",
    },
    "New value": {
        "es": "Nuevo valor", "eu": "Balio berria", "fr": "Nouvelle valeur",
    },
    "Read All Configuration": {
        "es": "Leer toda la configuración", "eu": "Konfigurazio guztia irakurri", "fr": "Lire toute la configuration",
    },
    "Success": {
        "es": "Éxito", "eu": "Arrakasta", "fr": "Succès",
    },
    "Partial Success": {
        "es": "Éxito parcial", "eu": "Arrakasta partziala", "fr": "Succès partiel",
    },
    "Write Failed": {
        "es": "Escritura fallida", "eu": "Idazketak huts egin du", "fr": "Échec de l'écriture",
    },
    "Baud rate changed": {
        "es": "Velocidad cambiada", "eu": "Abiadura aldatuta", "fr": "Débit modifié",
    },
    "Serial port reconnected automatically.": {
        "es": "Puerto serie reconectado automáticamente.",
        "eu": "Serie portua automatikoki berkonektatu da.",
        "fr": "Port série reconnecté automatiquement.",
    },
    "Baud rate written, but reconnect failed": {
        "es": "Velocidad escrita, pero la reconexión falló",
        "eu": "Abiadura idatzita, baina berkonexioak huts egin du",
        "fr": "Débit écrit, mais la reconnexion a échoué",
    },
    "Device address changed": {
        "es": "Dirección del dispositivo cambiada",
        "eu": "Gailuaren helbidea aldatuta",
        "fr": "Adresse de l'appareil modifiée",
    },
    "Register Address:": {
        "es": "Dirección del registro:", "eu": "Erregistroaren helbidea:", "fr": "Adresse du registre :",
    },
    "Value (dec):": {
        "es": "Valor (dec):", "eu": "Balioa (dec):", "fr": "Valeur (déc) :",
    },
    "Value (hex):": {
        "es": "Valor (hex):", "eu": "Balioa (hex):", "fr": "Valeur (hex) :",
    },
    "Write Register": {
        "es": "Escribir registro", "eu": "Erregistroa idatzi", "fr": "Écrire registre",
    },
    "Write Registers": {
        "es": "Escribir registros", "eu": "Erregistroak idatzi", "fr": "Écrire registres",
    },
    "Write Coil": {
        "es": "Escribir bobina", "eu": "Harilka idatzi", "fr": "Écrire bobine",
    },
    "Coil Address:": {
        "es": "Dirección de bobina:", "eu": "Harilka helbidea:", "fr": "Adresse de bobine :",
    },
    "Values:": {
        "es": "Valores:", "eu": "Balioak:", "fr": "Valeurs :",
    },
    "Write Log": {
        "es": "Registro de escritura", "eu": "Idazketa erregistroa", "fr": "Journal d'écriture",
    },
    "Operation Log": {
        "es": "Registro de operaciones", "eu": "Eragiketa erregistroa", "fr": "Journal d'opérations",
    },
    "Batch Address Assignment": {
        "es": "Asignación de direcciones por lotes",
        "eu": "Helbideen sorta esleipena",
        "fr": "Attribution d'adresses par lots",
    },
    "Assign unique addresses to multiple identical devices.": {
        "es": "Asigna direcciones únicas a múltiples dispositivos idénticos.",
        "eu": "Esleitu helbide bakarrak gailu identiko anitzei.",
        "fr": "Attribuez des adresses uniques à plusieurs appareils identiques.",
    },
    "Connect one device at a time.": {
        "es": "Conecta un dispositivo a la vez.",
        "eu": "Konektatu gailu bat aldi bakoitzean.",
        "fr": "Connectez un appareil à la fois.",
    },
    "Batch Configuration": {
        "es": "Configuración por lotes", "eu": "Sorta konfigurazioa", "fr": "Configuration par lots",
    },
    "Keep current": {
        "es": "Mantener actual", "eu": "Oraingoa mantendu", "fr": "Garder l'actuel",
    },
    "Target baud rate:": {
        "es": "Velocidad objetivo:", "eu": "Helburu abiadura:", "fr": "Débit cible :",
    },
    "Reading configuration from device": {
        "es": "Leyendo configuración del dispositivo",
        "eu": "Gailuaren konfigurazioa irakurtzen",
        "fr": "Lecture de la configuration de l'appareil",
    },
    "Address changed": {
        "es": "Dirección cambiada", "eu": "Helbidea aldatuta", "fr": "Adresse modifiée",
    },
    "Ready for next device.": {
        "es": "Listo para el siguiente dispositivo.",
        "eu": "Hurrengo gailurako prest.",
        "fr": "Prêt pour l'appareil suivant.",
    },
    "Confirm Address Change": {
        "es": "Confirmar cambio de dirección",
        "eu": "Helbide aldaketa berretsi",
        "fr": "Confirmer le changement d'adresse",
    },
    "Change device address from": {
        "es": "Cambiar dirección del dispositivo de",
        "eu": "Aldatu gailuaren helbidea hemendik",
        "fr": "Changer l'adresse de l'appareil de",
    },
    "Current and new address are the same!": {
        "es": "La dirección actual y la nueva son iguales!",
        "eu": "Oraingo eta helbide berria berdinak dira!",
        "fr": "L'adresse actuelle et la nouvelle sont identiques !",
    },
    "All attempts failed. Load a device profile.": {
        "es": "Todos los intentos fallaron. Carga un perfil.",
        "eu": "Saiakera guztiek huts egin dute. Kargatu profil bat.",
        "fr": "Tous les essais ont échoué. Chargez un profil.",
    },
    "Device Address": {
        "es": "Dirección del dispositivo", "eu": "Gailu helbidea", "fr": "Adresse de l'appareil",
    },
    # Profile wizard extra
    "New Device Profile Wizard": {
        "es": "Asistente de nuevo perfil", "eu": "Profil berriaren morroia", "fr": "Assistant nouveau profil",
    },
    "Enter the basic information about the device. Check the device manual or datasheet.": {
        "es": "Introduce la información básica del dispositivo. Consulta el manual.",
        "eu": "Sartu gailuaren oinarrizko informazioa. Kontsultatu eskuliburua.",
        "fr": "Entrez les informations de base de l'appareil. Consultez le manuel.",
    },
    "Factory default values for new devices.": {
        "es": "Valores de fábrica para dispositivos nuevos.",
        "eu": "Fabrikako balio lehenetsiak gailu berrietarako.",
        "fr": "Valeurs d'usine par défaut pour les nouveaux appareils.",
    },
    "Add the registers that contain sensor measurements.": {
        "es": "Añade los registros con las mediciones del sensor.",
        "eu": "Gehitu sentsorearen neurketen erregistroak.",
        "fr": "Ajoutez les registres contenant les mesures du capteur.",
    },
    "Add the registers used to configure the device.": {
        "es": "Añade los registros usados para configurar el dispositivo.",
        "eu": "Gehitu gailua konfiguratzeko erregistroak.",
        "fr": "Ajoutez les registres utilisés pour configurer l'appareil.",
    },
    "Data registers contain the sensor measurements.\nCheck the manual for register addresses.": {
        "es": "Los registros de datos contienen las mediciones.\nConsulta el manual para las direcciones.",
        "eu": "Datu erregistroek neurketak dituzte.\nKontsultatu eskuliburua helbideetarako.",
        "fr": "Les registres de données contiennent les mesures.\nConsultez le manuel pour les adresses.",
    },
    "Config registers control device settings.\nThe most common are device address and baud rate.": {
        "es": "Los registros de configuración controlan los ajustes.\nLos más comunes: dirección y velocidad.",
        "eu": "Konfigurazio erregistroek ezarpenak kontrolatzen dituzte.\nOhikoenak: helbidea eta abiadura.",
        "fr": "Les registres de config contrôlent les paramètres.\nLes plus courants : adresse et débit.",
    },
    "Quick Add Common Registers": {
        "es": "Añadir registros comunes", "eu": "Erregistro ohikoak gehitu", "fr": "Ajouter des registres courants",
    },
    "Edit Register": {
        "es": "Editar registro", "eu": "Erregistroa editatu", "fr": "Modifier le registre",
    },
    "Remove Register": {
        "es": "Eliminar registro", "eu": "Erregistroa kendu", "fr": "Supprimer le registre",
    },
    "Name:": {
        "es": "Nombre:", "eu": "Izena:", "fr": "Nom :",
    },
    "Unit:": {
        "es": "Unidad:", "eu": "Unitatea:", "fr": "Unité :",
    },
    "Data type:": {
        "es": "Tipo de dato:", "eu": "Datu mota:", "fr": "Type de données :",
    },
    "Scale factor:": {
        "es": "Factor de escala:", "eu": "Eskala faktorea:", "fr": "Facteur d'échelle :",
    },
    "e.g. 0.1 means raw 235 = 23.5": {
        "es": "ej. 0.1 significa que 235 = 23.5",
        "eu": "adib. 0.1 esan nahi du 235 = 23.5",
        "fr": "ex. 0.1 signifie que brut 235 = 23.5",
    },
    "Access:": {
        "es": "Acceso:", "eu": "Sarbidea:", "fr": "Accès :",
    },
    "Read function:": {
        "es": "Función de lectura:", "eu": "Irakurketa funtzioa:", "fr": "Fonction de lecture :",
    },
    "Write function:": {
        "es": "Función de escritura:", "eu": "Idazketa funtzioa:", "fr": "Fonction d'écriture :",
    },
    "Limit values": {
        "es": "Limitar valores", "eu": "Balioak mugatu", "fr": "Limiter les valeurs",
    },
    "Value range:": {
        "es": "Rango de valores:", "eu": "Balio tartea:", "fr": "Plage de valeurs :",
    },
    "Has value mapping (e.g. 1=1200 baud, 2=2400...)": {
        "es": "Tiene mapa de valores (ej. 1=1200 baud, 2=2400...)",
        "eu": "Balio mapa du (adib. 1=1200 baud, 2=2400...)",
        "fr": "A un mappage de valeurs (ex. 1=1200 baud, 2=2400...)",
    },
    "Value mapping:": {
        "es": "Mapa de valores:", "eu": "Balio mapa:", "fr": "Mappage de valeurs :",
    },
    "Register Value": {
        "es": "Valor del registro", "eu": "Erregistroaren balioa", "fr": "Valeur du registre",
    },
    "Meaning": {
        "es": "Significado", "eu": "Esanahia", "fr": "Signification",
    },
    "Add Mapping": {
        "es": "Añadir mapeo", "eu": "Mapaketa gehitu", "fr": "Ajouter un mappage",
    },
    "Remove Selected": {
        "es": "Eliminar seleccionado", "eu": "Hautatutakoa kendu", "fr": "Supprimer la sélection",
    },
    "Enter a register name.": {
        "es": "Introduce un nombre de registro.",
        "eu": "Sartu erregistroaren izena.",
        "fr": "Entrez un nom de registre.",
    },
    "Scale": {
        "es": "Escala", "eu": "Eskala", "fr": "Échelle",
    },
    "Review the generated profile. Click 'Finish' to save.": {
        "es": "Revisa el perfil generado. Pulsa 'Finalizar' para guardar.",
        "eu": "Berrikusi sortutako profila. Sakatu 'Amaitu' gordetzeko.",
        "fr": "Vérifiez le profil généré. Cliquez sur 'Terminer' pour enregistrer.",
    },
    "Save as": {
        "es": "Guardar como", "eu": "Gorde honela", "fr": "Enregistrer sous",
    },
    "auto-generated from device name": {
        "es": "generado automáticamente del nombre", "eu": "izenetik automatikoki sortua", "fr": "généré automatiquement",
    },
    "Enter a filename.": {
        "es": "Introduce un nombre de archivo.", "eu": "Sartu fitxategi izena.", "fr": "Entrez un nom de fichier.",
    },
    "File Exists": {
        "es": "El archivo existe", "eu": "Fitxategia existitzen da", "fr": "Le fichier existe",
    },
    "already exists. Overwrite?": {
        "es": "ya existe. ¿Sobrescribir?", "eu": "dagoeneko existitzen da. Gainidatzi?", "fr": "existe déjà. Écraser ?",
    },
    "Profile Saved": {
        "es": "Perfil guardado", "eu": "Profila gordeta", "fr": "Profil enregistré",
    },
    "Profile saved to": {
        "es": "Perfil guardado en", "eu": "Profila hemen gordeta", "fr": "Profil enregistré dans",
    },
    "Save failed": {
        "es": "Error al guardar", "eu": "Gordetze errorea", "fr": "Échec de l'enregistrement",
    },
}


def tr(text: str) -> str:
    """Translate a string to the current language."""
    if _current_lang == "en":
        return text
    entry = _STRINGS.get(text)
    if entry and _current_lang in entry:
        return entry[_current_lang]
    return text


def set_language(lang: str):
    """Set the current language code (en, es, eu, fr)."""
    global _current_lang
    if lang in LANGUAGES:
        _current_lang = lang


def get_language() -> str:
    """Get the current language code."""
    return _current_lang


def _settings_path() -> str:
    config_dir = os.path.expanduser("~/.config/modbustool")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.json")


def load_language():
    """Load saved language preference."""
    global _current_lang
    try:
        with open(_settings_path(), "r") as f:
            data = json.load(f)
            lang = data.get("language", "en")
            if lang in LANGUAGES:
                _current_lang = lang
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def save_language(lang: str):
    """Save language preference."""
    path = _settings_path()
    data = {}
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    data["language"] = lang
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
