# Umarti Profesionales

Directorio de profesionales independientes de Latinoamérica.
Se publica en https://profesionales.umartidigital.com (Hostinger, despliegue estático desde GitHub).

## Cómo se actualiza

1. Las fichas están en `data/profesionales.csv`, una fila por profesional.
   - `ejemplo`: `si` para fichas de muestra (llevan aviso y no se indexan), `no` para fichas reales.
   - `servicios`: separados con `|`.
   - `slug`: se puede dejar vacío y se genera solo.
2. Ejecutar `python3 tools/build.py` para regenerar el sitio (inicio, fichas en `p/`, mapa del sitio).
3. Subir los cambios a `main`.

Los contadores del inicio aparecen cuando hay 10 fichas reales o más.

## Formulario «Suma tu ficha»

`registro.php` envía cada solicitud por email, con una línea lista para pegar en el CSV.
Cambiar `DESTINO` por la casilla que recibe las solicitudes.
