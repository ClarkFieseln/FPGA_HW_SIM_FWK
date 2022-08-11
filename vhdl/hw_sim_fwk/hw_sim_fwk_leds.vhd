
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

entity hw_sim_fwk_leds is
    generic(
        NR_LEDS            : integer := 2;
        FILE_PATH          : string  := "/tmp/";
        LEDS_ON_FILE_NAME  : string  := FILE_PATH & "led_on";
        LEDS_OFF_FILE_NAME : string  := FILE_PATH & "led_off";
        PROTOCOL_LEDS      : boolean := false
    );
    -- NOTE: we want to take clock as input and change LED ONLY with clock
    port(
        reset  : in std_logic;
        clock  : in std_logic;
        hw_led : in std_logic_vector(NR_LEDS - 1 downto 0)
    );
end hw_sim_fwk_leds;

architecture arch of hw_sim_fwk_leds is
begin
    -- #####################################
    -- creation of files upon flanks detection
    proc_update_leds : process(reset, clock, hw_led)
        variable was_file_created : boolean                                := false;
        variable led_level        : std_logic_vector(NR_LEDS - 1 downto 0) := (others => '0');
        -- TODO: this works fine up to 100 files, beyond that need to manage file names in a different way so the lenght of the string is equal or otherwise
        --       properly handled.
        --       Note: unconstrained arrays are possible in VHDL-2008 onwards.
        --       Note: check use of "line" as alternative.
        type LEDS_ON_FILE_ARRAY is array (NR_LEDS - 1 downto 0) of string(1 to LEDS_ON_FILE_NAME'length + 3); -- +3 for _xx at the end of the name.. 
        variable LEDS_ON_FILE : LEDS_ON_FILE_ARRAY;  
        type LEDS_OFF_FILE_ARRAY is array (NR_LEDS - 1 downto 0) of string(1 to LEDS_OFF_FILE_NAME'length + 3); -- +3 for _xx at the end of the name.. 
        variable LEDS_OFF_FILE : LEDS_OFF_FILE_ARRAY;
    begin
        -- asynchronous reset
        -- ##################
        if reset = '1' then
            for i in 0 to NR_LEDS - 1 loop
                -- initialize arrays of file names
                -- workaround works up to 99 files
                if i < 10 then
                    LEDS_ON_FILE(i) := LEDS_ON_FILE_NAME & "_" & integer'image(i) & NUL; -- append NULL character
                    LEDS_OFF_FILE(i) := LEDS_OFF_FILE_NAME & "_" & integer'image(i) & NUL; -- append NULL character
                else
                    LEDS_ON_FILE(i) := LEDS_ON_FILE_NAME & "_" & integer'image(i);
                    LEDS_OFF_FILE(i) := LEDS_OFF_FILE_NAME & "_" & integer'image(i);
                end if;
                -- initialize leds signal depending on hw_led
                if hw_led(i) = '1' then
                    was_file_created := work.hw_sim_fwk_common.file_create(LEDS_ON_FILE(i));
                    if was_file_created = true then
                        led_level(i) := '1';
                        if PROTOCOL_LEDS = true then
                            report "simulated HW LED "&integer'image(i)&" initialized to ON.";
                        end if;
                    else
                        report "Error: could NOT initialize HW LED "&integer'image(i)&" to ON, no file created!";
                    end if;
                -- NOTE: if hw_led is NOT 1 then we also initialize to OFF..also for X,U,..
                else
                    was_file_created := work.hw_sim_fwk_common.file_create(LEDS_OFF_FILE(i));
                    if was_file_created = true then
                        led_level(i) := '0';
                        if PROTOCOL_LEDS = true then
                            report "simulated HW LED "&integer'image(i)&" initialized to OFF.";
                        end if;
                    else
                        report "Error: could NOT initialize HW LED "&integer'image(i)&" to OFF, no file created!";
                    end if;
                end if;
            end loop;
        elsif rising_edge(clock) then
            -- update file on rising/falling edges
            -- ##################################
            for i in 0 to NR_LEDS - 1 loop
                if led_level(i) /= '1' and hw_led(i) = '1' then
                    was_file_created := work.hw_sim_fwk_common.file_create(LEDS_ON_FILE(i));
                    if was_file_created = true then
                        led_level(i) := '1';
                        if PROTOCOL_LEDS = true then
                            report "simulated HW LED "&integer'image(i)&" rising edge!";
                        end if;
                    else
                        report "Error: could NOT simulate HW LED "&integer'image(i)&" rising edge, no file created!";
                    end if;
                elsif led_level(i) /= '0' and hw_led(i) = '0' then
                    was_file_created := work.hw_sim_fwk_common.file_create(LEDS_OFF_FILE(i));
                    if was_file_created = true then
                        led_level(i) := '0';
                        if PROTOCOL_LEDS = true then
                            report "simulated HW LED "&integer'image(i)&" falling edge!";
                        end if;
                    else
                        report "Error: could NOT simulate HW LED "&integer'image(i)&" falling edge, no file created!";
                    end if;
                end if;
            end loop;
        end if;
    end process proc_update_leds;
end arch;

-- synthesis translate_on
-- ######################





