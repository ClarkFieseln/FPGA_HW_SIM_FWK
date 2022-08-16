
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;


-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_leds_fifo is
    generic(
        NR_LEDS            : integer := 2;
        FIFO_PATH          : string  := "\\.\pipe\";
        LEDS_FILE_NAME     : string  := FIFO_PATH & "led_";
        PROTOCOL_LEDS      : boolean := false
    );
    -- NOTE: we want to take clock as input and change LED ONLY with clock
    port(
        reset  : in std_logic;
        clock  : in std_logic;
        hw_led : in std_logic_vector(NR_LEDS - 1 downto 0)
    );
end hw_sim_fwk_leds_fifo;

architecture arch of hw_sim_fwk_leds_fifo is
    -- signals common to all modules
    signal clock_tm, reset_tm : std_logic;
    -- signals led
    signal hw_led_tm           : std_logic_vector(NR_LEDS - 1 downto 0);
begin
    GEN_LEDS:
    for I in 0 to (NR_LEDS - 1) generate
        hw_sim_fwk_led_fifo_unit_x : entity work.hw_sim_fwk_fifo_write
        generic map(            
            NR_SIGOUT          => I,
            SIGOUT_PATH        => FIFO_PATH,
            SIGOUT_FILE_NAME   => LEDS_FILE_NAME & integer'image(I),
            PROTOCOL_SIGOUT    => PROTOCOL_LEDS
        )  
        port map(
            reset  => reset_tm,
            clock  => clock_tm,
            sigout => hw_led_tm(I)
        );
    end generate GEN_LEDS;
    -- connect cables
    clock_tm <= clock;
    reset_tm <= reset;
    hw_led_tm <= hw_led;
end arch;

-- synthesis translate_on
-- ######################





