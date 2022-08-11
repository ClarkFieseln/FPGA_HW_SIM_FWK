
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;


-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_digital_output is
    generic(
        NR_DO              : integer := 2; -- current index of DO
        FIFO_PATH          : string  := "\\.\pipe\";
        DO_FILE_NAME       : string  := FIFO_PATH & "do_" & integer'image(NR_DO);
        PROTOCOL_DOS       : boolean := false
    );
    port(
        reset   : in std_logic;
        clock   : in std_logic;
        hw_do   : in std_logic
    );
end hw_sim_fwk_digital_output;

architecture arch of hw_sim_fwk_digital_output is
begin
    -- process
    -- #######
    -- NOTE: the hw_do signal is inside the sensitivity list so we support "asynchronous" DOs
    proc_update_do : process(reset, clock, hw_do)
        variable initialized : boolean := false;
        variable resetted    : boolean := false;
        variable i           : integer := NR_DO;
        variable open_status : FILE_OPEN_STATUS;
        -- NOTE: it is not possible to create an array of files or
        --       including file type inside of a Record structure
        -- type BYTE is array(7 downto 0) of BIT;
        -- type INTEGER_FILE is file of BYTE;
        -- file o_file          : INTEGER_FILE; 
        type CHARACTER_FILE is file of character;
        file o_file          : CHARACTER_FILE;        
        variable do_level    : std_logic;
    begin
        -- initialization
        -- ##############
        if initialized = false then
            initialized := true;
            if (PROTOCOL_DOS = true) then
                report "simulated HW DO "&integer'image(i)&" waiting to open for write on FIFO.";
            end if;
            -- The file, which is a FIFO (named pipe), is created by the external application.    
            loop
                file_open(open_status, o_file, DO_FILE_NAME,  write_mode);
                exit when open_status = open_ok;
            end loop;
            if (PROTOCOL_DOS = true) then
                report "simulated HW DO "&integer'image(i)&" opened for write on FIFO.";
            end if;
        -- asynchronous reset
        -- ##################            
        elsif reset = '1' then
            -- initialize DO only once during reset
            if resetted = false then
                resetted := true;
                -- initialize digital output signal depending on hw_do
                if hw_do = '1' then
                    -- write ONE
                    do_level := '1';
                    write(o_file, '1'); -- "00000001");
                    if (PROTOCOL_DOS = true) then
                        report "simulated HW DO "&integer'image(i)&" initialized to ON.";
                    end if;
                -- NOTE: if hw_do is NOT 1 then we also initialize to OFF..also for X,U,..
                else
                    -- write ZERO
                    do_level := '0';
                    write(o_file, '0'); -- "00000000");
                    if (PROTOCOL_DOS = true) then
                        report "simulated HW DO "&integer'image(i)&" initialized to OFF.";
                    end if;
                end if;
                flush(o_file);            
            end if; -- if resetted = false    
        -- elsif rising_edge(clock) then -- by convention we update DOs "synchronously" on "rising clock edges"
        elsif (rising_edge(hw_do) or falling_edge(hw_do)) or rising_edge(clock) then
            if do_level /= '1' and hw_do = '1' then
                -- write ONE
                do_level := '1';
                write(o_file, '1'); -- "00000001");
                flush(o_file);
                if (PROTOCOL_DOS = true) then
                    report "simulated HW DO "&integer'image(i)&" rising edge!";
                end if;
            elsif do_level /= '0' and hw_do = '0' then
                -- write ZERO
                do_level := '0';
                write(o_file, '0'); -- "00000000");
                flush(o_file);
                if (PROTOCOL_DOS = true) then
                    report "simulated HW DO "&integer'image(i)&" falling edge!";
                end if;
            end if;
        end if; -- if initialized, async reset or clock rising edge
    end process proc_update_do;
end arch;

-- synthesis translate_on
-- ######################





