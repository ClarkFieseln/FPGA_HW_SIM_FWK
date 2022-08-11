
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

entity hw_sim_fwk_digital_inputs is
    generic(
        NR_DIS             : integer := 2;
        FILE_PATH          : string  := "/tmp/";
        DIS_FILE_NAME      : string  := FILE_PATH & "di_high";
        PROTOCOL_DIS       : boolean := false
    );
    port(
        reset     : in  std_logic;
        clock     : in  std_logic;
        hw_di     : out std_logic_vector(NR_DIS - 1 downto 0)
    );
end hw_sim_fwk_digital_inputs;

architecture arch of hw_sim_fwk_digital_inputs is
begin
    -- polling process
    -- ###############
    proc_update_dis : process(reset, clock)
        type POS_LEVEL_ARRAY is array (NR_DIS - 1 downto 0) of boolean;
        variable pos_level : POS_LEVEL_ARRAY := (others => false);
        -- TODO: this works fine up to 100 files, beyond that need to manage file names in a different way so the lenght of the string is equal or otherwise
        --       properly handled.
        --       Note: unconstrained arrays are possible in VHDL-2008 onwards.
        --       Note: check use of "line" as alternative.
        type DIS_FILE_ARRAY is array (NR_DIS - 1 downto 0) of string(1 to (DIS_FILE_NAME'length + 3)); -- +3 for _xx at the end of the name.. 
        variable DIS_FILE : DIS_FILE_ARRAY;   
    begin
        -- asynchronous reset
        if reset = '1' then
            for i in 0 to NR_DIS - 1 loop
                -- initialize array of file names
                -- workaround works up to 99 files
                if i < 10 then
                    DIS_FILE(i) := DIS_FILE_NAME & "_" & integer'image(i) & NUL; -- append NULL character
                else
                    DIS_FILE(i) := DIS_FILE_NAME & "_" & integer'image(i);
                end if; 
                -- initialize digital input signal depending on file existence
                if (file_exists(DIS_FILE(i)) = true) then
                    hw_di(i) <= '1';
                    pos_level(i) := true;
                    if (PROTOCOL_DIS = true) then
                        report "hw_di"&integer'image(i)&" initialized to 1";
                    end if;
                else
                    hw_di(i) <= '0';
                    pos_level(i) := false;
                    if (PROTOCOL_DIS = true) then
                        report "hw_di"&integer'image(i)&" initialized to 0";
                    end if;
                end if;
            end loop;
        -- synchronous events    
        -- Note: external simulator changes signals in "falling edge of clock"
        elsif falling_edge(clock) then
            if (PROTOCOL_DIS = true) then
                report "checking dis_rising/falling_edge..";
            end if;
            for i in 0 to NR_DIS - 1 loop
                -- rising edge?
                if pos_level(i) = false then
                    if (file_exists(DIS_FILE(i)) = true) then
                        if PROTOCOL_DIS = true then
                            report "digital input rising ege on DI = " & integer'image(i);
                        end if;
                        pos_level(i) := true;
                        hw_di(i) <= '1';
                    end if;
                -- falling edge?
                elsif (file_exists(DIS_FILE(i)) = false) then
                    if PROTOCOL_DIS = true then
                        report "ditial input falling ege on DI = " & integer'image(i);
                    end if;
                    pos_level(i) := false;
                    hw_di(i) <= '0';
                end if;
            end loop;
        end if;
    end process proc_update_dis;
end architecture arch;

-- synthesis translate_on
-- ######################




