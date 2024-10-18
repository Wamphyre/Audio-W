# Audio-W

Audio-W es un reproductor de audio ligero y elegante desarrollado en Python, diseñado para ofrecer una experiencia de usuario fluida y agradable.

## Características

- Interfaz gráfica intuitiva y moderna con tema oscuro
- Reproducción de archivos de audio en formatos MP3, WAV y FLAC
- Lista de reproducción con función de arrastrar y soltar
- Ordenamiento automático de canciones por número de pista para el mismo álbum y artista
- Visualización mejorada de la canción actualmente en reproducción
- Barra de progreso interactiva
- Controles de reproducción (play, pause, stop, anterior, siguiente)
- Visualización de metadatos (título, artista, álbum)
- Cálculo y visualización de la duración total de la playlist
- Asociación de archivos de audio (opcional durante la instalación)
- Sistema de instancia única para evitar múltiples copias en ejecución

## Requisitos del sistema

- Windows 7 o superior
- Python 3.7 o superior (solo para desarrollo)

## Instalación

### Para usuarios

1. Descarga el instalador más reciente `Audio-W-1.3-Setup.exe` desde la [página de releases](https://github.com/Wamphyre/Audio-W/releases).
2. Ejecuta el instalador y sigue las instrucciones en pantalla.
3. Opcionalmente, selecciona la opción para asociar archivos de audio durante la instalación.

### Para desarrolladores

1. Clona el repositorio:
   ```
   git clone https://github.com/Wamphyre/Audio-W.git
   ```
2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

## Uso

1. Inicia Audio-W desde el acceso directo creado durante la instalación o ejecutando `Audio-W.exe`.
2. Arrastra y suelta archivos de audio en la interfaz para añadirlos a la lista de reproducción.
3. Utiliza los controles de reproducción para gestionar la reproducción de audio.
4. Reordena las canciones en la playlist arrastrándolas a la posición deseada.
5. Haz doble clic en una canción de la playlist para reproducirla inmediatamente.

## Desarrollo

Para ejecutar la aplicación en modo de desarrollo:

```
python audio_w.py
```

Para compilar la aplicación:

1. Asegúrate de tener PyInstaller instalado:
   ```
   pip install pyinstaller
   ```
2. Compila la aplicación:
   ```
   pyinstaller audio_w.spec
   ```

Para crear el instalador:

1. Instala Inno Setup.
2. Abre `installer.iss` con Inno Setup.
3. Compila el script para generar el instalador.

## Solución de problemas

Si encuentras algún problema durante la reproducción de audio, como errores de "output underflow", intenta aumentar el tamaño del buffer de audio en la configuración de la aplicación.

## Registro de cambios

### Versión 1.3
- Añadida funcionalidad de arrastrar y soltar para reordenar canciones en la playlist
- Implementado ordenamiento automático de canciones por número de pista
- Mejorada la visualización de la canción en reproducción
- Añadida visualización de artista y duración para cada tema en la playlist
- Optimizado el rendimiento general de la aplicación
- Implementado sistema de logging mejorado para facilitar la depuración

## Licencia

Este proyecto está licenciado bajo la BSD 3-Clause License - vea el archivo [LICENSE](LICENSE) para más detalles.

La BSD 3-Clause License es una licencia de software libre permisiva que permite el uso, modificación y distribución del código, tanto en proyectos de código abierto como en software propietario, siempre que se mantengan las atribuciones de copyright y la renuncia de garantía.

---

Desarrollado con ❤️ por [Wamphyre](https://github.com/Wamphyre)

Si te gusta puedes comprarme un café en https://ko-fi.com/wamphyre94078
