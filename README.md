# Clancy — edición de cumpleaños

Sitio estático en español hecho como regalo: acertijos personales, una carta desplegable, un tocadiscos interactivo y un minijuego arcade. El tocadiscos reproduce los 13 archivos MP3 de `audio/` desde el navegador; no se conecta a Spotify o YouTube Music.

## Publicar en GitHub Pages

1. Integra estos archivos en la rama `main`.
2. En **Settings → Pages**, selecciona **GitHub Actions** como fuente.
3. El workflow `.github/workflows/pages.yml` publicará el sitio después de cada cambio en `main`. También se puede iniciar manualmente desde **Actions**.

No hay proceso de compilación ni dependencias: `index.html` es el sitio y puede abrirse directamente en un navegador.

## Personalizar

Edita la carta, las respuestas de las tres pistas y las listas `clancySongs` / `dedicatedSongs` dentro de `index.html`. Las pistas solo son una interacción lúdica del lado del navegador; no brindan privacidad ni autenticación real. El repositorio incluye 13 archivos MP3 referenciados por el sitio. Antes de publicar, confirma que tienes derecho a redistribuirlos: usa solo audio propio o con licencia para redistribución pública. No se presupone que los archivos actuales tengan licencia.

## QR del sitio

Arte listo para compartir o imprimir, con alto contraste y zona de silencio:

- [QR Clancy en SVG vectorial](qr/clancy-cumpleanos.svg)
- [QR Clancy en PNG de alta resolución](qr/clancy-cumpleanos.png)

Ambos apuntan exactamente a <https://jorgealbertt.github.io/clancy-cumpleanos/>. Para regenerarlos sin dependencias de ejecución, ejecuta `python tools/generate_qr.py`.
