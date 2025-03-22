cd C:\Users\User\Documents\Computer\keros

ca65 keros.s -o keros.o

ld65 -m mapfile.map -v  -o   staxsp.o procs.o kvprintf.o kvio.o crt0.o zeropage.o ldaxsp.o keros.o none.lib  -C keros.cfg -L C:\Users\User\Documents\cc65\lib 

copy C:\Users\User\Documents\Computer\keros\rom.bin C:\Users\User\Documents\Computer\rom.bin /Y
copy C:\Users\User\Documents\Computer\keros\mapfile.map C:\Users\User\Documents\Computer\mapfile.map /Y


pause