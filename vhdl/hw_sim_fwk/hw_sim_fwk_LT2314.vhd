
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;


-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_LT2314 is
    generic(
        NR_DATA_OUT        : integer := 16;
        FILE_PATH          : string  := "/tmp/";
        FIFO_PATH          : string  := "\\.\pipe\";
        -- SCK = CLK_XXX_MHZ / (POSTSCALER*2) = (CLK_XXX_MHZ / 2) MHz
	    SCK_POSTSCALER : std_logic_vector := "0000000000000010"
    );
    port(
        reset_in           : in std_logic;
        clock_in           : in std_logic;
        data_out_in        : in std_logic_vector(NR_DATA_OUT-1 downto 0); 
        sampling_pulse_out : out  std_logic;
	    SPI_DIN_out        : out  std_logic;
	    SPI_nCS_in         : in std_logic;
	    SPI_CLK_in         : in std_logic
    );
end hw_sim_fwk_LT2314;

architecture arch of hw_sim_fwk_LT2314 is
    -- signals common to all modules
    signal clock_tm, reset_tm : std_logic;
    -- signals out
    signal data_out_tm           : std_logic_vector(NR_DATA_OUT - 1 downto 0);
    signal SPI_nCS_tm            : std_logic;
    signal SPI_CLK_tm            : std_logic;
    signal sampling_pulse_tm     : std_logic_vector(0 downto 0);
    signal SPI_DIN_tm            : std_logic_vector(0 downto 0);
begin
    -- instantiate hw data outputs received in external simulation
    -- ###########################################################
    hw_sim_fwk_data_out_x : entity work.hw_sim_fwk_fifo_write_int
    generic map(
        NR_SIGOUT          => 0,
        SIGOUT_PATH        => FIFO_PATH,
        SIGOUT_FILE_NAME   => FIFO_PATH & "LT2314_data_out",
        PROTOCOL_SIGOUT    => false
    )  
    port map(
        reset  => reset_tm,
        clock  => SPI_nCS_tm, -- clock_tm, -- pass nCS instead to get the stable/final int value on it's rising_edge
        sigout => to_integer(unsigned(data_out_tm)) -- data_out_tm is of type std_logic_vector so we convert to integer
    );    
    -- instantiate hw SPI_nCS received in external simulation
    -- ######################################################
    hw_sim_fwk_SPI_nCS : entity work.hw_sim_fwk_fifo_write
    generic map(
        NR_SIGOUT          => 0,
        SIGOUT_PATH        => FIFO_PATH,
        SIGOUT_FILE_NAME   => FIFO_PATH & "LT2314_SPI_nCS",
        SIG_VAL_ON_RESET   => '1', -- IMPORTANT: we need to let moodule "autonomously" initialize to '1'
        PROTOCOL_SIGOUT    => false
    )  
    port map(
        reset  => reset_tm,
        clock  => clock_tm,
        sigout => SPI_nCS_tm
    );
    -- instantiate hw SPI_CLK received in external simulation
    -- ######################################################
    hw_sim_fwk_SPI_CLK : entity work.hw_sim_fwk_fifo_write
    generic map(
        NR_SIGOUT          => 0,
        SIGOUT_PATH        => FIFO_PATH,
        SIGOUT_FILE_NAME   => FIFO_PATH & "LT2314_SPI_SCK",
        PROTOCOL_SIGOUT    => false
    )  
    port map(
        reset  => reset_tm,
        clock  => clock_tm,
        sigout => SPI_CLK_tm
    );
    -- instantiate hw sampling_pulse sent from external simulation
    -- ###########################################################
    hw_sim_fwk_sampling_pulse : entity work.hw_sim_fwk_file_read
    generic map(              
        NR_SIGSIN        => 1,
        SIGSIN_PATH      => FILE_PATH,
        SIGSIN_FILE_NAME => FILE_PATH & "LT2314_sampling_pulse_high",
        PROTOCOL_SIGSIN  => false                
    )
    port map(
        reset     => reset_tm,
        clock     => clock_tm,
        sigsin    => sampling_pulse_tm
    );
    -- instantiate hw SPI_DIN sent from external simulation
    -- ####################################################
    hw_sim_fwk_SPI_DIN : entity work.hw_sim_fwk_file_read
    generic map(              
        NR_SIGSIN        => 1,
        SIGSIN_PATH      => FILE_PATH,
        SIGSIN_FILE_NAME => FILE_PATH & "LT2314_SPI_DIN_high",
        PROTOCOL_SIGSIN  => false                
    )
    port map(
        reset     => reset_tm,
        clock     => clock_tm,
        sigsin    => SPI_DIN_tm
    );    
    -- connect cables
    clock_tm           <= clock_in;
    reset_tm           <= reset_in;
    sampling_pulse_out <= sampling_pulse_tm(0);
    SPI_DIN_out        <= SPI_DIN_tm(0);
    data_out_tm        <= data_out_in;
    SPI_nCS_tm         <= SPI_nCS_in;
    SPI_CLK_tm         <= SPI_CLK_in;
end arch;

-- synthesis translate_on
-- ######################





