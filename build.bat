@echo off
echo 🔧 Instalando dependencias...
pip install -r requirements.txt

echo 🔧 Compilando a ejecutable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Remote Manager" ^
    --add-data "./api_onomondo;api_onomondo" ^
    --add-data "./gui;gui" ^
    --add-data "./secrets;secrets" ^
    --add-data "./ssh;ssh" ^
    main_gui.py

echo ✅ ¡Listo! El ejecutable está en dist\UDP_Sender.exe
echo 📁 Abre la carpeta dist para encontrar el archivo .exe
pause