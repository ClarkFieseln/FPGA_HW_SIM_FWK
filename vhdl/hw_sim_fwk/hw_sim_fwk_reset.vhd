library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;
use hw_sim_fwk.hw_sim_fwk_common.all;

-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_reset is
    generic(        
        FILE_PATH       : string  := "/tmp/";
        RESET_FILE_NAME : string  := FILE_PATH & "reset_high";
        PROTOCOL_RESET  : boolean := false
    );
    port(        
        clock     : in  std_logic;
        hw_reset  : out std_logic
    );
end hw_sim_fwk_reset;

architecture arch of hw_sim_fwk_reset is
begin
    -- polling process
    -- ###############
    proc_update_reset : process(clock)
        variable initialized         : boolean := false;
        variable pos_level           : boolean := false;
    begin
        -- initialization?
        if initialized = false then
            initialized := true;
            -- initialize reset signal depending on file existence
            if (work.hw_sim_fwk_common.file_exists(RESET_FILE_NAME) = true) then
                hw_reset <= '1';
                pos_level := true;
                if (PROTOCOL_RESET = true) then
                    report "hw_reset initialized to 1";
                end if;
            else
                hw_reset <= '0';
                pos_level := false;
                if (PROTOCOL_RESET = true) then
                    report "hw_reset initialized to 0";
                end if;
            end if;
        -- synchronous events
        -- Note: external simulator changes signals in "falling edge of clock"
        else -- elsif (rising_edge(clock) or falling_edge(clock)) then
            if (PROTOCOL_RESET = true) then
                report "checking reset_rising/falling_edge..";
            end if;
            -- rising edge?
            if (file_exists(RESET_FILE_NAME) = true) then
                if pos_level = false then
                    pos_level := true;
                    hw_reset <= '1';
                    if (PROTOCOL_RESET = true) then
                        report "reset = 1";
                    end if;                    
                end if;
            -- falling edge?
            else
                if pos_level = true then
                    pos_level := false;
                    hw_reset <= '0';
                    if (PROTOCOL_RESET = true) then
                        report "reset = 0";
                    end if;          
                end if;          
            end if;
        end if;
    end process proc_update_reset;
end arch;

-- synthesis translate_on
-- ######################







