# Publicación segura — Circo Dimensional 2 v1.0.0

Destino: <https://github.com/OnRail76/Circo-Dimensional-2> (repositorio nuevo de Tony C. Ware).

El repositorio ya contiene una licencia `LICENSE` creada al abrirlo. **El script actualizado la sustituye por la licencia MIT de este paquete, preservando todo el historial de GitHub**, y sube juego, fuentes, cinco fondos, recursos sonoros, carátula, historia, atlas revisado y manual.

## Un solo comando desde Linux / Bazzite

Descomprime el paquete **GitHub completo** y abre una terminal en su carpeta `Circo-Dimensional-2`:

```bash
bash PUBLICAR_EN_GITHUB.sh OnRail76/Circo-Dimensional-2
```

El script primero comprueba todos los SHA-256, clona el repo de GitHub, confirma que no contenga archivos ajenos al proyecto, crea un único commit y lo sube a `main`. No usa `--force` ni elimina la historia anterior. Si falta autenticación, usa `gh auth login` y `gh auth setup-git` (con GitHub CLI instalado) y repite el comando.

**Importante:** no ejecutarlo sobre la carpeta de la primera edición de Circo Dimensional para Spectrum; es un juego y repositorio distintos.

## Después del push

1. En **Actions**, confirma que `Pruebas automáticas` termina con éxito.
2. Ejecuta manualmente el workflow `Compilar Circo Dimensional 2 (AppImage y EXE)` para generar binarios en Linux y Windows.
3. Tras probar los binarios, crea la Release `v1.0.0` y usa `RELEASE_NOTES.md` como descripción. Adjunta al menos el ZIP de distribución, el manual y el atlas corregido. No declares los ejecutables verificados sin comprobarlos.

El paquete incluye la totalidad de los archivos, pero no binarios AppImage o EXE ya compilados.
