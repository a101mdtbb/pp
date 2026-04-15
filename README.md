# PP Launcher v3.1

PP Launcher is a desktop tool designed for Debian-based systems, focused on managing and centralizing access points for software downloads. The application functions as a dynamic indexer that facilitates navigation and redirection to external repositories through an optimized technical interface.

## General Description

The project centralizes a detailed catalog of applications and video games, allowing users to filter by category and technical specifications.

## Technical Features

* **Package Format:** Distributed as `pp-launcher_1.0_all.deb`, ensuring universal compatibility across supported architectures.
* **Structured Indexing:** Organized by name, software type, and detailed technical description.
* **Search Engine:** Efficient entry filtering for rapid catalog localization.
* **Redirection Management:** Integrated system for the automated opening of links in the default web browser.
* **User Interface:** Low visual and systemic impact design, focused on operational efficiency.

## System Requirements

* **Operating System:** Debian-based distributions (Ubuntu, Linux Mint, Kali Linux, etc.).
* **Architecture:** Compatible with 32-bit and 64-bit systems (`all` architecture).
* **Connectivity:** Internet access required for external link redirection functionality.

## Installation and Usage

### Installation via Terminal

To ensure a correct installation while automatically managing dependencies, use the following command:

```bash
sudo apt install $(find $HOME -name "pp-launcher_3.1.0_all.deb" -print -quit)
