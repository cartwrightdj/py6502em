#include <stdarg.h>
int __fastcall__ kvprintf (const char* format, va_list ap);

int __fastcall__ putchar (int c);

//void kvprint(const char *s);
char *input(const char *s);

int __fastcall__ get_proc_state_base();
int __fastcall__ switch_vmem (int vmemslot);
int __fastcall__ get_proc_slot (int p);




