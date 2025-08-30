FOR /f "tokens=*" %%i IN ('docker ps -q') DO docker stop %%i
FOR /f "tokens=*" %%i IN ('docker image ls  -q') DO docker image rm %%i
docker image ls