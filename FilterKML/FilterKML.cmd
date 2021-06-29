@echo off
set BikeTag="https://www.google.com/maps/d/u/0/edit?hl=en&mid=1ALf0s6IwCar4juuSamKjhZuOBVoPvSfk"
set LaterTag="https://www.google.com/maps/d/u/0/edit?hl=en&mid=10VH9MXzCK25k1RfplRkvMkGtOQFU2Ujs"
:TOP
echo Export KML from %BikeTag%
echo.
pause
if exist %HOMEPATH%\Downloads\SeattleBikeTag.kml (
    copy /y %HOMEPATH%\Downloads\SeattleBikeTag.kml .
    del %HOMEPATH%\Downloads\SeattleBikeTag.kml 
) else ( 
    goto :TOP
)
dir *.kml
pause
node FilterKML.js
dir *.kml
echo.
echo Import new.KML file to %LaterTag%
