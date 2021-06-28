copy /y %HOMEPATH%\Downloads\SeattleBikeTag.kml .
del %HOMEPATH%\Downloads\SeattleBikeTag.kml
dir
pause
node FilterKML.js
dir