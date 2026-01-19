# PP Launcher v3.1

PP Launcher es una herramienta de escritorio diseñada para sistemas basados en Debian, orientada a la gestión y centralización de accesos para la descarga de software. La aplicación funciona como un indexador dinámico que facilita la navegación y redirección hacia repositorios externos mediante una interfaz técnica optimizada.

## Descripción General

El proyecto centraliza un catálogo detallado de aplicaciones y videojuegos, permitiendo filtrar por categorías y especificaciones técnicas. Está enfocado en mejorar la accesibilidad a diferentes versiones de un mismo título, incluyendo optimizaciones para hardware con recursos limitados (versiones Lite y Super Lite).

## Características Técnicas

* **Formato de Paquete:** Distribuido como `pp-launcher_1.0_all.deb`, garantizando compatibilidad universal en arquitecturas soportadas.
* **Indexación Estructurada:** Organización por nombre, tipo de software y descripción técnica detallada.
* **Motor de Búsqueda:** Filtrado eficiente de entradas para una localización rápida en el catálogo.
* **Gestión de Redirección:** Sistema integrado para la apertura automatizada de enlaces en el navegador predeterminado.
* **Interfaz de Usuario:** Diseño de bajo impacto visual y sistémico, orientado a la eficiencia operativa.

## Requisitos del Sistema

* **Sistema Operativo:** Distribuciones basadas en Debian (Ubuntu, Linux Mint, Kali Linux, etc.).
* **Arquitectura:** Compatible con sistemas de 32 y 64 bits (arquitectura `all`).
* **Conectividad:** Acceso a internet para la funcionalidad de redirección de enlaces externos.

## Instalación y Uso

### Instalación vía Terminal

Para realizar una instalación correcta gestionando automáticamente las dependencias, utilice el siguiente comando desde el directorio donde se encuentre el archivo:

```bash
sudo apt install ./pp-launcher_1.0_all.deb
