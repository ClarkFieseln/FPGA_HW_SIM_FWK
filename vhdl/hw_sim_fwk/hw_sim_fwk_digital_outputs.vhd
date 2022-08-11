
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;


-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_digital_outputs is
    generic(
        NR_DOS             : integer := 2;
        FIFO_PATH          : string  := "\\.\pipe\";
        DOS_FILE_NAME      : string  := FIFO_PATH & "do_";
        PROTOCOL_DOS       : boolean := false
    );
    port(
        reset_in  : in std_logic;
        clock_in  : in std_logic;
        hw_do_in  : in std_logic_vector(NR_DOS - 1 downto 0)
    );
end hw_sim_fwk_digital_outputs;

architecture arch of hw_sim_fwk_digital_outputs is
    -- signals common to both modules
    signal clock_tm, reset_tm : std_logic;
    -- signals dio
    signal hw_do_tm           : std_logic_vector(NR_DOS - 1 downto 0);
begin
    -- instantiate hw digital outputs shown in external simulation
    -- ###########################################################
    -- NOTE: it is not possible to create an array of files or objects with files to be used in only one instance of the logic.
    --       Therefore, DOs(=hw_sim_fwk_digital_output) are instantiated NR_DOS times.
	--       Note that DIs are implemented by generating NR_DIS processes instead.
    GEN_DOS:
    for I in 0 to (NR_DOS - 1) generate
        hw_sim_fwk_digital_output_unit_x : entity work.hw_sim_fwk_digital_output
        generic map(
            NR_DO              => I,
            FIFO_PATH          => FIFO_PATH,
            DO_FILE_NAME       => DOS_FILE_NAME & integer'image(I),
            PROTOCOL_DOS       => PROTOCOL_DOS
        )  
        port map(
            reset => reset_tm,
            clock => clock_tm,
            hw_do => hw_do_tm(I)
        );
    end generate GEN_DOS;
    -- connect cables
    clock_tm <= clock_in;
    reset_tm <= reset_in;
    hw_do_tm <= hw_do_in;
end arch;
-- synthesis translate_on
-- ######################





