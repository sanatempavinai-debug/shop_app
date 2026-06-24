@echo off
chcp 65001 >nul
title LaoShop — Stop

echo.
echo  [*] ກຳລັງຢຸດ LaoShop...
docker compose down
echo.
echo  [✓] ຢຸດສຳເລັດ
echo.
pause
