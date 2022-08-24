
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;


-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_fifo_write_int is
    generic(
        NR_SIGOUT               : integer := 2; -- current index of output signal
        SIGOUT_PATH             : string  := "\\.\pipe\";
        SIGOUT_FILE_NAME        : string  := SIGOUT_PATH & "sigout_" & integer'image(NR_SIGOUT);
        PROTOCOL_SIGOUT         : boolean := false
    );
    port(
        reset    : in std_logic;
        clock    : in std_logic;
        -- #############################################################################################
        -- NOTE: replace everywhere with commented code to use std_logic_vector i.o. int as input signal
        --       or implement here with "overloaded" functions?
        -- #############################################################################################
        sigout   : in integer -- std_logic_vector(15 downto 0)
    );
end hw_sim_fwk_fifo_write_int;

architecture arch of hw_sim_fwk_fifo_write_int is
begin
    -- process
    -- #######
    -- NOTE: the output signal is inside the sensitivity list so we support "asynchronous" output signals
    proc_update_sigout : process(reset, clock, sigout)
        variable initialized : boolean := false;
        variable resetted    : boolean := false;
        variable i           : integer := NR_SIGOUT;
        variable open_status : FILE_OPEN_STATUS;
        type INTEGER_FILE is file of integer; -- TODO: use "unsigned"? or implement .._fifo_write_unsigned.vhd ?
        file o_file          : INTEGER_FILE;        
        variable sigout_value: integer; -- std_logic_vector(15 downto 0);
        -- variable sigout_int  : integer;
    begin
        -- initialization
        -- ##############
        if initialized = false then
            initialized := true;
            if (PROTOCOL_SIGOUT = true) then
                report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" waiting to open for write on FIFO.";
            end if;
            -- The file, which is a FIFO (named pipe), is created by the external application.    
            loop
                file_open(open_status, o_file, SIGOUT_FILE_NAME,  write_mode);
                exit when open_status = open_ok;
            end loop;
            if (PROTOCOL_SIGOUT = true) then
                report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" opened for write on FIFO.";
            end if;
        -- asynchronous reset
        -- ##################            
        elsif reset = '1' then
            -- initialize sigout only once during reset
            if resetted = false then
                resetted := true;
                -- initialize output signal depending on sigout
                if sigout /= sigout_value then
                    -- write sigout value
                    sigout_value := sigout;
                    -- sigout_int := to_integer(unsigned(sigout));
                    write(o_file, sigout); -- sigout_int);
                    flush(o_file);   
                    if (PROTOCOL_SIGOUT = true) then
                        -- report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" initialized to "&to_hstring(sigout) & "h, as int = "&integer'image(sigout_int);
                        report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" initialized to "&integer'image(sigout);
                    end if;
                end if; -- if sigout /= sigout_value                         
            end if; -- if resetted = false    
        -- TODO: check this..
        -- elsif (rising_edge(sigout) or falling_edge(sigout)) or rising_edge(clock) then
        -- elsif (rising_edge(sigout) or falling_edge(sigout)) or (rising_edge(clock) or falling_edge(clock)) then
        -- elsif falling_edge(clock) then
        -- elsif rising_edge(clock) then
        elsif rising_edge(clock) or falling_edge(clock) then
            if sigout_value /= sigout then
                -- write sigout value
                sigout_value := sigout;
                -- sigout_int := to_integer(unsigned(sigout));
                write(o_file, sigout); -- sigout_int);
                flush(o_file);
                if (PROTOCOL_SIGOUT = true) then
                    -- report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" with value "&to_hstring(sigout) & "h, as int = "&integer'image(sigout_int);
                    report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" with value "&integer'image(sigout);
                end if;
            end if; -- if sigout_value /= sigout
        end if; -- if initialized, async reset or clock rising edge
    end process proc_update_sigout;
end arch;

-- synthesis translate_on
-- ######################





