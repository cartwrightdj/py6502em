#include "kvio.h"
#include <stddef.h>
#include <stdio.h>
#include <string.h>  // Include for strcmp()

#define PROC_STATE_SIZE 9

#define CMD_NOTHING 0
#define CMD_INVALID 1

static unsigned char cmd;
static char *cmd_asc, *arg1, *arg2, *arg3, *args;  /* 'args': everything after command */



struct proc_state {
    unsigned char parent_proc;
    unsigned char state_flags;
    unsigned char pc_main_lo;
    unsigned char pc_main_hi;
    unsigned char stack_point;
    size_t reg_a;
    size_t reg_x;
    size_t reg_y;
    size_t proc_flags;
};

struct proc_state* get_proc_state(int index) {
    /* Get pointer to the start of the proc_state array from assembly */
    size_t *base = get_proc_state_base();
    
    /* Calculate the address of the requested structure.
     * Since each record is PROC_STATE_SIZE bytes, we add index * PROC_STATE_SIZE.
     */
    return (struct proc_state*)(base + (index * PROC_STATE_SIZE));
}

int proc_table(void){
    struct proc_state *ps;
    unsigned char i;

    printf("\t\tProcess Table\r\n");
    printf("----------------------------------------------------\r\n");
    printf("ID  PRNT    ST  LO HI\r\n");
    for (i = 0; i <= 8; i++) {
        
        ps = get_proc_state(i);

        printf("%hu\t%hu\t%hu\t%hu\t%hu\r\n", i,ps->parent_proc,ps->state_flags,ps->pc_main_lo,ps->pc_main_hi);
    }
    return 0;
}

static void get_command(void){
    char *ip;
    ip = input("\r$: ");
    /* skip over the first non-whitespace item */
    cmd_asc = strtok(ip, " ");
    printf("Cmd: %s ",cmd_asc);
    

               
    
    /* get arguments */
    arg1 = strtok(NULL, " \t\n");
    if (! arg1){
        printf("\r\n");
        return;
    }
    printf("Arg: %s ",arg1);
    arg2 = strtok(NULL, " \t\n");
    if (! arg2){
        printf("\r\n");
        return;
    }
    printf("Arg: %s ",arg2);
    arg3 = strtok(NULL, " \t\n");
    if (! arg3){
        printf("\r\n");
        return;
    }
    printf("Arg: %s ",arg3);
    printf("\r\n");
    return;

}

int main(void) {
    struct proc_state *ps;
    char *ip;

    int index = 66;  /* select the second record */
       
    //ps = get_proc_state(index);
    //printf("got base proc state: %d ABCD \r", index);
    proc_table();

    while(1){
        get_command();
        if (strcmp(cmd_asc, "PT") == 0) {
            proc_table();
        }
    }
    
    // This return will never be reached
    return 0;
}

int hwirq(void){
    __asm__ ("SEI");
    __asm__ ("RTI");
}




	