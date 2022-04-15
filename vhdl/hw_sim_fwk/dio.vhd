
library ieee;
use ieee.std_logic_1164.ALL;

entity dio is
    generic(
        NR_DIS : integer := 2;
        NR_DOS : integer := 2
    );
    port(
        reset  : in  std_logic;
        clock  : in  std_logic;
        di     : in  std_logic_vector(NR_DIS - 1 downto 0);        
        do     : out std_logic_vector(NR_DOS - 1 downto 0)
    );
end dio;

architecture Behavioral of dio is
    signal do_reg : std_logic_vector(NR_DOS - 1 downto 0);
begin
    -- process
    -- #######
    proc_dio : process(reset, clock)
    begin
        -- asynchronous reset 
        if reset = '1' then
            do_reg <= (others => '0');
        -- synchronous events
        elsif rising_edge(clock) then
            do_reg <= di; 
        end if;
    end process proc_dio;
    -- output signals
    -- ##############
    do <= do_reg;
end Behavioral;

