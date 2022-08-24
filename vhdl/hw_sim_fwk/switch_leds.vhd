
library ieee;
use ieee.std_logic_1164.ALL;


entity switch_leds is
    generic(
        NR_SWITCHES : integer := 2;
        NR_BUTTONS  : integer := 2;
        NR_LEDS     : integer := 2
    );
    port(
        reset  : in  std_logic;
        clock  : in  std_logic;
        switch : in  std_logic_vector(NR_SWITCHES - 1 downto 0);
        button : in  std_logic_vector(NR_BUTTONS - 1 downto 0);
        led    : out std_logic_vector(NR_LEDS - 1 downto 0)
    );
end switch_leds;

architecture Behavioral of switch_leds is
    signal led_reg : std_logic_vector(NR_LEDS - 1 downto 0);
begin
    -- process
    -- #######
    proc_switch_leds : process(reset, clock)
    begin
        -- asynchronous reset 
        if reset = '1' then
            led_reg <= (others => '0');
        -- synchronous events
        elsif rising_edge(clock) then
            -- led_reg(0) <= switch(0) and not button(0);            
            -- led_reg(NR_LEDS-1 downto 1) <= switch(NR_SWITCHES-1 downto 1);
            led_reg <= switch and not button; 
        end if;
    end process proc_switch_leds;
    -- output signals
    -- ##############
    led <= led_reg;
end Behavioral;

