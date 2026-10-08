# Datos de ubicación y logística (verificación)

Verificado el 8-oct-2026. Sirve de fuente para `js/mapa.js` (constantes `CFG`), los botones «¿Cómo llegar?» y los textos de Agenda y Transporte.

**Cómo se ha verificado (y límites).** `WebFetch` está bloqueado por la política de red del entorno para todos los hosts probados (nominatim.openstreetmap.org, es/en.wikipedia.org, telpark.com, komoot.com, info.valladolid.es, turismocastillayleon.com, tripomatic.com, parclick.com, laposadadelpinar.com, bodas.net, maps.app.goo.gl…), y no se ha rodeado. Se ha trabajado con `WebSearch` (resúmenes de páginas de terceros) y con búsqueda de código en GitHub (datos abiertos ya publicados: GTFS de AUVASA, geocodificaciones Google/Nominatim de otros proyectos, JSON-LD de Patrimonio Abierto). **No se ha abierto ninguna ficha oficial ni se ha contrastado nada sobre un mapa real.** Las coordenadas llevan 5 decimales (≈ 1 m de resolución) pero su exactitud real es la indicada en «Fiabilidad».

## 1. Resumen

| Lugar | Nombre | Dirección | Lat, Lng (WGS84) | Fiabilidad |
|---|---|---|---|---|
| Ceremonia | Iglesia Conventual de San Pablo (Dominicos) | Plaza de San Pablo, 4 · 47011 Valladolid | **41.65710, -4.72442** | Alta (±25 m, 4 fuentes coherentes) |
| Celebración | La Posada Real del Pinar (también «La Posada del Pinar») | Pinar de San Rafael, s/n · 47450 Pozal de Gallinas (Valladolid) | **41.29956, -4.81734** | Media-alta (±50 m; la dirección es segura, el punto viene de portales de reservas) |
| Parking | Plaza de Portugalete (aparcamiento «IC Plaza de Portugalete») | Plaza de Portugalete · 47002 Valladolid (acceso: Plaza Portugalete 5 / Plaza de la Libertad 5, según el portal) | **41.65335, -4.72386** (centro de la plaza, no la boca del garaje) | Media-alta (±30 m; es el punto de Google Maps de la plaza) |
| Autocar de vuelta | Plaza del Poniente (Valladolid, Centro) | Plaza del Poniente · 47003 (algunas fuentes 47001) | **41.65316, -4.73128** | Media-alta para el lugar; **sin confirmar que sea la que quiere el cliente** (ver §5) |
| Zona de alojamiento | Círculo centrado en el baricentro Plaza Mayor–Catedral–San Pablo | — | **41.65423, -4.72563**, radio **900 m** | Decisión de diseño (ver §6) |

## 2. Iglesia de San Pablo

- **Nombre:** Iglesia Conventual de San Pablo (Real Convento de San Pablo, Dominicos); Bien de Interés Cultural. Dirección: Plaza de San Pablo, 4, 47011 (spain.info).
- **Coordenadas (todas dentro de ~40 m):** Wikidata Q3031934 vía Patrimonio Abierto 41.657136, -4.724425 · Tripomatic 41.657071, -4.724379 · Wikipedia ES (copia en Kiddle) 41°39′25″N 4°43′28″O · GCatholic, Plus Code 8CHQM74G+Q3 → 41.65694, -4.72481 · campaners.com 41.65667, -4.72472. Se usa 41.65710, -4.72442.
- Fuentes: <https://www.spain.info/es/lugares-interes/iglesia-san-pablo-valladolid/> · <https://patrimonioabierto.es/monumento/15900-iglesia-de-san-pablo/> · <https://gcatholic.org/churches/europe-south/53711> · <https://ninos.kiddle.co/Iglesia_de_San_Pablo_(Valladolid)>.
- No verificado: horarios, normas de acceso y si hay misa/acto antes de la ceremonia.

## 3. La Posada Real del Pinar

