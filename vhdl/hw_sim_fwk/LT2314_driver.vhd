
-- Code (adapted) from:
-- https://imperix.com/doc/implementation/fpga-based-spi-communication-ip
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity LT2314_driver is
	port(
		-- CLOCKS:
		clk: in std_logic; -- xxx MHz clock
		sampling_pulse: in std_logic; -- sampling strobe
		-- CONFIGURATION:
		-- spi_sck = clk / (postscaler_in*2)
		postscaler_in: in std_logic_vector(15 downto 0);
        -- OUTPUT DATA:
		data_out: out std_logic_vector(15 downto 0) := (others => '0');
		-- SPI SIGNALS:
        spi_sck: out std_logic; -- communication clock
        spi_cs_n: out std_logic; -- chip select strobe / sampling trigger
		spi_din: in std_logic -- serial data in
	);
end LT2314_driver;

architecture impl of LT2314_driver is
	TYPE states is (ACQ,CONV);
	SIGNAL state : states := ACQ; -- FSM state register
	-- Signal used as SPI communication clock
	-- spi_sck = postscaled_clk = clk / (postscaler_in*2)
	SIGNAL postscaled_clk : std_logic := '0';
	-- Indicates a rising edge on postscaled_clk
	SIGNAL postscaled_clk_rising_pulse : std_logic := '0';
	-- Asserted when sampling_pulse = '1'
	-- Cleared when postscaled_clk_rising_pulse = '1'
	SIGNAL pulse_detected : std_logic := '0';
begin
	spi_sck <= postscaled_clk;
	spi_cs_n <= '1' when state=ACQ else '0';
	-- Generate postscaled_clk and postscaled_clk_rising_pulse
	-- #######################################################
	POSTSCALER: process(clk)
		variable postscaler_cnt: unsigned(15 downto 0):=(others=>'0');
    begin
		if rising_edge(clk) then
			postscaled_clk_rising_pulse <= '0';
			-- Toggle postscaled_clk
			-- Assert postscaled_clk_rising_pulse if rising edge
			if postscaler_cnt+1 >= unsigned(postscaler_in) then
				if postscaled_clk = '0' then
					postscaled_clk_rising_pulse <= '1';
				end if;
				postscaler_cnt := (others => '0');
				postscaled_clk <= not postscaled_clk;
			else
				postscaler_cnt := postscaler_cnt + 1;
			end if;
		end if;
	end process POSTSCALER;
	-- Generate pulse_detected
	-- #######################
	SAMPLING: process(clk)
	begin
		if rising_edge(clk) then
			if sampling_pulse = '1' then
				pulse_detected <= '1';
			elsif postscaled_clk_rising_pulse = '1' then
				pulse_detected <= '0';
			end if;
		end if;
	end process SAMPLING;
	-- Finite State Machine
	-- ####################
	-- Run at SPI clock speed (using postscaled_clk_rising_pulse=
	FSM : process(clk)
		variable bit_cnt : unsigned(4 downto 0) := (others=>'0'); -- bit counter
	begin
		if rising_edge(clk) and postscaled_clk_rising_pulse = '1' then
				case state is
					when ACQ =>
						bit_cnt := (others => '0');
						if pulse_detected = '1' then
							state <= CONV;
						end if;
					when CONV =>
						bit_cnt := bit_cnt + 1;
						if bit_cnt >= 16 then
							state <= ACQ;
						end if;
					when others => null;
				end case;
		end if;
	end process FSM;
	-- Sample spi_din on spi_sck rising edge during ACQUISITION phase
	-- ##############################################################
	SHIFT_REG: process (clk)
		variable data_reg: std_logic_vector(15 downto 0):=(others=>'0');
	begin
		if rising_edge(clk) then
			if state = CONV and postscaled_clk_rising_pulse = '1' then
				data_reg := data_reg(14 downto 0) & spi_din;
			elsif state = ACQ then
				data_out <= "0" & data_reg(15 downto 1); -- re-align data
			end if;
		end if;
	end process SHIFT_REG;
end impl;




