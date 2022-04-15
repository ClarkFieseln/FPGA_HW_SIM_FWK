
library ieee;
use ieee.std_logic_1164.all;
use STD.textio.all;
use ieee.std_logic_textio.all; 


package hw_sim_fwk_common is
  -- functions
  -- #########
  function file_exists(filename : in string) return boolean;
  function file_create(filename : in string) return boolean;
end hw_sim_fwk_common;


package body hw_sim_fwk_common is
  -- function file_exists()
  -- #####################
  function file_exists(filename : in string) return boolean is
    variable open_status : FILE_OPEN_STATUS;
    variable ret_val : boolean := false;
    file infile : text;    
  begin
    file_open(open_status, infile, filename, read_mode);
    if open_status = open_ok then
      file_close(infile);
      ret_val := true;
    end if;
    return ret_val;
  end function file_exists;  
  -- funciton file_create()
  -- #####################
  -- Note: the consumer deletes the files right after detection
  function file_create(filename : in string) return boolean is
    variable ret_val : boolean := false;
    variable open_status : FILE_OPEN_STATUS;
    file LEDS_FILE : text;
  begin
    file_open(open_status, LEDS_FILE, filename, write_mode);
    if open_status /= open_ok then
      report "Error: could not create file for LED!";
    else
      file_close(LEDS_FILE);
      ret_val := true;
    end if;	
    return ret_val;		
  end function file_create;
end hw_sim_fwk_common;