- **Nombre:** los portales usan «La Posada Real del Pinar» (Bodas.net, Booking) y «La Posada del Pinar» (web propia y Turismo de Castilla y León, marca «Posadas Reales»). Web oficial según los buscadores: <https://laposadadelpinar.com/> (no se ha podido abrir).
- **Dirección:** Pinar de San Rafael, s/n (Turismo CyL: «Camino Pinar de San Rafael s/n»), Pozal de Gallinas, Valladolid. Páginas Amarillas añade «Parcela 1234, Polígono 1». **Código postal: 47450** (web de la posada, Turismo CyL, Páginas Amarillas); varios portales ponen 47400 (el de Medina del Campo). Se recomienda 47450.
- **Coordenadas:** Booking/Destinia/Hotelmix 41.29965, -4.81756 (misma base) · Tripadvisor 41.29947, -4.81711 · Bodas.net lat 41.2992. Se usa la media 41.29956, -4.81734. Descartados por incoherentes: Tuscasasrurales (lng a 1,1 km) y Directorio Rural (es el pueblo, 41°19′7″N 4°50′11″O, a 2,6 km).
- **Distancias:** a Medina del Campo 5 km (Rumbo) / 8,3 km al centro (Kayak; en línea recta sale 8,2 km). El pueblo de Pozal de Gallinas queda 2,6 km al norte.
- **Desde Valladolid en coche (no verificado con ruteador):** en línea recta ≈ 40 km desde la Plaza Mayor. Las fuentes dicen «45 km» (Rumbo, hoteles.net; no se sabe si es recta), «≈ 1 h» (Amimir) y 61,9 km / 46 min a Pozal de Gallinas pueblo (distanciaentre.org). Estimación propia: **55–65 km y 45–60 min**. Para la web: «a algo menos de una hora en coche» o sin cifra; comprobar en Google Maps antes de publicar un número.
- Los listados no mencionan «palomar» (sí una capilla de los antiguos dueños, jardines de 1900 y pinar de ~130 ha). Ver `docs/contenido-original.md` sobre la ilustración del palomar.
- Salida habitual por la A-6 (salida 157, según un portal; no verificado).

## 4. Plaza de Portugalete (parking)

