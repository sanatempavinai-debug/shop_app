@echo off
chcp 65001 >nul
title LaoShop — Docker Startup

echo.
echo  ╔══════════════════════════════════════╗
echo  ║        LAOSHOP — Docker Start        ║
echo  ╚══════════════════════════════════════╝
echo.

:: ກວດສອບ Docker ເປີດຢູ່ບໍ
docker info >nul 2>&1
if errorlevel 1 (
    echo  [!] Docker Desktop ຍັງບໍ່ໄດ້ເປີດ!
    echo  [!] ກາລຸນາເປີດ Docker Desktop ກ່ອນ ແລ້ວລອງໃໝ່
    pause
    exit /b 1
)

echo  [✓] Docker Desktop ພ້ອມໃຊ້ງານ
echo.
echo  [*] ກຳລັງ build ແລະ start containers...
echo.

docker compose up -d --build

if errorlevel 1 (
    echo.
    echo  [!] ເກີດຂໍ້ຜິດພາດ — ກວດສອບ log ດ້ວຍ: docker compose logs
    pause
    exit /b 1
)

echo.
echo  [*] ລໍຖ້າ database ພ້ອມ...
timeout /t 5 /nobreak >nul

echo.
echo  ╔══════════════════════════════════════╗
echo  ║         ✓ ສຳເລັດ! ພ້ອມໃຊ້ງານ          ║
echo  ╠══════════════════════════════════════╣
echo  ║  🛒 ໜ້າຮ້ານ : http://localhost:8000   ║
echo  ║  ⚙  Admin  : http://localhost:8000/admin ║
echo  ╚══════════════════════════════════════╝
echo.

start http://localhost:8000

echo  ກົດ Enter ເພື່ອປິດໜ້າຕ່າງນີ້ (server ຍັງລັນຢູ່)
pause >nul
