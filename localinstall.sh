#!/bin/sh
rm -rf dist/
poetry build
pipx install --force dist/devpod-*.tar.gz
