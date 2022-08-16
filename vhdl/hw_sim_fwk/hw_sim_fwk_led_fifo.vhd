
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;


-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_led_fifo is
    generic(
        NR_LED             : integer := 2; -- current index of LED
        FIFO_PATH          : string  := "\\.\pipe\";
        LED_FILE_NAME      : string  := FIFO_PATH & "led_";
        PROTOCOL_LED       : boolean := false
    );
    -- NOTE: we want to take clock as input and change LED ONLY with clock
    port(
        reset  : in std_logic;
        clock  : in std_logic;
        hw_led : in std_logic
    );
end hw_sim_fwk_led_fifo;

architecture arch of hw_sim_fwk_led_fifo is
begin
    -- #####################################
    -- NOTE: the hw_led signal is inside the sensitivity list so we support "asynchronous" LEDs
    proc_update_led : process(reset, clock, hw_led)
        variable initialized : boolean := false;
        variable resetted    : boolean := false;
        variable i           : integer := NR_LED;
        variable open_status : FILE_OPEN_STATUS;
        -- NOTE: it is not possible to create an array of files or
        --       including file type inside of a Record structure
        -- type BYTE is array(7 downto 0) of BIT;
        -- type INTEGER_FILE is file of BYTE;
        -- file o_file          : INTEGER_FILE; 
        type CHARACTER_FILE is file of character;
        file o_file          : CHARACTER_FILE;        
        variable led_level    : std_logic;
    begin
        -- initialization
        -- ##############
        if initialized = false then
            initialized := true;
            if (PROTOCOL_LED = true) then
                report "simulated HW LED "&integer'image(i)&" waiting to open for write on FIFO.";
            end if;
            -- The file, which is a FIFO (named pipe), is created by the external application.    
            loop
                file_open(open_status, o_file, LED_FILE_NAME,  write_mode);
                exit when open_status = open_ok;
            end loop;
            if (PROTOCOL_LED = true) then
                report "simulated HW LED "&integer'image(i)&" opened for write on FIFO.";
            end if;
        -- asynchronous reset
        -- ##################            
        elsif reset = '1' then
            -- initialize LED only once during reset
            if resetted = false then
                resetted := true;
                -- initialize LED signal depending on hw_led
                if hw_led = '1' then
                    -- write ONE
                    led_level := '1';
                    write(o_file, '1'); -- "00000001");
                    if (PROTOCOL_LED = true) then
                        report "simulated HW LED "&integer'image(i)&" initialized to ON.";
                    end if;
                -- NOTE: if hw_led is NOT 1 then we also initialize to OFF..also for X,U,..
                else
                    -- write ZERO
                    led_level := '0';
                    write(o_file, '0'); -- "00000000");
                    if (PROTOCOL_LED = true) then
                        report "simulated HW LED "&integer'image(i)&" initialized to OFF.";
                    end if;
                end if;
                flush(o_file);            
            end if; -- if resetted = false    
        -- TODO: check this..
        -- elsif (rising_edge(hw_led) or falling_edge(hw_led)) or rising_edge(clock) then
        elsif (rising_edge(hw_led) or falling_edge(hw_led)) or (rising_edge(clock) or falling_edge(clock)) then
            if led_level /= '1' and hw_led = '1' then
                -- write ONE
                led_level := '1';
                write(o_file, '1'); -- "00000001");
                flush(o_file);
                if (PROTOCOL_LED = true) then
                    report "simulated HW LED "&integer'image(i)&" rising edge!";
                end if;
            elsif led_level /= '0' and hw_led = '0' then
                -- write ZERO
                led_level := '0';
                write(o_file, '0'); -- "00000000");
                flush(o_file);
                if (PROTOCOL_LED = true) then
                    report "simulated HW LED "&integer'image(i)&" falling edge!";
                end if;
            end if;
        end if; -- if initialized, async reset or clock rising edge
    end process proc_update_led;    
end arch;

-- synthesis translate_on
-- ######################





