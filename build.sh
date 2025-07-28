#!/usr/bin/env bash

mkdir -p wkhtmltopdf
cd wkhtmltopdf

# Descargar binario portable actualizado
wget https://github.com/ashrafminhaj/wkhtmltopdf-installer/releases/download/v0.12.6/wkhtmltox.tar.xz
tar -xf wkhtmltox.tar.xz

# Copiar binario al raíz del proyecto
cp wkhtmltox/bin/wkhtmltopdf ../wkhtmltopdf-local
