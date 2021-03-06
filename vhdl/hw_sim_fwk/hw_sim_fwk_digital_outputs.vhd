
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

entity hw_sim_fwk_digital_outputs is
    generic(
        NR_DOS             : integer := 2;
        FILE_PATH          : string  := "/tmp/";
        DOS_HIGH_FILE_NAME : string  := "/tmp/do_high"; -- FILE_PATH & "do_high" -- cannot use concatenation here!
        DOS_LOW_FILE_NAME  : string  := "/tmp/do_low";
        PROTOCOL_DOS       : boolean := false -- to report details
    );
    -- NOTE: we want to take clock as input and change DO ONLY with clock
    port(
        reset  : in std_logic;
        clock  : in std_logic;
        hw_do : in std_logic_vector(NR_DOS - 1 downto 0)
    );
end hw_sim_fwk_digital_outputs;

architecture arch of hw_sim_fwk_digital_outputs is
begin
    -- #####################################
    -- creation of files upon flanks detection
    proc_update_dos : process(reset, clock, hw_do)
        variable was_file_created : boolean                               := false;
        variable do_level        : std_logic_vector(NR_DOS - 1 downto 0) := (others => '0');
        -- TODO: this works fine up to 100 files, beyond that need to manage file names in a different way so the lenght of the string is equal or otherwise
        --       properly handled.
        --       Note: unconstrained arrays are possible in VHDL-2008 onwards.
        --       Note: check use of "line" as alternative.
        type DOS_HIGH_FILE_ARRAY is array (NR_DOS - 1 downto 0) of string(1 to DOS_HIGH_FILE_NAME'length + 3); -- +3 for _xx at the end of the name.. 
        variable DOS_HIGH_FILE : DOS_HIGH_FILE_ARRAY;  
        type DOS_LOW_FILE_ARRAY is array (NR_DOS - 1 downto 0) of string(1 to DOS_LOW_FILE_NAME'length + 3); -- +3 for _xx at the end of the name.. 
        variable DOS_LOW_FILE : DOS_LOW_FILE_ARRAY;
    begin
        -- asynchronous reset
        -- ##################
        if reset = '1' then
            for i in 0 to NR_DOS - 1 loop
                -- initialize arrays of file names
                -- workaround works up to 99 files
                if i < 10 then
                    DOS_HIGH_FILE(i) := DOS_HIGH_FILE_NAME & "_" & integer'image(i) & NUL; -- append NULL character
                    DOS_LOW_FILE(i) := DOS_LOW_FILE_NAME & "_" & integer'image(i) & NUL; -- append NULL character
                else
                    DOS_HIGH_FILE(i) := DOS_HIGH_FILE_NAME & "_" & integer'image(i);
                    DOS_LOW_FILE(i) := DOS_LOW_FILE_NAME & "_" & integer'image(i);
                end if;
                -- initialize digital output signal depending on hw_do
                if hw_do(i) = '1' then
                    was_file_created := work.hw_sim_fwk_common.file_create(DOS_HIGH_FILE(i));
                    if was_file_created = true then
                        do_level(i) := '1';
                        if (PROTOCOL_DOS = true) then
                            report "simulated HW DO "&integer'image(i)&" initialized to ON.";
                        end if;
                    else
                        report "Error: could NOT initialize HW DO "&integer'image(i)&" to ON, no file created!";
                    end if;
                -- NOTE: if hw_do is NOT 1 then we also initialize to OFF..also for X,U,..
                else
                    was_file_created := work.hw_sim_fwk_common.file_create(DOS_LOW_FILE(i));
                    if was_file_created = true then
                        do_level(i) := '0';
                        if (PROTOCOL_DOS = true) then
                            report "simulated HW DO "&integer'image(i)&" initialized to OFF.";
                        end if;
                    else
                        report "Error: could NOT initialize HW DO "&integer'image(i)&" to OFF, no file created!";
                    end if;
                end if;
            end loop;
        elsif rising_edge(clock) then
            -- update file on rising/falling edges
            -- ##################################
            for i in 0 to NR_DOS - 1 loop
                if do_level(i) /= '1' and hw_do(i) = '1' then
                    was_file_created := work.hw_sim_fwk_common.file_create(DOS_HIGH_FILE(i));
                    if was_file_created = true then
                        do_level(i) := '1';
                        if (PROTOCOL_DOS = true) then
                            report "simulated HW DO "&integer'image(i)&" rising edge!";
                        end if;
                    else
                        report "Error: could NOT simulate HW DO "&integer'image(i)&" rising edge, no file created!";
                    end if;
                elsif do_level(i) /= '0' and hw_do(i) = '0' then
                    was_file_created := work.hw_sim_fwk_common.file_create(DOS_LOW_FILE(i));
                    if was_file_created = true then
                        do_level(i) := '0';
                        if (PROTOCOL_DOS = true) then
                            report "simulated HW DO "&integer'image(i)&" falling edge!";
                        end if;
                    else
                        report "Error: could NOT simulate HW DO "&integer'image(i)&" falling edge, no file created!";
                    end if;
                end if;
            end loop;
        end if;
    end process proc_update_dos;
end arch;

-- synthesis translate_on
-- ######################





