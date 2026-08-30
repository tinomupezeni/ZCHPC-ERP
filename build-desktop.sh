#!/bin/bash

# ZCHPC ERP Desktop Build Script

echo "--- Starting ZCHPC ERP Desktop Build ---"

# 1. Build React Frontend
echo "1. Building React Frontend..."
cd zchpc-erp-synergy-main
npm install
npm run build
cd ..

# 2. Prepare Electron UI folder
echo "2. Preparing Electron UI assets..."
rm -rf desktop-shell/ui_dist/*
cp -r zchpc-erp-synergy-main/dist/* desktop-shell/ui_dist/

# 3. Compile Backend (requires Python environment)
echo "3. Compiling Backend (Skip if already built)..."
# In a real environment, we'd run:
# cd erp_project
# source venv/bin/activate
# pyinstaller zchpc_backend.spec
# cd ..

# 4. Final Packaging (requires Node.js)
echo "4. Packaging Desktop Application..."
cd desktop-shell
npm install
# npm run build  # This generates the actual .exe
cd ..

echo "--- Build Script Prepared ---"
echo "To generate the final installer, run 'npm run build' inside 'desktop-shell/' on a Windows machine."
