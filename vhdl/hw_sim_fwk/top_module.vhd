
library ieee;
use ieee.std_logic_1164.ALL;


-- top_module just "passes through" signals to and from modMCounter and switch_leds modules.
-- No additional logic here besides making sure that the intermediate signals are updated
-- only on the rising edge of the clock.
-- The sender and receiver from these signals is the Hardware Simulation Framework and the Testbench.
-- ##################################################################################################
entity top_module is
    generic(
        -- modMCounter:
        M              : integer := 5;     -- count from 0 to M-1
        N              : integer := 3;     -- N bits required to count upto M i.e. 2**N >= M
        -- switch_leds
        NR_SWITCHES    : integer := 2;
        NR_BUTTONS     : integer := 2;
        NR_LEDS        : integer := 2;
        -- dio
        NR_DIS         : integer := 2;
        NR_DOS         : integer := 2;
        -- LT2314_driver
        -- SCK = CLK_XXX_MHZ / (POSTSCALER*2) = (CLK_XXX_MHZ / 2) MHz
	    SCK_POSTSCALER : std_logic_vector := "0000000000000010"
    );
    port(
        -- common
        reset_in           : in  std_logic;
        clock_in           : in  std_logic;
        -- modMCounter:         
        complete_tick_out  : out std_logic;
        count_out          : out std_logic_vector(N - 1 downto 0);
        -- switch_leds:
        switch_in          : in  std_logic_vector(NR_SWITCHES - 1 downto 0);
        button_in          : in  std_logic_vector(NR_BUTTONS - 1 downto 0);
        led_out            : out std_logic_vector(NR_LEDS - 1 downto 0);
        -- dio:
        di_in              : in  std_logic_vector(NR_DIS - 1 downto 0);
        do_out             : out std_logic_vector(NR_DOS - 1 downto 0);  
        -- LT2314_driver
        data_out           : out std_logic_vector(15 downto 0);        
        sampling_pulse     : in  std_logic;
	    SPI_DIN            : in  std_logic;
	    SPI_nCS            : out std_logic;
	    SPI_CLK            : out std_logic
    );    
    -- NOTE: functions not used for now
    -- ################################
    FUNCTION reverse(a : IN STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR IS
        VARIABLE result : STD_LOGIC_VECTOR(a'RANGE);
        ALIAS aa : STD_LOGIC_VECTOR(a'REVERSE_RANGE) IS a;
        BEGIN
            FOR i IN aa'RANGE LOOP
                result(i) := aa(i);
            END LOOP;
        RETURN result;
    END;
    FUNCTION invert(a : IN STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR IS
        VARIABLE result : STD_LOGIC_VECTOR(a'RANGE);
        BEGIN
            FOR i IN a'RANGE LOOP
                result(i) := not(a(i));
            END LOOP;
        RETURN result;
    END;    
    -- ################################
end top_module;

architecture Behavioral of top_module is
    -- signals common to both modules
    signal clock_tm, reset_tm : std_logic;
    -- signals modMCounter
    signal complete_tick_tm   : std_logic;
    signal count_tm           : std_logic_vector(N - 1 downto 0);
    -- signals switch_leds  
    signal led_tm             : std_logic_vector(NR_LEDS - 1 downto 0);
    signal switch_tm          : std_logic_vector(NR_SWITCHES - 1 downto 0);
    signal button_tm          : std_logic_vector(NR_BUTTONS - 1 downto 0);
    -- signals dio
    signal do_tm              : std_logic_vector(NR_DOS - 1 downto 0);
    signal di_tm              : std_logic_vector(NR_DIS - 1 downto 0);
    -- signals LT2314 driver
    signal sampling_pulse_tm  : std_logic;
	signal SPI_DIN_tm         : std_logic;
	signal SPI_nCS_tm         : std_logic;
	signal SPI_CLK_tm         : std_logic;
	signal data_out_tm        : std_logic_vector(15 downto 0);
begin
    -- instantiate modMCounter
    -- #######################    
    -- modMCounter_inst : modMCounter
    modMCounter_inst : entity work.modMCounter
        generic map(
            M => M,
            N => N
        )
        port map(
            clock         => clock_tm,  -- common signal
            reset         => reset_tm,  -- common signal
            complete_tick => complete_tick_tm,
            count         => count_tm
        );
    -- instantiate switch_leds_unit
    -- ############################
    switch_leds_unit : entity work.switch_leds
        generic map(
            NR_SWITCHES => NR_SWITCHES,
            NR_BUTTONS  => NR_BUTTONS,
            NR_LEDS     => NR_LEDS
        )
        port map(
            -- in
            reset  => reset_tm,         -- common signal
            clock  => clock_tm,         -- common signal
            switch => switch_tm,
            button => button_tm,
            -- out
            led    => led_tm
        );
    -- instantiate dio
    -- ###############
    dio_unit : entity work.dio
        generic map(
            NR_DIS => NR_DIS,
            NR_DOS => NR_DOS
        )
        port map(
            -- in
            reset  => reset_tm,         -- common signal
            clock  => clock_tm,         -- common signal
            di     => di_tm,            
            -- out
            do     => do_tm
        );      
    -- instantiate LT2314_driver
    -- #########################
    proc_LT2314_driver: entity work.LT2314_driver   
		port map(
			clk            => clock_tm,  -- common signal
			sampling_pulse => sampling_pulse_tm,
			postscaler_in  => SCK_POSTSCALER,
			spi_sck        => SPI_CLK_tm,
			spi_cs_n       => SPI_nCS_tm,
			spi_din        => SPI_DIN_tm,
			data_out       => data_out_tm
		);
    -- common process
    -- Note:
    --      in this process we put everything together.
    --      Alternatively, we could move async and sync behavior of modMCount and switch_leds
    --      to separate processes with corresponding sensitivity lists.
    --      Both solutions generate the same circuits but the readability varies.
    --      The current approach focuses on the fact that we have a top_module which
    --      under normal conditions would add some logic to the design.
    -- ##########################################################################
    proc_common : process(clock_in, reset_in) -- , switch_in, button_in)
    begin
        -- in common
        -- clock_tm <= clock_in;
        -- reset_tm <= reset_in;
        if reset_in = '1' then
            -- out modMCounter
            count_out         <= (others => '0');
            complete_tick_out <= '0';
            -- in switch_leds
            switch_tm         <= (others => '0');
            button_tm         <= (others => '0');
            -- out switch_leds
            led_out           <= (others => '0');
            -- in dio
            di_tm             <= (others => '0');
            -- out dio
            do_out            <= (others => '0');
            -- LT2314
            data_out          <= (others => '0');
            SPI_nCS           <= '1';
            SPI_CLK           <= '0';
        elsif rising_edge(clock_in) then
            -- out modMCounter
            complete_tick_out <= complete_tick_tm;
            count_out         <= count_tm;
            -- in switch_leds            
            -- TEST
            -- ###################
            -- switch_in as input:
            ---- switch_tm         <= switch_in;
            -- di_in as input:
            ---- switch_tm         <= di_in;
            -- d_in and switch_in as combined inputs:
            switch_tm(NR_DIS/2-1 downto 0)                <= di_in(NR_DIS/2-1 downto 0);
            -- switch_tm(NR_DIS/2-1 downto 0)                <= di_in(NR_DIS/2-1 downto 0) and invert(switch_in(NR_SWITCHES/2-1 downto 0));
            switch_tm(NR_SWITCHES-1 downto NR_SWITCHES/2) <= switch_in(NR_SWITCHES-1 downto NR_SWITCHES/2);
            -- ###################            
            button_tm         <= button_in;
            -- out switch_leds
            led_out           <= led_tm;
            -- in dio
            di_tm             <= di_in;
            -- out dio
            do_out            <= do_tm;
            -- LT2314
            sampling_pulse_tm <= sampling_pulse;
            SPI_DIN_tm        <= SPI_DIN;
            data_out          <= data_out_tm;
            SPI_nCS           <= SPI_nCS_tm;
            SPI_CLK           <= SPI_CLK_tm;
        end if;
    end process proc_common;
    -- in common
    clock_tm <= clock_in;
    reset_tm <= reset_in;
end Behavioral;



