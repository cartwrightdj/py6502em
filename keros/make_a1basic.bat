C:^Users^User^Documents^PythonProjects^Computer^keros


 
ca65 a1basic.asm -o a1basic.o
ld65 -m mapfile.map ^
  -u Z1d ^
  -u ch ^
  -u var ^
  -u lomem ^
  -u himem ^
  -u rnd ^
  -u noun_stk_l ^
  -u syn_stk_h ^
  -u noun_stk_h_str ^
  -u syn_stk_l ^
  -u noun_stk_h_int ^
  -u txtndxstk ^
  -u text_index ^
  -u leadbl ^
  -u pp ^
  -u pv ^
  -u acc ^
  -u srch ^
  -u tokndxstk ^
  -u srch2 ^
  -u if_flag ^
  -u cr_flag ^
  -u current_verb ^
  -u precedence ^
  -u x_save ^
  -u run_flag ^
  -u aux ^
  -u pline ^
  -u pverb ^
  -u p1 ^
  -u p2 ^
  -u p3 ^
  -u token_index ^
  -u pcon ^
  -u auto_inc ^
  -u auto_ln ^
  -u auto_flag ^
  -u char ^
  -u leadzr ^
  -u for_nest_count ^
  -u gosub_nest_count ^
  -u synstkdx ^
  -u synpag ^
  -u gstk_pverbl ^
  -u gstk_pverbh ^
  -u gstk_plinel ^
  -u gstk_plineh ^
  -u fstk_varl ^
  -u fstk_varh ^
  -u fstk_stepl ^
  -u fstk_steph ^
  -u fstk_plinel ^
  -u fstk_plineh ^
  -u fstk_pverbl ^
  -u fstk_pverbh ^
  -u fstk_tol ^
  -u fstk_toh ^
  -u buffer ^
  -u KBD ^
  -u KBDCR ^
  -u DSP ^
  -u START ^
  -u rdkey ^
  -u Se00c ^
  -u Se011 ^
  -u Se018 ^
  -u nextbyte ^
  -u Le034 ^
  -u list_comman ^
  -u list_all ^
  -u list_cmd ^
  -u list_line ^
  -u list_int ^
  -u list_token ^
  -u paren_substr ^
  -u comma_substr ^
  -u Se118 ^
  -u str_arr_dest ^
  -u dim_str ^
  -u input_str ^
  -u string_lit ^
  -u Se1bc ^
  -u string_eq ^
  -u string_neq ^
  -u mult_op ^
  -u Se254 ^
  -u Se25b ^
  -u mod_op ^
  -u read_line ^
  -u cold ^
  -u warm ^
  -u Le2b6 ^
  -u Le2f9 ^
  -u Le2fb ^
  -u Le883 ^
  -C a1basic.cfg -o basic.bin a1basic.o




pause