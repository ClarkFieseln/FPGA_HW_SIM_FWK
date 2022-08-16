
library IEEE;
use IEEE.STD_LOGIC_1164.all;


use std.textio.all;
package hw_sim_fwk_pipe_common is
    procedure pipe_writeline(file o_file: text; value: integer);
end package;

package body hw_sim_fwk_pipe_common is
    constant USE_FLUSH : boolean := true;
    -- procedure pipe_writeline()
    -- #########################
    procedure pipe_writeline(file o_file : text; constant value : integer) is
      variable open_status : FILE_OPEN_STATUS;
      variable o_line : line;   
    begin
      write(o_line, value);
      writeline(o_file, o_line); 
      flush(o_file);
    end procedure pipe_writeline; 
end;


