
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

entity hw_sim_fwk_switches is
    generic(
        NR_SWITCHES        : integer := 2;
        FILE_PATH          : string  := "/tmp/";
        SWITCHES_FILE_NAME : string  := "/tmp/switch_high"; -- FILE_PATH & "switch_high" -- cannot use concatenation here!
        PROTOCOL_SWITCHES  : boolean := false -- to report details
    );
    port(
        reset     : in  std_logic;
        clock     : in  std_logic;
        hw_switch : out std_logic_vector(NR_SWITCHES - 1 downto 0)
    );
end hw_sim_fwk_switches;

architecture arch of hw_sim_fwk_switches is
begin
    -- polling process
    -- ###############
    proc_update_switches : process(reset, clock)
        type POS_LEVEL_ARRAY is array (NR_SWITCHES - 1 downto 0) of boolean;
        variable pos_level : POS_LEVEL_ARRAY := (others => false);
        -- TODO: this works fine up to 100 files, beyond that need to manage file names in a different way so the lenght of the string is equal or otherwise
        --       properly handled.
        --       Note: unconstrained arrays are possible in VHDL-2008 onwards.
        --       Note: check use of "line" as alternative.
        type SWITCHES_FILE_ARRAY is array (NR_SWITCHES - 1 downto 0) of string(1 to (SWITCHES_FILE_NAME'length + 3)); -- +3 for _xx at the end of the name.. 
        variable SWITCHES_FILE : SWITCHES_FILE_ARRAY;   
    begin
        -- asynchronous reset
        if reset = '1' then
            for i in 0 to NR_SWITCHES - 1 loop
                -- initialize array of file names
                -- workaround works up to 99 files
                if i < 10 then
                    SWITCHES_FILE(i) := SWITCHES_FILE_NAME & "_" & integer'image(i) & NUL; -- append NULL character
                else
                    SWITCHES_FILE(i) := SWITCHES_FILE_NAME & "_" & integer'image(i);
                end if; 
                -- initialize switches signal depending on file existence
                if (file_exists(SWITCHES_FILE(i)) = true) then
                    hw_switch(i) <= '1';
                    pos_level(i) := true;
                    if (PROTOCOL_SWITCHES = true) then
                        report "hw_switch"&integer'image(i)&" initialized to 1";
                    end if;
                else
                    hw_switch(i) <= '0';
                    pos_level(i) := false;
                    if (PROTOCOL_SWITCHES = true) then
                        report "hw_switch"&integer'image(i)&" initialized to 0";
                    end if;
                end if;
            end loop;
        -- synchronous events    
        -- Note: external simulator changes signals in "falling edge of clock"
        elsif falling_edge(clock) then
            if (PROTOCOL_SWITCHES = true) then
                report "checking switches_rising/falling_edge..";
            end if;
            for i in 0 to NR_SWITCHES - 1 loop
                -- rising edge?
                if pos_level(i) = false then
                    if (file_exists(SWITCHES_FILE(i)) = true) then
                        if PROTOCOL_SWITCHES = true then
                            report "switches rising ege on LED = " & integer'image(i);
                        end if;
                        pos_level(i) := true;
                        hw_switch(i) <= '1';
                    end if;
                -- falling edge?
                elsif (file_exists(SWITCHES_FILE(i)) = false) then
                    if PROTOCOL_SWITCHES = true then
                        report "switches falling ege on LED = " & integer'image(i);
                    end if;
                    pos_level(i) := false;
                    hw_switch(i) <= '0';
                end if;
            end loop;
        end if;
    end process proc_update_switches;
end architecture arch;

-- synthesis translate_on
-- ######################





