# Clancy — edición de cumpleaños

Sitio estático en español hecho como regalo: acertijos personales, una carta desplegable, un tocadiscos interactivo y un minijuego arcade. El tocadiscos genera una señal sintética original directamente en el navegador; no se conecta a Spotify o YouTube Music ni aloja las grabaciones comerciales del álbum.

## Publicar en GitHub Pages

1. Integra estos archivos en la rama `main`.
2. En **Settings → Pages**, selecciona **GitHub Actions** como fuente.
3. El workflow `.github/workflows/pages.yml` publicará el sitio después de cada cambio en `main`. También se puede iniciar manualmente desde **Actions**.

No hay proceso de compilación ni dependencias: `index.html` es el sitio y puede abrirse directamente en un navegador.

## Personalizar

Edita la carta, las respuestas de las tres pistas y las listas `clancySongs` / `dedicatedSongs` dentro de `index.html`. Las pistas solo son una interacción lúdica del lado del navegador, no un control de acceso. No publiques canciones comerciales, letras ni archivos LRC; cualquier audio que se añada debe ser una grabación propia o contar con licencia para redistribución pública.