- **Qué es:** plaza abierta del casco histórico entre la Catedral y la iglesia de La Antigua, sobre el antiguo mercado de hierro de Portugalete (información turística municipal: <https://info.valladolid.es/en/enjoy/heritage/green-areas/squares/portugalete-and-university-squares>). Debajo está el aparcamiento público cubierto «IC Plaza de Portugalete» (abierto en 2008; 24 h; 396 plazas, 258 públicas; altura máx. 2,10–2,20 m según portal; Telpark: desde 2,10 €/h y tope diario 22,60 €. Datos de terceros, pueden estar desactualizados). Accesos según portal: «Plaza Portugalete 5» (Parclick) o «Plaza de la Libertad 5» (Telpark).
- **Coordenadas:** punto de la ficha de Google Maps «Plaza de Portugalete» 41.6533536, -4.7238626 (repo público aldeapucela/fiestas; mismo valor en un GeoJSON de Google My Maps) y 41.6532668, -4.7239288 (mismo repo, «lateral de la Catedral»). Se usa 41.65335, -4.72386.
- **¿Está a ~500 m / 5 min de San Pablo? Casi.** Distancia en línea recta: **420 m**. Andando, por el casco antiguo, ≈ 500–600 m. A paso normal son **6–8 minutos**, no 5. Texto sugerido: «a unos 500 m (6–8 minutos andando)».
- **Enlace corto del cliente** (<https://maps.app.goo.gl/a4cSyb4YTgGbtBFt9>): bloqueado, no se ha podido resolver. No se sabe si apunta a la plaza o a la boca del garaje; el cliente debería abrirlo y comprobarlo. Se mantiene tal cual en el texto de Transporte (lo pidió él); el mapa usa un enlace por nombre.

## 5. «Plaza del Poniente» (autocar de vuelta)

- **Identificada:** Plaza del Poniente, Valladolid (barrio Centro), junto al Paseo de Isabel la Católica y a unos **250 m al oeste de la Plaza Mayor**, cerca del Puente del Poniente sobre el Pisuerga. Es parque con estanque (en 2012 se montó allí el mercado provisional del Mercado del Val; documentos del Ayuntamiento en valladolid.gob.es). Direcciones con número: Plaza del Poniente 1–6, CP 47003 (BOE) / 47001 (Open Charge Map).
- **Coordenadas (4 fuentes dentro de ~100 m):** geocodificación Nominatim 41.6531571, -4.7312823 (repo aldeapucela/fiestas) · parada AUVASA «Paseo Isabel la Católica Plaza Poniente» 41.653327, -4.732088 y «Plaza Poniente frente Jorge Guillén» 41.653499, -4.731113 (GTFS de AUVASA) · calle OSM «Plaza del Poniente» 41.65362, -4.73209. Se usa 41.65316, -4.73128.
- **Ya es un nudo de autobuses:** paradas urbanas AUVASA (origen de la línea 24, según findit.city) y paradas de líneas de Arroyo de la Encomienda. Una web de boda pública de otra pareja (oct-2026) usa «Poniente» como salida de autocares hacia esta misma finca (anecdótico; no se enlaza por privacidad).
- **Otras con el mismo nombre:** existen «plaza del Poniente» en otras localidades (p. ej. Fuenlabrada, Madrid), irrelevantes. En Valladolid ciudad no se ha encontrado otra. En la provincia, la búsqueda no fue concluyente.
- **DUDA ABIERTA (preguntar al cliente):** ¿«Plaza del Poniente» es esta plaza de Valladolid Centro (Paseo de Isabel la Católica)? ¿Es de verdad donde parará el autocar de vuelta? ¿Y dónde recoge el de ida: delante de San Pablo o en otro punto? El mapa de alojamiento **no** la marca.
- URL de búsqueda: `https://www.google.com/maps/search/?api=1&query=Plaza%20del%20Poniente%2C%20Valladolid`.

## 6. Zona recomendada para alojarse (círculo del mapa)

- **Centro: 41.65423, -4.72563.** Baricentro de Plaza Mayor (41.65225, -4.72861; Google), Catedral/Plaza de Portugalete y San Pablo. Distancias al centro: San Pablo 335 m, Plaza Mayor 331 m, Plaza de Portugalete 177 m, Catedral 270 m.
- **Radio: 900 m** (≈ 11 min andando). Deja dentro, con margen, todos los puntos de la boda en la ciudad (el más lejano, la Plaza del Poniente, a 484 m) y hacia el sur llega a la zona de la Plaza de Zorrilla y el Campo Grande (aproximado, no contrastado sobre mapa). Se eligió 900 y no 1000–1100 para que el círculo entero quepa a zoom 14 en el mapa del móvil (≈ 343×304 px); en pantallas ≥ 600 px cabe a zoom 15.
- Es una recomendación visual («entorno del centro»), no un límite. El texto del cliente no fija distancia.

## 7. URLs de Google Maps (bien codificadas; no se han podido probar contra Google)

Formato oficial `api=1`. «Ruta» abre las indicaciones desde la ubicación del usuario; «Ver» abre la ficha del lugar.

| Lugar | Ruta (`dir`) | Ver (`search`) |
|---|---|---|
| Iglesia de San Pablo | `https://www.google.com/maps/dir/?api=1&destination=Iglesia%20de%20San%20Pablo%2C%20Plaza%20de%20San%20Pablo%2C%2047011%20Valladolid` | `https://www.google.com/maps/search/?api=1&query=Iglesia%20de%20San%20Pablo%2C%20Plaza%20de%20San%20Pablo%2C%2047011%20Valladolid` |
| La Posada Real del Pinar | `https://www.google.com/maps/dir/?api=1&destination=La%20Posada%20Real%20del%20Pinar%2C%20Pozal%20de%20Gallinas%2C%20Valladolid` | `https://www.google.com/maps/search/?api=1&query=La%20Posada%20Real%20del%20Pinar%2C%20Pozal%20de%20Gallinas%2C%20Valladolid` |
| Posada (por coordenadas, plan B) | `https://www.google.com/maps/dir/?api=1&destination=41.29956%2C-4.81734` | `https://www.google.com/maps/search/?api=1&query=41.29956%2C-4.81734` |
| Parking Plaza de Portugalete | `https://www.google.com/maps/dir/?api=1&destination=Parking%20Plaza%20de%20Portugalete%2C%20Valladolid` | `https://www.google.com/maps/search/?api=1&query=Parking%20Plaza%20de%20Portugalete%2C%20Valladolid` (o el enlace corto del cliente) |
| Zona / centro | — | `https://www.google.com/maps/search/?api=1&query=Plaza%20Mayor%2C%20Valladolid` · hoteles: `…&query=hoteles%20cerca%20de%20Plaza%20Mayor%2C%20Valladolid` |

En HTML, escribir `&amp;` en vez de `&`. Si Google no resolviera bien el nombre de la finca, usar la variante por coordenadas.

## 8. Dudas abiertas y lo que NO se pudo verificar

1. **Plaza del Poniente:** confirmar cuál es y si es la parada real del autocar (§5).
2. **Enlace corto del parking:** abrirlo y comprobar a qué punto lleva (§4). Si apunta a la boca del garaje, mejor usarlo como botón «¿Cómo llegar?» del parking.
3. **Tiempo en coche a la finca:** medirlo en Google Maps (hora de salida real) antes de poner una cifra (§3).
4. **Código postal de la finca:** 47450 (propio) frente a 47400 (portales).
5. Sin abrir: webs oficiales (posada, Turismo CyL, Ayuntamiento). Las coordenadas de San Pablo y de la plaza son las que más fuentes avalan; la de la finca depende de portales de reservas.
6. «5 minutos» a pie desde el parking: ajustar el texto a «unos 500 m (6–8 min)».
7. **Aspecto real de las teselas** (CARTO Positron) en el mapa: no se pudo ver (hosts externos bloqueados); se probó con teselas falsas y sin teselas.
