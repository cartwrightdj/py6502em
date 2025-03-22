C:\Users\User\Documents\PythonProjects\Computer\keros


 
ca65 kvio.s -o kvio.o
cc65 keros.c 
ca65 keros.s -o keros.o --feature string_escapes
ca65 kvprintf.s -o kvprintf.o 
ca65 crt0.s -o crt0.o
ca65 procs.s -o procs.o
ca65 staxsp.s -o staxsp.o
ca65 ldaxsp.s -o ldaxsp.o
ca65 zeropage.s -o zeropage.o



ld65 -m mapfile.map -v  -o   staxsp.o procs.o kvprintf.o kvio.o crt0.o zeropage.o ldaxsp.o keros.o none.lib  -C keros.cfg -L C:\Users\User\Documents\cc65\lib 

copy C:\Users\User\Documents\PythonProjects\Computer\keros\rom.bin C:\Users\User\Documents\PythonProjects\Computer\rom.bin /Y
copy C:\Users\User\Documents\PythonProjects\Computer\keros\mapfile.map C:\Users\User\Documents\PythonProjects\Computer\mapfile.map /Y


pause