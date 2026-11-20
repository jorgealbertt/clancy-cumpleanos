# Clancy — edición de cumpleaños

Sitio estático en español hecho como regalo: pistas personales, una carta y enlaces para escuchar música en servicios oficiales. No aloja música ni carga reproductores de terceros automáticamente; cada botón abre una búsqueda en Spotify o YouTube Music cuando la persona decide escuchar.

## Publicar en GitHub Pages

1. Integra estos archivos en la rama `main`.
2. En **Settings → Pages**, selecciona **GitHub Actions** como fuente.
3. El workflow `.github/workflows/pages.yml` publicará el sitio después de cada cambio en `main`. También se puede iniciar manualmente desde **Actions**.

No hay proceso de compilación ni dependencias: `index.html` es el sitio y puede abrirse directamente en un navegador.

## Personalizar

Edita la carta, las respuestas de las tres pistas y las listas `clancySongs` / `dedicatedSongs` dentro de `index.html`. Las pistas solo son una interacción lúdica del lado del navegador, no un control de acceso.
