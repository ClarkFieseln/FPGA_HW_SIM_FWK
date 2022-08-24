
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
    -- Use process logic or just wire-through?
    -- With wire-through we avoid using an additional register which also adds a new delay.
    -- But in case some additional logic is needed we do need this additional intermediate step.
    constant USE_PROCESS_LOGIC : boolean := false; -- true; -- false;
    signal do_reg : std_logic_vector(NR_DOS - 1 downto 0);
begin
    g_conditional_process : if USE_PROCESS_LOGIC = true generate
        -- process
        -- #######
        -- NOTE: the reset signal is inside the sensitivity list so we support "asynchronous" reset
        -- NOTE: the di signal is inside the sensitivity list so we support "asynchronous" DIs
        -- proc_dio : process(reset, clock, di)
        -- NOTE: the di signal is "partially" inside the sensitivity list so we support "asynchronous" DIs for some DIs
        proc_dio : process(reset, clock, di(NR_DIS - 1 downto NR_DIS/2))
        begin
            -- asynchronous reset 
            if reset = '1' then
                do_reg <= (others => '0');
            -- synchronous events
            elsif rising_edge(clock) then
                do_reg <= di; 
            -- asynchronous DIs that might as well be output as asynchronous DOs (see hw_sim_fwk_digital_output)
            elsif rising_edge(di(NR_DIS - 1)) then
                do_reg(NR_DIS - 1) <= di(NR_DIS - 1); 
            elsif rising_edge(di(NR_DIS - 2)) then
                do_reg(NR_DIS - 2) <= di(NR_DIS - 2); 
            elsif rising_edge(di(NR_DIS - 3)) then
                do_reg(NR_DIS - 3) <= di(NR_DIS - 3); 
            elsif rising_edge(di(NR_DIS - 4)) then
                do_reg(NR_DIS - 4) <= di(NR_DIS - 4);     
            elsif rising_edge(di(NR_DIS - 5)) then
                do_reg(NR_DIS - 5) <= di(NR_DIS - 5);                              
            end if;
        end process proc_dio;
        -- output signals
        -- ##############
        do <= do_reg;
    else generate
        -- NOTE: here we get the following warnings but we can "wire-through" DI->DO signals without additional delays/flip-flops
        --       WARNING: [Synth 8-7129] Port reset in module dio is either unconnected or has no load
        --       WARNING: [Synth 8-7129] Port clock in module dio is either unconnected or has no load
        do <= di;
    end generate g_conditional_process;
end Behavioral;



