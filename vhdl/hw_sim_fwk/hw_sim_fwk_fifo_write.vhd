
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;


-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_fifo_write is
    generic(
        NR_SIGOUT               : integer := 2; -- current index of output signal
        SIGOUT_PATH             : string  := "\\.\pipe\";
        SIGOUT_FILE_NAME        : string  := SIGOUT_PATH & "sigout_" & integer'image(NR_SIGOUT);
        PROTOCOL_SIGOUT         : boolean := false
    );
    port(
        reset    : in std_logic;
        clock    : in std_logic;
        sigout   : in std_logic
    );
end hw_sim_fwk_fifo_write;

architecture arch of hw_sim_fwk_fifo_write is
begin
    -- process
    -- #######
    -- NOTE: the output signal is inside the sensitivity list so we support "asynchronous" output signals
    proc_update_sigout : process(reset, clock, sigout)
        variable initialized : boolean := false;
        variable resetted    : boolean := false;
        variable i           : integer := NR_SIGOUT;
        variable open_status : FILE_OPEN_STATUS;
        -- NOTE: it is not possible to create an array of files or
        --       including file type inside of a Record structure
        -- type BYTE is array(7 downto 0) of BIT;
        -- type INTEGER_FILE is file of BYTE;
        -- file o_file          : INTEGER_FILE; 
        type CHARACTER_FILE is file of character;
        file o_file          : CHARACTER_FILE;        
        variable sigout_level    : std_logic;
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
                if sigout = '1' then
                    -- write ONE
                    sigout_level := '1';
                    write(o_file, '1'); -- "00000001");
                    if (PROTOCOL_SIGOUT = true) then
                        report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" initialized to HIGH/ON.";
                    end if;
                -- NOTE: if sigout is NOT 1 then we also initialize to LOW/OFF also for X,U,..
                else
                    -- write ZERO
                    sigout_level := '0';
                    write(o_file, '0'); -- "00000000");
                    if (PROTOCOL_SIGOUT = true) then
                        report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" initialized to LOW/OFF.";
                    end if;
                end if;
                flush(o_file);            
            end if; -- if resetted = false    
        -- TODO: check this..
        -- elsif (rising_edge(sigout) or falling_edge(sigout)) or rising_edge(clock) then
        elsif (rising_edge(sigout) or falling_edge(sigout)) or (rising_edge(clock) or falling_edge(clock)) then
            if sigout_level /= '1' and sigout = '1' then
                -- write ONE
                sigout_level := '1';
                write(o_file, '1'); -- "00000001");
                flush(o_file);
                if (PROTOCOL_SIGOUT = true) then
                    report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" rising edge!";
                end if;
            elsif sigout_level /= '0' and sigout = '0' then
                -- write ZERO
                sigout_level := '0';
                write(o_file, '0'); -- "00000000");
                flush(o_file);
                if (PROTOCOL_SIGOUT = true) then
                    report SIGOUT_FILE_NAME&": simulated HW output signal "&integer'image(i)&" falling edge!";
                end if;
            end if;
        end if; -- if initialized, async reset or clock rising edge
    end process proc_update_sigout;
end arch;

-- synthesis translate_on
-- ######################





