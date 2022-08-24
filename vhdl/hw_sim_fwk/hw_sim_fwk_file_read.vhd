
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

entity hw_sim_fwk_file_read is
    generic(
        NR_SIGSIN           : integer := 2; -- number of input signals
        SIGSIN_PATH         : string  := "/tmp/";
        SIGSIN_FILE_NAME    : string  := SIGSIN_PATH & "sigsin_high";
        PROTOCOL_SIGSIN     : boolean := false
    );
    port(
        reset     : in  std_logic;
        clock     : in  std_logic;
        sigsin    : out std_logic_vector(NR_SIGSIN - 1 downto 0)
    );
end hw_sim_fwk_file_read;

architecture arch of hw_sim_fwk_file_read is
begin
    -- polling process
    -- ###############
    proc_update_sigsin : process(reset, clock)
        type POS_LEVEL_ARRAY is array (NR_SIGSIN - 1 downto 0) of boolean;
        variable pos_level : POS_LEVEL_ARRAY := (others => false);
        -- TODO: this works fine up to 100 files, beyond that need to manage file names in a different way so the lenght of the string is equal or otherwise
        --       properly handled.
        --       Note: unconstrained arrays are possible in VHDL-2008 onwards.
        --       Note: check use of "line" as alternative.
        type SIGSIN_FILE_ARRAY is array (NR_SIGSIN - 1 downto 0) of string(1 to (SIGSIN_FILE_NAME'length + 3)); -- +3 for _xx at the end of the name.. 
        variable SIGSIN_FILE : SIGSIN_FILE_ARRAY;   
    begin
        -- asynchronous reset
        if reset = '1' then
            for i in 0 to NR_SIGSIN - 1 loop
                -- initialize array of file names
                -- workaround works up to 99 files
                if NR_SIGSIN > 1 then
                    if i < 10 then
                        SIGSIN_FILE(i) := SIGSIN_FILE_NAME & "_" & integer'image(i) & NUL; -- append NULL character
                    else
                        SIGSIN_FILE(i) := SIGSIN_FILE_NAME & "_" & integer'image(i);
                    end if; 
                else
                    SIGSIN_FILE(i) := SIGSIN_FILE_NAME & NUL & NUL & NUL; -- fill last 3 characters with NULL
                end if;
                -- initialize digital input signal depending on file existence
                if (file_exists(SIGSIN_FILE(i)) = true) then
                    sigsin(i) <= '1';
                    pos_level(i) := true;
                    if (PROTOCOL_SIGSIN = true) then
                        report SIGSIN_FILE(i)&": input signal "&integer'image(i)&" initialized to 1";
                    end if;
                else
                    sigsin(i) <= '0';
                    pos_level(i) := false;
                    if (PROTOCOL_SIGSIN = true) then
                        report SIGSIN_FILE(i)&": input signal "&integer'image(i)&" initialized to 0";
                    end if;
                end if;
            end loop;
        -- synchronous events    
        elsif rising_edge(clock) then
        -- TODO: check this..
        -- elsif rising_edge(clock) or falling_edge(clock) then -- detect DI changes in both clock edges to give async DIs a chance to be seen (?)
            for i in 0 to NR_SIGSIN - 1 loop
                if (PROTOCOL_SIGSIN = true) then
                    report SIGSIN_FILE(i)&": checking input signal rising/falling_edge..";
                end if;
                -- rising edge?
                if pos_level(i) = false then
                    if (file_exists(SIGSIN_FILE(i)) = true) then
                        if PROTOCOL_SIGSIN = true then
                            report SIGSIN_FILE(i)&": input signal rising ege on index = " & integer'image(i);
                        end if;
                        pos_level(i) := true;
                        sigsin(i) <= '1';
                    end if;
                -- falling edge?
                elsif (file_exists(SIGSIN_FILE(i)) = false) then
                    if PROTOCOL_SIGSIN = true then
                        report SIGSIN_FILE(i)&": input signal falling ege on index = " & integer'image(i);
                    end if;
                    pos_level(i) := false;
                    sigsin(i) <= '0';
                end if;
            end loop;
        end if;
    end process proc_update_sigsin;
end architecture arch;

-- synthesis translate_on
-- ######################




